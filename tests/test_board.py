"""Tests for the Kanban board system."""

from company.engine.board import (
    KanbanBoard,
    Issue,
    IssueType,
    IssueStatus,
    IssuePriority,
)


def test_create_issue():
    board = KanbanBoard()
    issue = board.create_issue(
        title="Test issue",
        description="Test description",
        type=IssueType.TASK,
        priority=IssuePriority.HIGH,
        labels=["backend"],
    )
    assert issue.title == "Test issue"
    assert issue.status == IssueStatus.BACKLOG
    assert issue.priority == IssuePriority.HIGH
    assert "backend" in issue.labels


def test_assign_issue():
    board = KanbanBoard()
    issue = board.create_issue("Test", "desc")
    board.move_issue(issue.id, IssueStatus.TODO)
    board.assign_issue(issue.id, "backend_agent")
    assert issue.assignee == "backend_agent"
    assert issue.status == IssueStatus.IN_PROGRESS


def test_move_issue():
    board = KanbanBoard()
    issue = board.create_issue("Test", "desc")
    board.move_issue(issue.id, IssueStatus.DONE)
    assert issue.status == IssueStatus.DONE


def test_get_available_tasks():
    board = KanbanBoard()
    i1 = board.create_issue("Task 1", "desc", labels=["backend"])
    i2 = board.create_issue("Task 2", "desc", labels=["frontend"])
    board.move_issue(i1.id, IssueStatus.TODO)
    board.move_issue(i2.id, IssueStatus.TODO)

    backend_tasks = board.get_available_tasks(labels=["backend"])
    assert len(backend_tasks) == 1
    assert backend_tasks[0].title == "Task 1"


def test_add_comment():
    board = KanbanBoard()
    issue = board.create_issue("Test", "desc")
    comment = board.add_comment(issue.id, "pm", "Need more details")
    assert comment is not None
    assert comment.author == "pm"
    assert len(issue.comments) == 1


def test_summary():
    board = KanbanBoard()
    board.create_issue("T1", "d")
    board.create_issue("T2", "d")
    summary = board.summary()
    assert summary["backlog"] == 2


def test_has_todo():
    board = KanbanBoard()
    assert not board.has_todo_tasks()
    issue = board.create_issue("T1", "d")
    board.move_issue(issue.id, IssueStatus.TODO)
    assert board.has_todo_tasks()
