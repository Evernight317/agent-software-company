"""Parser — extract structured data from LLM-generated markdown.

Handles three types of parsing:
- PRD issues (from PM output)
- Design tasks (from Architect output)
- Code files and code review (from Developer/Reviewer output)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ============================================================================
# Data classes
# ============================================================================


@dataclass
class ParsedIssue:
    """An issue parsed from PRD or design output."""
    title: str
    description: str
    priority: int = 1  # 0-2
    labels: list[str] = field(default_factory=list)


@dataclass
class ParsedFile:
    """A file extracted from LLM output."""
    path: str
    content: str
    language: str = ""


@dataclass
class ReviewFeedback:
    """A single review comment."""
    file: str
    line: int
    severity: str  # suggestion / warning / blocking
    comment: str


@dataclass
class ParsedReview:
    """A code review result parsed from LLM output."""
    approved: bool = False
    changes_requested: bool = False
    comments: list[ReviewFeedback] = field(default_factory=list)


# ============================================================================
# PRD / Design parsing
# ============================================================================


def parse_prd_issues(prd_text: str) -> list[ParsedIssue]:
    """Parse issue lines from a PRD document.

    Expected format (from PM_ANALYZE prompt):
        - [P{priority}] {title} | {description} | labels: {comma-separated}
    """
    issues: list[ParsedIssue] = []
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
    """Extract the content under a markdown heading."""
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
            next_heading = re.match(r"^(#+)\s+", line)
            if next_heading and len(next_heading.group(1)) <= heading_level:
                break
            captured.append(line)

    return "\n".join(captured).strip()


# ============================================================================
# Code file parsing
# ============================================================================


def parse_code_files(llm_output: str) -> list[ParsedFile]:
    """Extract files from LLM output.

    Expected format:
        ### FILE: path/to/file.py
        ```python
        code here
        ```
    """
    files: list[ParsedFile] = []
    pattern = r"###\s*FILE:\s*(.+?)\n```(\w*)\n(.*?)```"
    matches = re.findall(pattern, llm_output, re.DOTALL)

    for path, language, content in matches:
        files.append(ParsedFile(
            path=path.strip(),
            content=content.strip() + "\n",
            language=language.strip(),
        ))

    return files


# ============================================================================
# Code review parsing
# ============================================================================


def parse_review(llm_output: str) -> ParsedReview:
    """Parse a code review response from the LLM."""
    result = ParsedReview()

    upper = llm_output.upper().strip()
    if "APPROVED" in upper:
        result.approved = True
    if "CHANGES_REQUESTED" in upper:
        result.changes_requested = True
        result.approved = False

    lines = llm_output.split("\n")
    current: dict[str, str] = {}

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- FILE:") or stripped.startswith("FILE:"):
            if current:
                result.comments.append(_make_feedback(current))
            current = {"file": stripped.split(":", 1)[1].strip()}
        elif stripped.startswith("- LINE:") or stripped.startswith("LINE:"):
            current["line"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- SEVERITY:") or stripped.startswith("SEVERITY:"):
            current["severity"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- COMMENT:") or stripped.startswith("COMMENT:"):
            current["comment"] = stripped.split(":", 1)[1].strip()

    if current:
        result.comments.append(_make_feedback(current))

    return result


def _make_feedback(data: dict[str, str]) -> ReviewFeedback:
    try:
        line = int(data.get("line", "0"))
    except ValueError:
        line = 0
    return ReviewFeedback(
        file=data.get("file", ""),
        line=line,
        severity=data.get("severity", "suggestion"),
        comment=data.get("comment", ""),
    )
