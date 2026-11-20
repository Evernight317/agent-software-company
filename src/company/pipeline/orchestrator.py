"""Orchestrator — drives the multi-agent development pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from company.engine import (
    KanbanBoard,
    CodeSandbox,
    GitRepo,
    ArtifactStore,
    MessageChannel,
    Issue,
    IssueType,
    IssueStatus,
    IssuePriority,
    ArtifactType,
)
from company.llm import LLMClient, prompts
from company.output import DevLogger


@dataclass
class CompanyContext:
    """Shared context for all agents."""
    board: KanbanBoard = field(default_factory=KanbanBoard)
    sandbox: Optional[CodeSandbox] = None
    git: GitRepo = field(default_factory=GitRepo)
    artifacts: ArtifactStore = field(default_factory=ArtifactStore)
    channel: MessageChannel = field(default_factory=MessageChannel)
    logger: Optional[DevLogger] = None


class Orchestrator:
    """Coordinates the multi-agent development pipeline."""

    def __init__(
        self,
        llm: LLMClient,
        project_name: str = "project",
        logger: Optional[DevLogger] = None,
    ) -> None:
        self.llm = llm
        self.project_name = project_name
        self.logger = logger or DevLogger()
        self.ctx = CompanyContext(logger=self.logger)

        # Sandbox will be initialized when pipeline starts
        self._sandbox_dir = f"output/projects/{project_name}"

    def run(self, requirement: str) -> dict:
        """Run the full development pipeline."""
        self.logger.phase(f"Starting Project: {self.project_name}")
        self.logger.log("user", "requirement", requirement)

        # Initialize sandbox
        self.ctx.sandbox = CodeSandbox(project_dir=self._sandbox_dir)

        results = {}

        # Phase 1: PM — requirements analysis
        results["prd"] = self._run_pm(requirement)

        # Phase 2: Architect — technical design
        results["design"] = self._run_architect(results["prd"])

        # Phase 3: Development — backend + frontend
        results["backend"] = self._run_development("backend", results["design"])
        results["frontend"] = self._run_development("frontend", results["design"])

        # Phase 4: QA — integration testing
        results["qa"] = self._run_qa(results["design"])

        # Phase 5: DevOps — deployment
        results["devops"] = self._run_devops()

        # Phase 6: Finalize
        results["summary"] = self._finalize()

        self.logger.phase("Project Complete")
        return results

    def _run_pm(self, requirement: str) -> str:
        self.logger.phase("Phase 1: Requirements Analysis (PM)")

        messages = [{"role": "system", "content": prompts.PM_SYSTEM}]
        messages.append({"role": "user", "content": prompts.PM_ANALYZE.format(requirement=requirement)})

        prd = self.llm.chat_primary(messages)
        self.ctx.artifacts.save(
            type=ArtifactType.PRD,
            title="Product Requirements Document",
            content=prd,
            author="pm",
            file_path="docs/prd.md",
        )
        self.logger.log("PM", "PRD created", "Product requirements document generated", "success")

        # Create issues from PRD (simplified — in production would parse PRD)
        issue = self.ctx.board.create_issue(
            title="Backend API implementation",
            description="Implement backend API based on PRD",
            type=IssueType.TASK,
            priority=IssuePriority.HIGH,
            labels=["backend"],
        )
        self.ctx.board.move_issue(issue.id, IssueStatus.TODO)

        issue = self.ctx.board.create_issue(
            title="Frontend UI implementation",
            description="Implement frontend UI based on PRD",
            type=IssueType.TASK,
            priority=IssuePriority.HIGH,
            labels=["frontend"],
        )
        self.ctx.board.move_issue(issue.id, IssueStatus.TODO)

        self.logger.print_board(self.ctx.board)
        return prd

    def _run_architect(self, prd: str) -> str:
        self.logger.phase("Phase 2: Technical Design (Architect)")

        messages = [{"role": "system", "content": prompts.ARCHITECT_SYSTEM}]
        messages.append({"role": "user", "content": prompts.ARCHITECT_DESIGN.format(prd=prd)})

        design = self.llm.chat_primary(messages)
        self.ctx.artifacts.save(
            type=ArtifactType.DESIGN,
            title="Technical Design Document",
            content=design,
            author="architect",
            file_path="docs/design.md",
        )
        self.logger.log("Architect", "Design created", "Technical design document generated", "success")
        return design

    def _run_development(self, role: str, design: str) -> str:
        self.logger.phase(f"Phase 3: Development ({role.title()})")

        system = prompts.BACKEND_SYSTEM if role == "backend" else prompts.FRONTEND_SYSTEM
        tasks = self.ctx.board.get_issues_by_status(IssueStatus.TODO)
        role_tasks = [t for t in tasks if role in t.labels]

        if not role_tasks:
            self.logger.log(role.title(), "no tasks", f"No {role} tasks found", "warning")
            return ""

        task = role_tasks[0]
        self.ctx.board.assign_issue(task.id, role)
        self.logger.log(role.title(), "task claimed", f"#{task.id} {task.title}")

        messages = [{"role": "system", "content": system}]
        prompt = prompts.DEV_IMPLEMENT.format(
            task_title=task.title,
            task_description=task.description,
            design=design[:3000],  # truncate to fit context
            existing_code="(none — fresh project)",
        )
        messages.append({"role": "user", "content": prompt})

        code_output = self.llm.chat_primary(messages, temperature=0.3)

        # Save code to artifacts
        self.ctx.artifacts.save(
            type=ArtifactType.CODE,
            title=f"{role} implementation",
            content=code_output,
            author=role,
            file_path=f"src/{role}/",
        )

        self.ctx.board.move_issue(task.id, IssueStatus.REVIEW)
        self.logger.log(role.title(), "code submitted", f"PR created for {task.title}", "success")

        return code_output

    def _run_qa(self, design: str) -> str:
        self.logger.phase("Phase 4: Testing (QA)")

        file_list = "\n".join(self.ctx.sandbox.list_files()) if self.ctx.sandbox else "(no files)"

        messages = [{"role": "system", "content": prompts.QA_SYSTEM}]
        prompt = prompts.QA_TEST.format(
            design=design[:2000],
            file_list=file_list,
        )
        messages.append({"role": "user", "content": prompt})

        test_output = self.llm.chat_primary(messages)
        self.ctx.artifacts.save(
            type=ArtifactType.TEST_REPORT,
            title="Test Plan and Results",
            content=test_output,
            author="qa",
        )
        self.logger.log("QA", "tests written", "Integration test plan generated", "success")
        return test_output

    def _run_devops(self) -> str:
        self.logger.phase("Phase 5: Deployment (DevOps)")

        file_structure = "\n".join(self.ctx.sandbox.list_files()) if self.ctx.sandbox else "(project structure)"

        messages = [{"role": "system", "content": prompts.DEVOPS_SYSTEM}]
        prompt = prompts.DEVOPS_DEPLOY.format(file_structure=file_structure)
        messages.append({"role": "user", "content": prompt})

        deploy_output = self.llm.chat_primary(messages)
        self.ctx.artifacts.save(
            type=ArtifactType.DEPLOY_CONFIG,
            title="Deployment Configuration",
            content=deploy_output,
            author="devops",
        )
        self.logger.log("DevOps", "deploy config created", "Docker configuration generated", "success")
        return deploy_output

    def _finalize(self) -> dict:
        self.logger.phase("Phase 6: Finalization")
        self.logger.print_board(self.ctx.board)

        summary = {
            "issues_total": len(self.ctx.board.issues),
            "issues_done": len(self.ctx.board.get_issues_by_status(IssueStatus.DONE)),
            "issues_review": len(self.ctx.board.get_issues_by_status(IssueStatus.REVIEW)),
            "artifacts": self.ctx.artifacts.summary(),
            "commits": len(self.ctx.git.log()),
        }
        self.logger.log("system", "summary", str(summary), "success")
        return summary
