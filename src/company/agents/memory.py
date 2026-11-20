"""Agent memory — working memory and long-term memory."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MemoryItem:
    id: str
    content: str
    category: str = "general"  # decision, bug, review, design, experience
    importance: float = 0.5  # 0.0-1.0
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


class AgentMemory:
    """Two-tier memory: working (current task) + long-term (cross-task)."""

    def __init__(self, max_working: int = 20) -> None:
        self.max_working = max_working
        self.working: list[MemoryItem] = []
        self.long_term: list[MemoryItem] = []

    def remember_working(self, content: str, category: str = "general", importance: float = 0.5) -> MemoryItem:
        item = MemoryItem(
            id=f"wm_{int(time.time()*1000)}",
            content=content,
            category=category,
            importance=importance,
        )
        self.working.append(item)
        if len(self.working) > self.max_working:
            self.working.pop(0)
        return item

    def remember_long_term(self, content: str, category: str = "general", importance: float = 0.7) -> MemoryItem:
        item = MemoryItem(
            id=f"lt_{int(time.time()*1000)}",
            content=content,
            category=category,
            importance=importance,
        )
        self.long_term.append(item)
        # Promote from working if exists
        self.working = [w for w in self.working if w.content != content]
        return item

    def recall(self, query: str, top_k: int = 5) -> list[MemoryItem]:
        """Simple keyword-based recall. TODO: replace with embedding similarity."""
        all_items = self.working + self.long_term
        scored = []
        query_words = set(query.lower().split())
        for item in all_items:
            content_words = set(item.content.lower().split())
            overlap = len(query_words & content_words)
            recency = 1.0 / (1.0 + (time.time() - item.timestamp) / 3600)
            score = overlap * item.importance * recency
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    def get_context(self) -> str:
        """Get memory context as text for LLM prompt."""
        lines = []
        if self.working:
            lines.append("## Recent Context")
            for item in self.working[-5:]:
                lines.append(f"- [{item.category}] {item.content}")
        if self.long_term:
            lines.append("\n## Key Memories")
            for item in sorted(self.long_term, key=lambda x: x.importance, reverse=True)[:5]:
                lines.append(f"- [{item.category}] {item.content}")
        return "\n".join(lines) if lines else ""

    def clear_working(self) -> None:
        self.working = []
