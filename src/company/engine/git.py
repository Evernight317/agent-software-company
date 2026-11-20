"""Simulated Git — commit, branch, PR, review, merge."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PRStatus(str, Enum):
    OPEN = "open"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    MERGED = "merged"
    CLOSED = "closed"


@dataclass
class Commit:
    id: str
    author: str  # Agent ID
    message: str
    files: dict[str, str] = field(default_factory=dict)  # path -> content
    branch: str = "main"
    timestamp: float = field(default_factory=time.time)


@dataclass
class ReviewComment:
    id: str
    reviewer: str  # Agent ID
    file: str
    line: int
    comment: str
    severity: str = "suggestion"  # suggestion / warning / blocking


@dataclass
class PR:
    id: str
    title: str
    description: str
    branch: str
    author: str  # Agent ID
    commits: list[Commit] = field(default_factory=list)
    review_comments: list[ReviewComment] = field(default_factory=list)
    status: PRStatus = PRStatus.OPEN
    reviewer: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    merged_at: Optional[float] = None


class GitRepo:
    """Simulated Git repository with PR workflow."""

    def __init__(self) -> None:
        self.main_branch: list[Commit] = []
        self.branches: dict[str, list[Commit]] = {"main": self.main_branch}
        self.prs: list[PR] = []
        self._current_branch = "main"

    def checkout(self, branch: str) -> None:
        if branch not in self.branches:
            self.branches[branch] = []
        self._current_branch = branch

    def create_branch(self, name: str) -> str:
        if name not in self.branches:
            self.branches[name] = list(self.branches.get(self._current_branch, []))
        self._current_branch = name
        return name

    def commit(self, author: str, files: dict[str, str], message: str) -> Commit:
        commit = Commit(
            id=str(uuid.uuid4())[:8],
            author=author,
            message=message,
            files=files.copy(),
            branch=self._current_branch,
        )
        self.branches.setdefault(self._current_branch, []).append(commit)
        return commit

    def create_pr(
        self,
        branch: str,
        title: str,
        description: str,
        author: str,
    ) -> PR:
        pr = PR(
            id=str(uuid.uuid4())[:8],
            title=title,
            description=description,
            branch=branch,
            author=author,
            commits=list(self.branches.get(branch, [])),
        )
        self.prs.append(pr)
        return pr

    def get_pr(self, pr_id: str) -> Optional[PR]:
        return next((p for p in self.prs if p.id == pr_id), None)

    def add_review_comment(
        self,
        pr_id: str,
        reviewer: str,
        file: str,
        line: int,
        comment: str,
        severity: str = "suggestion",
    ) -> Optional[ReviewComment]:
        pr = self.get_pr(pr_id)
        if pr is None:
            return None
        rc = ReviewComment(
            id=str(uuid.uuid4())[:8],
            reviewer=reviewer,
            file=file,
            line=line,
            comment=comment,
            severity=severity,
        )
        pr.review_comments.append(rc)
        pr.reviewer = reviewer
        pr.status = PRStatus.CHANGES_REQUESTED
        return rc

    def approve_pr(self, pr_id: str, reviewer: str) -> Optional[PR]:
        pr = self.get_pr(pr_id)
        if pr is None:
            return None
        pr.reviewer = reviewer
        pr.status = PRStatus.APPROVED
        return pr

    def merge_pr(self, pr_id: str) -> Optional[PR]:
        pr = self.get_pr(pr_id)
        if pr is None or pr.status not in (PRStatus.APPROVED, PRStatus.OPEN):
            return None
        pr.status = PRStatus.MERGED
        pr.merged_at = time.time()
        for commit in pr.commits:
            if commit not in self.main_branch:
                self.main_branch.append(commit)
        return pr

    def get_diff(self, pr_id: str) -> str:
        pr = self.get_pr(pr_id)
        if pr is None:
            return ""
        diff_lines = []
        for commit in pr.commits:
            diff_lines.append(f"--- commit {commit.id} by {commit.author}: {commit.message}")
            for filepath, content in commit.files.items():
                diff_lines.append(f"+++ {filepath}")
                diff_lines.append(content)
        return "\n".join(diff_lines)

    def log(self) -> list[Commit]:
        return list(self.main_branch)

    def get_files(self) -> dict[str, str]:
        """Return current main branch file state."""
        files: dict[str, str] = {}
        for commit in self.main_branch:
            files.update(commit.files)
        return files
