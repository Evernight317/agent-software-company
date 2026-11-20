"""Tests for the PRD/design markdown parser."""

from company.agents.parser import parse_prd_issues, parse_design_tasks, parse_markdown_section


SAMPLE_PRD = """\
## Overview
A simple todo application.

## User Stories
- As a user, I want to create todos so that I can track tasks.

## Issues
- [P0] Implement Todo CRUD API | Create REST endpoints for create/read/update/delete | labels: backend, api
- [P1] Build Todo UI Components | React components for todo list | labels: frontend, ui
- [P2] Add dark mode | Support dark theme | labels: frontend
"""


def test_parse_prd_issues_count():
    issues = parse_prd_issues(SAMPLE_PRD)
    assert len(issues) == 3


def test_parse_prd_issue_priority():
    issues = parse_prd_issues(SAMPLE_PRD)
    assert issues[0].priority == 0
    assert issues[1].priority == 1
    assert issues[2].priority == 2


def test_parse_prd_issue_labels():
    issues = parse_prd_issues(SAMPLE_PRD)
    assert "backend" in issues[0].labels
    assert "api" in issues[0].labels
    assert "frontend" in issues[1].labels


def test_parse_prd_issue_title_desc():
    issues = parse_prd_issues(SAMPLE_PRD)
    assert "Todo CRUD API" in issues[0].title
    assert "REST endpoints" in issues[0].description


def test_parse_prd_empty():
    issues = parse_prd_issues("No issues here")
    assert issues == []


SAMPLE_DESIGN = """\
## Architecture Overview
Simple layered architecture.

## Tasks
- [backend] Implement models | Define SQLAlchemy models | labels: models, db
- [backend] Implement API routes | Create FastAPI routers | labels: api
- [frontend] Create components | Build React components | labels: ui
- [shared] Define types | Shared TypeScript types | labels: types
"""


def test_parse_design_tasks_count():
    tasks = parse_design_tasks(SAMPLE_DESIGN)
    assert len(tasks) == 4


def test_parse_design_task_type_in_labels():
    tasks = parse_design_tasks(SAMPLE_DESIGN)
    assert "backend" in tasks[0].labels
    assert "frontend" in tasks[2].labels
    assert "shared" in tasks[3].labels


def test_parse_design_task_title():
    tasks = parse_design_tasks(SAMPLE_DESIGN)
    assert "models" in tasks[0].title.lower()


def test_parse_markdown_section():
    section = parse_markdown_section(SAMPLE_PRD, "Overview")
    assert "todo application" in section.lower()


def test_parse_markdown_section_not_found():
    section = parse_markdown_section(SAMPLE_PRD, "Nonexistent")
    assert section == ""
