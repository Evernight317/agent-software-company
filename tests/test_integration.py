"""Integration test — verify engine modules work together."""

from company.engine.board import KanbanBoard, IssueType, IssueStatus, IssuePriority
from company.engine.sandbox import CodeSandbox
from company.engine.git import GitRepo, PRStatus
from company.engine.artifacts import ArtifactStore, ArtifactType
from company.engine.channel import MessageChannel, MessageType


def test_full_workflow():
    """Test a simplified development workflow end-to-end."""
    board = KanbanBoard()
    sandbox = CodeSandbox()
    git = GitRepo()
    artifacts = ArtifactStore()
    channel = MessageChannel()

    try:
        # PM creates requirement
        prd = artifacts.save(ArtifactType.PRD, "PRD", "Build a todo app")
        issue = board.create_issue(
            "Implement API", "Build REST API", IssueType.TASK, IssuePriority.HIGH, ["backend"]
        )
        board.move_issue(issue.id, IssueStatus.TODO)

        # Dev claims task
        tasks = board.get_available_tasks(labels=["backend"])
        assert len(tasks) == 1
        board.assign_issue(issue.id, "backend_dev")
        assert issue.status == IssueStatus.IN_PROGRESS

        # Dev writes code
        sandbox.write_file("main.py", "print('todo app')")
        assert sandbox.file_exists("main.py")

        # Dev commits and creates PR
        git.create_branch("feature/api")
        git.commit("backend_dev", {"main.py": "print('todo app')"}, "implement api")
        pr = git.create_pr("feature/api", "API implementation", "REST API", "backend_dev")

        # Reviewer approves
        git.approve_pr(pr.id, "frontend_dev")
        git.merge_pr(pr.id)
        assert pr.status == PRStatus.MERGED

        # Move issue to done
        board.move_issue(issue.id, IssueStatus.DONE)

        # QA sends message
        channel.send("qa", "backend_dev", "Tests pass!", MessageType.NOTIFICATION)

        # Verify
        assert len(git.log()) == 1
        assert len(board.get_issues_by_status(IssueStatus.DONE)) == 1
        assert artifacts.get(prd.id) is not None
        msg = channel.get_inbox("backend_dev")
        assert len(msg) >= 1

    finally:
        sandbox.cleanup()
