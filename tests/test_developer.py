"""Tests for DeveloperAgent and ReviewerAgent (with mocked LLM)."""

from unittest.mock import MagicMock

from company.agents import DeveloperAgent, ReviewerAgent
from company.agents.base import Role
from company.agents.parser import ParsedFile
from company.engine import (
    KanbanBoard,
    CodeSandbox,
    GitRepo,
    ArtifactStore,
    MessageChannel,
    IssueType,
    IssueStatus,
    IssuePriority,
    ArtifactType,
)
from company.engine.git import PRStatus


SAMPLE_CODE = """\
### FILE: main.py
```python
print("hello")
```
"""

SAMPLE_TEST_OUTPUT_PASS = """\
1 passed in 0.01s
"""

SAMPLE_TEST_OUTPUT_FAIL = """\
1 failed in 0.01s
FAILED tests/test_main.py::test_hello - AssertionError
"""


def _make_llm_mock(response: str) -> MagicMock:
    llm = MagicMock()
    llm.chat_primary.return_value = response
    llm.chat_fast.return_value = response
    llm.chat.return_value = response
    return llm


def _make_engine_kwargs(llm, sandbox=None):
    return dict(
        llm=llm,
        board=KanbanBoard(),
        sandbox=sandbox or CodeSandbox(),
        git=GitRepo(),
        artifacts=ArtifactStore(),
        channel=MessageChannel(),
    )


def _make_task(board, labels=None):
    issue = board.create_issue(
        title="Implement API",
        description="Build REST API endpoints",
        type=IssueType.TASK,
        priority=IssuePriority.HIGH,
        labels=labels or ["backend"],
    )
    board.move_issue(issue.id, IssueStatus.TODO)
    return issue


# --- DeveloperAgent ---

def test_dev_implement_task():
    llm = _make_llm_mock(SAMPLE_CODE)
    agent = DeveloperAgent(role=Role.BACKEND, **_make_engine_kwargs(llm))
    task = _make_task(agent.board)

    files = agent.implement_task(task, design="## Architecture\nSimple API")
    assert len(files) == 1
    assert files[0].path == "main.py"


def test_dev_write_files():
    llm = _make_llm_mock(SAMPLE_CODE)
    sandbox = CodeSandbox()
    try:
        agent = DeveloperAgent(role=Role.BACKEND, **_make_engine_kwargs(llm, sandbox))
        agent.write_files([ParsedFile(path="test.py", content="print(1)", language="python")])
        assert agent.sandbox.file_exists("test.py")
        assert "print(1)" in agent.sandbox.read_file("test.py")
    finally:
        sandbox.cleanup()


def test_dev_create_pr():
    llm = _make_llm_mock(SAMPLE_CODE)
    agent = DeveloperAgent(role=Role.BACKEND, **_make_engine_kwargs(llm))
    task = _make_task(agent.board)

    files = [ParsedFile(path="main.py", content="print('hello')", language="python")]
    pr = agent.create_pr(task, files)
    assert pr.status == PRStatus.OPEN
    assert pr.author == "backend"
    assert "main.py" in pr.commits[0].files


def test_dev_execute_task_full_cycle():
    """Test full dev cycle: implement → write → test → PR."""
    llm = _make_llm_mock(SAMPLE_CODE)
    sandbox = CodeSandbox()
    try:
        agent = DeveloperAgent(role=Role.BACKEND, **_make_engine_kwargs(llm, sandbox))
        task = _make_task(agent.board)

        pr = agent.execute_task(task, design="## Architecture\nSimple")
        assert pr is not None
        assert task.status == IssueStatus.REVIEW
    finally:
        sandbox.cleanup()


def test_dev_role_frontend():
    llm = _make_llm_mock(SAMPLE_CODE)
    agent = DeveloperAgent(role=Role.FRONTEND, **_make_engine_kwargs(llm))
    assert agent.role == Role.FRONTEND
    assert agent.id == "frontend"


# --- ReviewerAgent ---

def test_reviewer_approves_pr():
    llm = _make_llm_mock("APPROVED")
    agent = ReviewerAgent(**_make_engine_kwargs(llm))

    # Create a PR to review
    agent.git.create_branch("feature/test")
    agent.git.commit("backend", {"main.py": "print(1)"}, "test")
    pr = agent.git.create_pr("feature/test", "Test PR", "testing", "backend")

    review = agent.review_pr(pr)
    assert review.approved is True
    assert pr.status == PRStatus.APPROVED


def test_reviewer_requests_changes():
    llm = _make_llm_mock("""CHANGES_REQUESTED

- FILE: main.py
- LINE: 5
- SEVERITY: warning
- COMMENT: Missing error handling
""")
    agent = ReviewerAgent(**_make_engine_kwargs(llm))

    agent.git.create_branch("feature/test")
    agent.git.commit("backend", {"main.py": "print(1)"}, "test")
    pr = agent.git.create_pr("feature/test", "Test PR", "testing", "backend")

    review = agent.review_pr(pr)
    assert review.changes_requested is True
    assert len(review.comments) == 1
    assert pr.status == PRStatus.CHANGES_REQUESTED
