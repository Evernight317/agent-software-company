"""Parser — extract structured data from LLM-generated markdown."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedIssue:
    """An issue parsed from PRD or design output."""
    title: str
    description: str
    priority: int = 1  # 0-2
    labels: list[str] = field(default_factory=list)


def parse_prd_issues(prd_text: str) -> list[ParsedIssue]:
    """Parse issue lines from a PRD document.

    Expected format (from PM_ANALYZE prompt):
        - [P{priority}] {title} | {description} | labels: {comma-separated}
    """
    issues: list[ParsedIssue] = []
    # Match lines like: - [P0] Title | Description | labels: backend, api
    pattern = r"^\s*[-*]\s*\[P([0-2])\]\s*(.+?)\s*\|\s*(.+?)(?:\s*\|\s*labels?\s*:\s*(.+))?\s*$"

    in_issues_section = False
    for line in prd_text.split("\n"):
        stripped = line.strip().lower()
        if stripped.startswith("##") and "issue" in stripped:
            in_issues_section = True
            continue
        if stripped.startswith("##") and in_issues_section:
            in_issues_section = False
            continue

        match = re.match(pattern, line)
        if match:
            priority = int(match.group(1))
            title = match.group(2).strip()
            description = match.group(3).strip()
            labels_str = match.group(4) or ""
            labels = [l.strip() for l in labels_str.split(",") if l.strip()]
            issues.append(ParsedIssue(
                title=title,
                description=description,
                priority=priority,
                labels=labels,
            ))

    return issues


def parse_design_tasks(design_text: str) -> list[ParsedIssue]:
    """Parse development tasks from an architecture design document.

    Expected format (from ARCHITECT_DESIGN prompt):
        - [{type}] {title} | {description} | labels: {comma-separated}
    """
    tasks: list[ParsedIssue] = []
    # Match: - [backend] Title | Description | labels: something
    pattern = r"^\s*[-*]\s*\[(\w+)\]\s*(.+?)\s*\|\s*(.+?)(?:\s*\|\s*labels?\s*:\s*(.+))?\s*$"

    in_tasks_section = False
    for line in design_text.split("\n"):
        stripped = line.strip().lower()
        if stripped.startswith("##") and "task" in stripped:
            in_tasks_section = True
            continue
        if stripped.startswith("##") and in_tasks_section:
            in_tasks_section = False
            continue

        match = re.match(pattern, line)
        if match:
            task_type = match.group(1).strip().lower()
            title = match.group(2).strip()
            description = match.group(3).strip()
            labels_str = match.group(4) or ""
            labels = [l.strip() for l in labels_str.split(",") if l.strip()]
            if task_type not in labels:
                labels.insert(0, task_type)
            tasks.append(ParsedIssue(
                title=title,
                description=description,
                priority=1,
                labels=labels,
            ))

    return tasks


def parse_markdown_section(text: str, heading: str) -> str:
    """Extract the content under a markdown heading.

    Returns the text between the heading and the next heading of same/higher level.
    """
    pattern = rf"^#+\s*{re.escape(heading)}\s*$"
    lines = text.split("\n")
    capturing = False
    captured: list[str] = []
    heading_level = 0

    for line in lines:
        if re.match(rf"^#+\s*{re.escape(heading)}\s*$", line, re.IGNORECASE):
            capturing = True
            heading_level = len(line) - len(line.lstrip("#"))
            continue
        if capturing:
            # Stop at same or higher level heading
            next_heading = re.match(r"^(#+)\s+", line)
            if next_heading and len(next_heading.group(1)) <= heading_level:
                break
            captured.append(line)

    return "\n".join(captured).strip()
