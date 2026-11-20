"""Agent base class — common behavior for all roles."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from company.agents.memory import AgentMemory
from company.engine.board import Issue, KanbanBoard
from company.engine.channel import MessageChannel
from company.engine.sandbox import CodeSandbox
from company.engine.artifacts import ArtifactStore
from company.engine.git import GitRepo
from company.llm.client import LLMClient


class Role(str, Enum):
    PM = "pm"
    ARCHITECT = "architect"
    BACKEND = "backend"
    FRONTEND = "frontend"
    QA = "qa"
    DEVOPS = "devops"


@dataclass
class AgentConfig:
    id: str
    name: str
    role: Role
    skills: list[str] = field(default_factory=list)
    system_prompt: str = ""


class BaseAgent:
    """Base class for all company agents."""

    def __init__(
        self,
        config: AgentConfig,
        llm: LLMClient,
        board: KanbanBoard,
        sandbox: CodeSandbox,
        git: GitRepo,
        artifacts: ArtifactStore,
        channel: MessageChannel,
    ) -> None:
        self.config = config
        self.llm = llm
        self.board = board
        self.sandbox = sandbox
        self.git = git
        self.artifacts = artifacts
        self.channel = channel
        self.memory = AgentMemory()
        self.current_task: Optional[Issue] = None

    @property
    def id(self) -> str:
        return self.config.id

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def role(self) -> Role:
        return self.config.role

    def _build_messages(self, user_prompt: str, include_memory: bool = True) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": self.config.system_prompt}]
        if include_memory and self.memory.long_term:
            context = self.memory.get_context()
            if context:
                messages.append({"role": "system", "content": f"Memory:\n{context}"})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def _call_llm(self, prompt: str, fast: bool = False, include_memory: bool = True) -> str:
        messages = self._build_messages(prompt, include_memory)
        if fast:
            return self.llm.chat_fast(messages)
        return self.llm.chat_primary(messages)

    def claim_task(self) -> Optional[Issue]:
        """Claim an available task from the board matching this agent's role."""
        tasks = self.board.get_available_tasks(labels=[self.role.value])
        if not tasks:
            tasks = self.board.get_available_tasks()
        if not tasks:
            return None
        issue = tasks[0]
        self.board.assign_issue(issue.id, self.id)
        self.current_task = issue
        self.memory.remember_working(
            f"Claimed task: {issue.title}", category="task", importance=0.8
        )
        return issue

    def complete_task(self, status: str = "done") -> None:
        """Mark current task as complete."""
        if self.current_task:
            from company.engine.board import IssueStatus
            self.board.move_issue(
                self.current_task.id,
                IssueStatus.DONE if status == "done" else IssueStatus.REVIEW,
            )
            self.memory.remember_long_term(
                f"Completed task: {self.current_task.title}",
                category="experience",
                importance=0.6,
            )
            self.current_task = None

    def check_messages(self) -> list[str]:
        """Check and return unread messages."""
        unread = self.channel.get_inbox(self.id, unread_only=True)
        contents = [m.content for m in unread]
        self.channel.mark_read(self.id)
        return contents

    def send_message(self, receiver: str, content: str, msg_type: str = "direct") -> None:
        from company.engine.channel import MessageType
        type_map = {
            "direct": MessageType.DIRECT,
            "issue_comment": MessageType.ISSUE_COMMENT,
            "pr_review": MessageType.PR_REVIEW,
            "notification": MessageType.NOTIFICATION,
        }
        self.channel.send(self.id, receiver, content, type_map.get(msg_type, MessageType.DIRECT))

    def work(self) -> Optional[Any]:
        """Main work loop — to be overridden by subclasses."""
        task = self.claim_task()
        if task is None:
            return None
        return self.execute_task(task)

    def execute_task(self, task: Issue) -> Any:
        """Execute a specific task — to be overridden by subclasses."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement execute_task")
