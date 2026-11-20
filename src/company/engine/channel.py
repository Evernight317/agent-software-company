"""Message channel — structured communication between agents."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MessageType(str, Enum):
    ISSUE_COMMENT = "issue_comment"
    PR_REVIEW = "pr_review"
    MEETING = "meeting"
    DIRECT = "direct"
    NOTIFICATION = "notification"


@dataclass
class Message:
    id: str
    type: MessageType
    sender: str  # Agent ID or "system" or "user"
    receiver: str  # Agent ID or "all" or "team"
    content: str
    metadata: dict = field(default_factory=dict)  # issue_id, pr_id, meeting_topic, etc.
    created_at: float = field(default_factory=time.time)
    read: bool = False


class MessageChannel:
    """Structured communication channel for agent collaboration."""

    def __init__(self) -> None:
        self._messages: list[Message] = []
        self._inboxes: dict[str, list[Message]] = {}

    def send(
        self,
        sender: str,
        receiver: str,
        content: str,
        type: MessageType = MessageType.DIRECT,
        metadata: dict | None = None,
    ) -> Message:
        msg = Message(
            id=str(uuid.uuid4())[:8],
            type=type,
            sender=sender,
            receiver=receiver,
            content=content,
            metadata=metadata or {},
        )
        self._messages.append(msg)
        self._inboxes.setdefault(receiver, []).append(msg)
        if receiver == "all":
            for agent_id in list(self._inboxes.keys()):
                if agent_id != sender and agent_id != "all":
                    self._inboxes[agent_id].append(msg)
        return msg

    def get_inbox(self, agent_id: str, unread_only: bool = False) -> list[Message]:
        messages = self._inboxes.get(agent_id, [])
        if unread_only:
            return [m for m in messages if not m.read]
        return list(messages)

    def mark_read(self, agent_id: str, message_id: str | None = None) -> None:
        messages = self._inboxes.get(agent_id, [])
        for msg in messages:
            if message_id is None or msg.id == message_id:
                msg.read = True

    def broadcast(
        self,
        sender: str,
        content: str,
        type: MessageType = MessageType.NOTIFICATION,
        metadata: dict | None = None,
    ) -> Message:
        return self.send(sender, "all", content, type, metadata)

    def get_history(
        self,
        agent_id: str | None = None,
        type: MessageType | None = None,
        limit: int = 50,
    ) -> list[Message]:
        messages = self._messages
        if agent_id:
            messages = [m for m in messages if m.sender == agent_id or m.receiver == agent_id]
        if type:
            messages = [m for m in messages if m.type == type]
        return messages[-limit:]

    def clear_inbox(self, agent_id: str) -> None:
        self._inboxes[agent_id] = []
