"""Reviewer Agent — reviews PRs and requests changes or approves."""

from __future__ import annotations

from typing import Any, Optional

from company.agents.base import BaseAgent, AgentConfig, Role
from company.agents.parser import parse_review, ParsedReview
from company.engine import GitRepo, Issue, IssueStatus, KanbanBoard
from company.engine.git import PR, PRStatus
from company.llm import prompts
from company.llm.client import LLMClient


class ReviewerAgent(BaseAgent):
    """Code reviewer — reviews PRs, leaves comments, approves or requests changes."""

    def __init__(self, **kwargs: Any) -> None:
        config = AgentConfig(
            id="reviewer",
            name="Code Reviewer",
            role=Role.ARCHITECT,  # reviewer role is architect in Phase 3
            skills=["code-review", "best-practices"],
            system_prompt=prompts.ARCHITECT_SYSTEM,
        )
        super().__init__(config=config, **kwargs)
        self._max_review_iterations = 2

    def review_pr(self, pr: PR) -> ParsedReview:
        """Review a PR using the LLM and return parsed feedback."""
        diff = self.git.get_diff(pr.id)

        prompt = prompts.REVIEW_PR.format(
            pr_title=pr.title,
            pr_description=pr.description,
            diff=diff[:4000],
        )
        output = self._call_llm(prompt, include_memory=False)
        review = parse_review(output)

        # Apply review comments to the PR
        for fb in review.comments:
            self.git.add_review_comment(
                pr_id=pr.id,
                reviewer=self.id,
                file=fb.file,
                line=fb.line,
                comment=fb.comment,
                severity=fb.severity,
            )

        if review.approved:
            self.git.approve_pr(pr.id, self.id)
            self.memory.remember_long_term(
                f"Approved PR {pr.id}: {pr.title}",
                category="review",
                importance=0.6,
            )
        else:
            self.memory.remember_working(
                f"Requested changes on PR {pr.id}: {len(review.comments)} comments",
                category="review",
                importance=0.8,
            )

        return review

    def execute_task(self, task: Issue) -> Any:
        """Review all open PRs."""
        self.current_task = task
        self.board.assign_issue(task.id, self.id)

        open_prs = [p for p in self.git.prs if p.status == PRStatus.OPEN]
        results = []
        for pr in open_prs:
            review = self.review_pr(pr)
            results.append((pr, review))

        self.complete_task()
        return results
