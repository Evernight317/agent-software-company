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
from company.agents import PMAgent, ArchitectAgent
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

        self._sandbox_dir = f"output/projects/{project_name}"

    def _build_agent_kwargs(self) -> dict:
        """Common kwargs for agent construction."""
        return {
            "llm": self.llm,
            "board": self.ctx.board,
            "sandbox": self.ctx.sandbox or CodeSandbox(),
            "git": self.ctx.git,
            "artifacts": self.ctx.artifacts,
            "channel": self.ctx.channel,
        }

    def run(self, requirement: str) -> dict:
        """Run the full development pipeline."""
        self.logger.phase(f"Starting Project: {self.project_name}")
        self.logger.log("user", "requirement", requirement)

        self.ctx.sandbox = CodeSandbox(project_dir=self._sandbox_dir)

        results = {}

        # Phase 1: PM — requirements analysis
        results["prd"] = self._run_pm(requirement)

        # Phase 2: Architect — technical design
        results["design"] = self._run_architect(results["prd"])

        # Phase 3: Development (Phase 3+ stubs — implemented in Phase 3)
        results["development"] = self._run_development(results["design"])

        # Phase 4: QA (stub)
        results["qa"] = self._run_qa(results["design"])

        # Phase 5: DevOps (stub)
        results["devops"] = self._run_devops()

        # Phase 6: Finalize
        results["summary"] = self._finalize()

        self.logger.phase("Project Complete")
        return results

    def run_phases_1_2(self, requirement: str) -> dict:
        """Run only PM + Architect phases (Phase 2 milestone)."""
        self.logger.phase(f"Starting Project: {self.project_name}")
        self.logger.log("user", "requirement", requirement)

        self.ctx.sandbox = CodeSandbox(project_dir=self._sandbox_dir)

        results = {}
        results["prd"] = self._run_pm(requirement)
        results["design"] = self._run_architect(results["prd"])
        results["summary"] = self._finalize()

        self.logger.phase("Phase 1-2 Complete")
        return results

    def _run_pm(self, requirement: str) -> str:
        self.logger.phase("Phase 1: Requirements Analysis (PM)")

        agent = PMAgent(**self._build_agent_kwargs())

        # Generate PRD
        prd = agent.analyze_requirement(requirement)
        self.logger.log("PM", "PRD created", "Product requirements document generated", "success")

        # Create issues from PRD
        issues = agent.create_issues_from_prd(prd)
        for issue in issues:
            self.logger.log("PM", "issue created", f"#{issue.id} {issue.title}")
        self.logger.print_board(self.ctx.board)

        return prd

    def _run_architect(self, prd: str) -> str:
        self.logger.phase("Phase 2: Technical Design (Architect)")

        agent = ArchitectAgent(**self._build_agent_kwargs())

        design = agent.design(prd)
        self.logger.log("Architect", "design created", "Technical design document generated", "success")

        tasks = agent.create_tasks_from_design(design)
        for task in tasks:
            self.logger.log("Architect", "task created", f"#{task.id} {task.title} [{','.join(task.labels)}]")
        self.logger.print_board(self.ctx.board)

        return design

    def _run_development(self, design: str) -> str:
        self.logger.phase("Phase 3: Development (pending Phase 3)")

        tasks = self.ctx.board.get_issues_by_status(IssueStatus.TODO)
        dev_tasks = [t for t in tasks if any(l in t.labels for l in ("backend", "frontend", "shared"))]

        if not dev_tasks:
            self.logger.log("system", "no dev tasks", "No development tasks found", "warning")
            return ""

        self.logger.log(
            "system", "dev tasks queued",
            f"{len(dev_tasks)} tasks waiting for implementation (Phase 3)",
        )
        return f"{len(dev_tasks)} tasks queued"

    def _run_qa(self, design: str) -> str:
        self.logger.phase("Phase 4: Testing (pending Phase 4)")
        self.logger.log("QA", "pending", "QA agent will be implemented in Phase 4", "warning")
        return "pending"

    def _run_devops(self) -> str:
        self.logger.phase("Phase 5: Deployment (pending Phase 4)")
        self.logger.log("DevOps", "pending", "DevOps agent will be implemented in Phase 4", "warning")
        return "pending"

    def _finalize(self) -> dict:
        self.logger.phase("Phase 6: Finalization")
        self.logger.print_board(self.ctx.board)

        summary = {
            "issues_total": len(self.ctx.board.issues),
            "issues_done": len(self.ctx.board.get_issues_by_status(IssueStatus.DONE)),
            "issues_review": len(self.ctx.board.get_issues_by_status(IssueStatus.REVIEW)),
            "issues_todo": len(self.ctx.board.get_issues_by_status(IssueStatus.TODO)),
            "artifacts": self.ctx.artifacts.summary(),
            "commits": len(self.ctx.git.log()),
            "messages": len(self.ctx.channel._messages),
        }
        self.logger.log("system", "summary", str(summary), "success")
        return summary
