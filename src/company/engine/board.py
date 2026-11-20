"""Project board — Issue tracking and Kanban system."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class IssueType(str, Enum):
    REQUIREMENT = "requirement"
    TASK = "task"
    BUG = "bug"
    IMPROVEMENT = "improvement"


class IssueStatus(str, Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"


class IssuePriority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3
    CRITICAL = 4


@dataclass
class Comment:
    id: str
    author: str  # Agent ID or "user"
    content: str
    created_at: float = field(default_factory=time.time)


@dataclass
class Issue:
    id: str
    title: str
    description: str
    type: IssueType
    status: IssueStatus = IssueStatus.BACKLOG
    priority: IssuePriority = IssuePriority.NORMAL
    assignee: Optional[str] = None  # Agent ID
    labels: list[str] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def add_comment(self, author: str, content: str) -> Comment:
        comment = Comment(id=str(uuid.uuid4())[:8], author=author, content=content)
        self.comments.append(comment)
        self.updated_at = time.time()
        return comment

    def assign(self, agent_id: str) -> None:
        self.assignee = agent_id
        self.status = IssueStatus.IN_PROGRESS
        self.updated_at = time.time()

    def move_to(self, status: IssueStatus) -> None:
        self.status = status
        self.updated_at = time.time()


class KanbanBoard:
    """Issue tracking board for the whole team."""

    def __init__(self) -> None:
        self.issues: list[Issue] = []

    def create_issue(
        self,
        title: str,
        description: str,
        type: IssueType = IssueType.TASK,
        priority: IssuePriority = IssuePriority.NORMAL,
        labels: list[str] | None = None,
    ) -> Issue:
        issue = Issue(
            id=str(uuid.uuid4())[:8],
            title=title,
            description=description,
            type=type,
            priority=priority,
            labels=labels or [],
        )
        self.issues.append(issue)
        return issue

    def get_issue(self, issue_id: str) -> Optional[Issue]:
        for issue in self.issues:
            if issue.id == issue_id:
                return issue
        return None

    def get_issues_by_status(self, status: IssueStatus) -> list[Issue]:
        return [i for i in self.issues if i.status == status]

    def get_issues_by_label(self, label: str) -> list[Issue]:
        return [i for i in self.issues if label in i.labels]

    def get_available_tasks(self, labels: list[str] | None = None) -> list[Issue]:
        """Get todo tasks, optionally filtered by labels (role-matching)."""
        tasks = self.get_issues_by_status(IssueStatus.TODO)
        if labels:
            tasks = [t for t in tasks if any(l in t.labels for l in labels)]
        tasks.sort(key=lambda i: i.priority, reverse=True)
        return tasks

    def has_todo_tasks(self) -> bool:
        return len(self.get_issues_by_status(IssueStatus.TODO)) > 0

    def assign_issue(self, issue_id: str, agent_id: str) -> Optional[Issue]:
        issue = self.get_issue(issue_id)
        if issue and issue.status == IssueStatus.TODO:
            issue.assign(agent_id)
        return issue

    def add_comment(self, issue_id: str, author: str, content: str) -> Optional[Comment]:
        issue = self.get_issue(issue_id)
        if issue:
            return issue.add_comment(author, content)
        return None

    def move_issue(self, issue_id: str, status: IssueStatus) -> Optional[Issue]:
        issue = self.get_issue(issue_id)
        if issue:
            issue.move_to(status)
        return issue

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for status in IssueStatus:
            counts[status.value] = len(self.get_issues_by_status(status))
        return counts
