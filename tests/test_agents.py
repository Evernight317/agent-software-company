"""Tests for PM and Architect agents (with mocked LLM)."""

from unittest.mock import MagicMock, patch

from company.agents import PMAgent, ArchitectAgent
from company.engine import (
    KanbanBoard,
    CodeSandbox,
    GitRepo,
    ArtifactStore,
    MessageChannel,
    ArtifactType,
    IssueStatus,
)


SAMPLE_PRD = """\
## Overview
A todo app.

## Issues
- [P0] Implement API | REST CRUD endpoints | labels: backend, api
- [P1] Build UI | React todo list | labels: frontend
"""

SAMPLE_DESIGN = """\
## Tasks
- [backend] Define models | SQLAlchemy models | labels: models
- [frontend] Create views | React views | labels: ui
"""


def _make_llm_mock(response: str) -> MagicMock:
    llm = MagicMock()
    llm.chat_primary.return_value = response
    llm.chat_fast.return_value = response
    llm.chat.return_value = response
    return llm


def _make_engine_kwargs(llm):
    return dict(
        llm=llm,
        board=KanbanBoard(),
        sandbox=CodeSandbox(),
        git=GitRepo(),
        artifacts=ArtifactStore(),
        channel=MessageChannel(),
    )


# --- PM Agent ---

def test_pm_analyze_requirement_saves_prd():
    llm = _make_llm_mock(SAMPLE_PRD)
    agent = PMAgent(**_make_engine_kwargs(llm))

    prd = agent.analyze_requirement("Build a todo app")

    assert prd == SAMPLE_PRD
    prd_artifacts = agent.artifacts.get_by_type(ArtifactType.PRD)
    assert len(prd_artifacts) == 1
    assert prd_artifacts[0].content == SAMPLE_PRD


def test_pm_create_issues_from_prd():
    llm = _make_llm_mock(SAMPLE_PRD)
    agent = PMAgent(**_make_engine_kwargs(llm))

    agent.analyze_requirement("Build a todo app")
    issues = agent.create_issues_from_prd(SAMPLE_PRD)

    assert len(issues) == 2
    assert "backend" in issues[0].labels
    assert issues[0].status == IssueStatus.TODO


def test_pm_memory_remembers():
    llm = _make_llm_mock(SAMPLE_PRD)
    agent = PMAgent(**_make_engine_kwargs(llm))

    agent.analyze_requirement("Build a todo app")

    assert len(agent.memory.working) > 0
    assert any("PRD" in m.content for m in agent.memory.long_term)


# --- Architect Agent ---

def test_architect_design_saves_artifact():
    llm = _make_llm_mock(SAMPLE_DESIGN)
    agent = ArchitectAgent(**_make_engine_kwargs(llm))

    design = agent.design(SAMPLE_PRD)

    assert design == SAMPLE_DESIGN
    design_artifacts = agent.artifacts.get_by_type(ArtifactType.DESIGN)
    assert len(design_artifacts) == 1


def test_architect_create_tasks_from_design():
    llm = _make_llm_mock(SAMPLE_DESIGN)
    agent = ArchitectAgent(**_make_engine_kwargs(llm))

    agent.design(SAMPLE_PRD)
    tasks = agent.create_tasks_from_design(SAMPLE_DESIGN)

    assert len(tasks) == 2
    assert "backend" in tasks[0].labels
    assert "frontend" in tasks[1].labels
    assert tasks[0].status == IssueStatus.TODO


def test_architect_reads_prd_from_artifacts():
    """Architect should fetch the latest PRD from the artifact store."""
    llm = _make_llm_mock(SAMPLE_DESIGN)
    kwargs = _make_engine_kwargs(llm)

    # PM runs first, saves PRD (mock returns SAMPLE_DESIGN as content)
    pm = PMAgent(**kwargs)
    pm.analyze_requirement("Build a todo app")

    # The stored PRD content is whatever PM saved
    from company.engine import ArtifactType
    stored_prd = kwargs["artifacts"].get_latest(ArtifactType.PRD)
    assert stored_prd is not None

    # Architect should use the saved PRD
    architect = ArchitectAgent(**kwargs)
    architect.design("")  # empty arg — should fetch from artifacts

    # Verify LLM was called with the stored PRD content
    call_args = llm.chat_primary.call_args
    messages = call_args[0][0]
    user_msg = messages[-1]["content"]
    assert stored_prd.content in user_msg
