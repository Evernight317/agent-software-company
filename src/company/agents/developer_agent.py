"""Developer Agent — implements code, runs tests, creates PRs."""

from __future__ import annotations

from typing import Any, Optional

from company.agents.base import BaseAgent, AgentConfig, Role
from company.agents.parser import parse_code_files, ParsedFile
from company.engine import (
    ArtifactType,
    CodeSandbox,
    GitRepo,
    Issue,
    IssueStatus,
    KanbanBoard,
    MessageChannel,
    ArtifactStore,
)
from company.engine.git import PR, PRStatus
from company.engine.sandbox import TestResult
from company.llm import prompts
from company.llm.client import LLMClient


class DeveloperAgent(BaseAgent):
    """Developer — claims tasks, writes code, runs tests, submits PRs.

    Supports both backend and frontend roles.
    """

    def __init__(self, role: Role = Role.BACKEND, **kwargs: Any) -> None:
        system = prompts.BACKEND_SYSTEM if role == Role.BACKEND else prompts.FRONTEND_SYSTEM
        role_id = role.value
        config = AgentConfig(
            id=role_id,
            name=f"{role.value.title()} Developer",
            role=role,
            skills=["coding", "testing", "git"],
            system_prompt=system,
        )
        super().__init__(config=config, **kwargs)
        self._max_fix_iterations = 3

    def implement_task(self, task: Issue, design: str) -> list[ParsedFile]:
        """Call LLM to generate code for a task, return parsed files."""
        self.memory.remember_working(
            f"Implementing: {task.title}",
            category="task",
            importance=0.9,
        )

        existing = self._get_existing_code_context()
        prompt = prompts.DEV_IMPLEMENT.format(
            task_title=task.title,
            task_description=task.description,
            design=design[:4000],
            existing_code=existing,
        )
        output = self._call_llm(prompt, include_memory=False)
        files = parse_code_files(output)

        self.memory.remember_working(
            f"Generated {len(files)} files for {task.title}",
            category="task",
            importance=0.7,
        )
        return files

    def write_files(self, files: list[ParsedFile]) -> None:
        """Write parsed files to the sandbox."""
        for f in files:
            self.sandbox.write_file(f.path, f.content)
            self.memory.remember_working(
                f"Wrote {f.path} ({len(f.content)} chars)",
                category="task",
                importance=0.5,
            )

    def run_tests(self) -> TestResult:
        """Run tests in the sandbox and return results."""
        result = self.sandbox.run_tests()
        self.memory.remember_working(
            f"Tests: {result.passed}/{result.total} passed",
            category="task",
            importance=0.8,
        )
        if not result.success and result.errors:
            for err in result.errors[:3]:
                self.memory.remember_working(
                    f"Test error: {err[:200]}",
                    category="bug",
                    importance=0.7,
                )
        return result

    def fix_issues(self, errors: list[str], design: str) -> list[ParsedFile]:
        """Ask LLM to fix code based on test errors."""
        current_code = self._get_existing_code_context()
        prompt = prompts.FIX_BUG.format(
            bug_description="; ".join(errors[:5]),
            error_output="\\n".join(errors[:10]),
            current_code=current_code[:3000],
        )
        output = self._call_llm(prompt, include_memory=False)
        files = parse_code_files(output)

        self.memory.remember_working(
            f"Fix generated for {len(files)} files",
            category="bug",
            importance=0.8,
        )
        return files

    def create_pr(self, task: Issue, files: list[ParsedFile]) -> PR:
        """Create a branch, commit files, and open a PR."""
        branch_name = f"feature/{task.id}"
        self.git.create_branch(branch_name)

        file_dict = {f.path: f.content for f in files}
        self.git.commit(self.id, file_dict, f"Implement: {task.title}")

        pr = self.git.create_pr(
            branch=branch_name,
            title=f"[{task.id}] {task.title}",
            description=task.description,
            author=self.id,
        )

        self.memory.remember_long_term(
            f"PR created: {pr.id} for {task.title}",
            category="experience",
            importance=0.7,
        )
        return pr

    def execute_task(self, task: Issue, design: str = "") -> Optional[PR]:
        """Full development cycle: implement → test → fix → PR.

        Returns the created PR, or None if tests couldn't pass.
        """
        self.current_task = task
        self.board.assign_issue(task.id, self.id)

        # Snapshot before changes
        self.sandbox.snapshot(name=f"before_{task.id}")

        # Generate and write code
        files = self.implement_task(task, design)
        if not files:
            self.memory.remember_working(
                "No files generated — skipping",
                category="bug",
                importance=0.9,
            )
            self.board.move_issue(task.id, IssueStatus.BLOCKED)
            return None
        self.write_files(files)

        # Iterate: test → fix
        for iteration in range(self._max_fix_iterations):
            test_result = self.run_tests()
            if test_result.success:
                break

            self.memory.remember_working(
                f"Fix iteration {iteration + 1}: {test_result.failed} failures",
                category="bug",
                importance=0.8,
            )
            fixed = self.fix_issues(test_result.errors, design)
            if fixed:
                self.write_files(fixed)
            else:
                break

        # Final test
        final_result = self.run_tests()

        # Create PR regardless (reviewer can catch remaining issues)
        pr = self.create_pr(task, files)
        self.artifacts.save(
            type=ArtifactType.CODE,
            title=f"Implementation: {task.title}",
            content="\\n".join(f"### FILE: {f.path}\\n```{f.language}\\n{f.content}```" for f in files),
            author=self.id,
            file_path=f"pr/{pr.id}/",
        )

        if final_result.success:
            self.board.move_issue(task.id, IssueStatus.REVIEW)
            self.channel.send(
                sender=self.id,
                receiver="architect",
                content=f"PR {pr.id} ready for review: {task.title}. Tests: {final_result.passed}/{final_result.total} passed.",
            )
        else:
            self.board.move_issue(task.id, IssueStatus.REVIEW)
            self.channel.send(
                sender=self.id,
                receiver="architect",
                content=f"PR {pr.id} submitted with {final_result.failed} test failures: {task.title}. Needs attention.",
            )

        self.complete_task(status="review")
        return pr

    def _get_existing_code_context(self) -> str:
        """Get a summary of existing code files for LLM context."""
        files = self.sandbox.list_files()
        if not files:
            return "(none — fresh project)"
        lines = [f"{f} ({len(self.sandbox.read_file(f))} chars)" for f in files[:20]]
        return "\\n".join(lines)
