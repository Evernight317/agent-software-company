"""Development logger — real-time event streaming to terminal and file."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


@dataclass
class LogEntry:
    timestamp: float
    agent: str  # Agent name or "system"
    event: str
    detail: str
    level: str = "info"  # info, warning, error, success


class DevLogger:
    """Real-time development event logger with Rich terminal output."""

    ROLE_COLORS = {
        "PM": "cyan",
        "Architect": "magenta",
        "Backend": "green",
        "Frontend": "blue",
        "QA": "yellow",
        "DevOps": "red",
        "system": "white",
        "user": "bold white",
    }

    LEVEL_STYLES = {
        "info": "",
        "warning": "bold yellow",
        "error": "bold red",
        "success": "bold green",
    }

    def __init__(self, log_dir: str = "output/logs", console: Optional[Console] = None) -> None:
        self.console = console or Console()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._entries: list[LogEntry] = []
        self._file_path = self.log_dir / f"dev_{int(time.time())}.log"

    def log(self, agent: str, event: str, detail: str, level: str = "info") -> None:
        entry = LogEntry(
            timestamp=time.time(),
            agent=agent,
            event=event,
            detail=detail,
            level=level,
        )
        self._entries.append(entry)
        self._print(entry)
        self._write_file(entry)

    def _print(self, entry: LogEntry) -> None:
        color = self.ROLE_COLORS.get(entry.agent, "white")
        time_str = time.strftime("%H:%M:%S", time.localtime(entry.timestamp))
        style = self.LEVEL_STYLES.get(entry.level, "")

        header = f"[{time_str}] [{color}]{entry.agent}[/{color}]"
        if style:
            header = f"[{style}]{header}[/{style}]"

        self.console.print(f"{header} {entry.event}")
        if entry.detail:
            self.console.print(f"  {entry.detail}", style="dim")

    def _write_file(self, entry: LogEntry) -> None:
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry.timestamp))
        line = f"[{time_str}] [{entry.level.upper()}] {entry.agent} | {entry.event}: {entry.detail}\n"
        with open(self._file_path, "a", encoding="utf-8") as f:
            f.write(line)

    def phase(self, name: str) -> None:
        self.console.print()
        self.console.print(Panel(Text(name, style="bold cyan"), border_style="cyan", padding=(0, 2)))
        self.log("system", "phase", f"Entering phase: {name}")

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self._entries:
            counts[entry.agent] = counts.get(entry.agent, 0) + 1
        return counts

    def print_board(self, board) -> None:
        from company.engine.board import IssueStatus
        self.console.print("\n[bold]Project Board[/bold]")
        for status in IssueStatus:
            issues = board.get_issues_by_status(status)
            if issues:
                self.console.print(f"  [{status.value}] ({len(issues)})")
                for issue in issues:
                    assignee = issue.assignee or "unassigned"
                    self.console.print(f"    #{issue.id} {issue.title} — {assignee}")
        self.console.print()
