"""PM Agent — analyzes requirements and creates PRD + Issues."""

from __future__ import annotations

from typing import Any, Optional

from company.agents.base import BaseAgent, AgentConfig, Role
from company.agents.parser import parse_prd_issues
from company.engine import (
    ArtifactType,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
)
from company.llm import prompts


class PMAgent(BaseAgent):
    """Product Manager — transforms user requirements into PRD and board issues."""

    def __init__(self, **kwargs: Any) -> None:
        config = AgentConfig(
            id="pm",
            name="PM Agent",
            role=Role.PM,
            skills=["requirements", "user-stories", "prioritization"],
            system_prompt=prompts.PM_SYSTEM,
        )
        super().__init__(config=config, **kwargs)

    def analyze_requirement(self, requirement: str) -> str:
        """Generate a PRD from a raw user requirement."""
        self.memory.remember_working(
            f"Analyzing requirement: {requirement[:200]}",
            category="task",
            importance=0.9,
        )

        prompt = prompts.PM_ANALYZE.format(requirement=requirement)
        prd = self._call_llm(prompt, include_memory=False)

        # Save PRD artifact
        self.artifacts.save(
            type=ArtifactType.PRD,
            title="Product Requirements Document",
            content=prd,
            author=self.id,
            file_path="docs/prd.md",
        )
        self.memory.remember_long_term(
            "PRD generated and saved",
            category="decision",
            importance=0.8,
        )
        return prd

    def create_issues_from_prd(self, prd: str) -> list[Issue]:
        """Parse PRD and create board issues for each parsed item."""
        parsed = parse_prd_issues(prd)
        priority_map = {
            0: IssuePriority.URGENT,
            1: IssuePriority.HIGH,
            2: IssuePriority.NORMAL,
        }

        created: list[Issue] = []
        for item in parsed:
            issue = self.board.create_issue(
                title=item.title,
                description=item.description,
                type=IssueType.TASK,
                priority=priority_map.get(item.priority, IssuePriority.NORMAL),
                labels=item.labels or ["general"],
            )
            self.board.move_issue(issue.id, IssueStatus.TODO)
            created.append(issue)

        self.memory.remember_working(
            f"Created {len(created)} issues from PRD",
            category="task",
            importance=0.8,
        )
        return created

    def execute_task(self, task: Issue) -> str:
        """Execute PM-specific task (analyze a requirement issue)."""
        self.current_task = task
        self.board.assign_issue(task.id, self.id)

        prd = self.analyze_requirement(task.description)
        issues = self.create_issues_from_prd(prd)

        # Notify the team
        self.channel.broadcast(
            sender=self.id,
            content=f"PRD created. {len(issues)} issues added to the board.",
        )

        self.complete_task()
        return prd
