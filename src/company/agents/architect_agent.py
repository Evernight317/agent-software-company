"""Architect Agent — designs technical architecture from PRD."""

from __future__ import annotations

from typing import Any, Optional

from company.agents.base import BaseAgent, AgentConfig, Role
from company.agents.parser import parse_design_tasks
from company.engine import (
    ArtifactStore,
    ArtifactType,
    CodeSandbox,
    GitRepo,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
    KanbanBoard,
    MessageChannel,
)
from company.llm import prompts
from company.llm.client import LLMClient


class ArchitectAgent(BaseAgent):
    """Software Architect — turns PRD into technical design + dev tasks."""

    def __init__(self, **kwargs: Any) -> None:
        config = AgentConfig(
            id="architect",
            name="Architect Agent",
            role=Role.ARCHITECT,
            skills=["architecture", "api-design", "task-breakdown"],
            system_prompt=prompts.ARCHITECT_SYSTEM,
        )
        super().__init__(config=config, **kwargs)

    def design(self, prd: str = "") -> str:
        """Generate a technical design document from a PRD.

        If prd is empty, fetches the latest PRD from the artifact store.
        """
        if not prd.strip():
            prd_artifact = self.artifacts.get_latest(ArtifactType.PRD)
            prd = prd_artifact.content if prd_artifact else "(no PRD available)"

        self.memory.remember_working(
            "Designing architecture from PRD",
            category="task",
            importance=0.9,
        )

        prompt = prompts.ARCHITECT_DESIGN.format(prd=prd)
        design = self._call_llm(prompt, include_memory=False)

        self.artifacts.save(
            type=ArtifactType.DESIGN,
            title="Technical Design Document",
            content=design,
            author=self.id,
            file_path="docs/design.md",
        )
        self.memory.remember_long_term(
            "Technical design generated",
            category="design",
            importance=0.8,
        )
        return design

    def create_tasks_from_design(self, design: str) -> list[Issue]:
        """Parse design doc and create development task issues."""
        parsed = parse_design_tasks(design)

        created: list[Issue] = []
        for item in parsed:
            issue = self.board.create_issue(
                title=item.title,
                description=item.description,
                type=IssueType.TASK,
                priority=IssuePriority.HIGH,
                labels=item.labels,
            )
            self.board.move_issue(issue.id, IssueStatus.TODO)
            created.append(issue)

        self.memory.remember_working(
            f"Created {len(created)} dev tasks from design",
            category="task",
            importance=0.8,
        )
        return created

    def execute_task(self, task: Issue) -> str:
        """Execute architect task — read PRD from artifacts, produce design."""
        self.current_task = task
        self.board.assign_issue(task.id, self.id)

        # Fetch latest PRD
        prd_artifact = self.artifacts.get_latest(ArtifactType.PRD)
        prd_content = prd_artifact.content if prd_artifact else task.description

        design = self.design(prd_content)
        tasks = self.create_tasks_from_design(design)

        self.channel.broadcast(
            sender=self.id,
            content=f"Design complete. {len(tasks)} dev tasks created.",
        )

        self.complete_task()
        return design
