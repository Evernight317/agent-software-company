"""Tests for the simulated Git system."""

from company.engine.git import GitRepo, PRStatus


def test_commit():
    repo = GitRepo()
    commit = repo.commit("backend_dev", {"main.py": "print('hi')"}, "initial")
    assert commit.author == "backend_dev"
    assert "main.py" in commit.files


def test_create_branch_and_commit():
    repo = GitRepo()
    repo.create_branch("feature/api")
    repo.commit("backend_dev", {"api.py": "# api"}, "add api")
    assert len(repo.branches["feature/api"]) == 1


def test_create_pr_and_merge():
    repo = GitRepo()
    repo.create_branch("feature/test")
    repo.commit("dev", {"test.py": "# test"}, "add test")
    pr = repo.create_pr("feature/test", "Add test", "test desc", "dev")
    assert pr.status == PRStatus.OPEN
    repo.approve_pr(pr.id, "reviewer")
    assert pr.status == PRStatus.APPROVED
    repo.merge_pr(pr.id)
    assert pr.status == PRStatus.MERGED
    assert len(repo.main_branch) == 1


def test_review_comment():
    repo = GitRepo()
    repo.create_branch("feat")
    repo.commit("dev", {"code.py": "# code"}, "add code")
    pr = repo.create_pr("feat", "PR", "desc", "dev")
    rc = repo.add_review_comment(pr.id, "reviewer", "code.py", 5, "fix this", "warning")
    assert rc is not None
    assert pr.status == PRStatus.CHANGES_REQUESTED
    assert len(pr.review_comments) == 1


def test_get_files():
    repo = GitRepo()
    repo.commit("dev", {"a.py": "1", "b.py": "2"}, "init")
    repo.commit("dev", {"c.py": "3"}, "add c")
    files = repo.get_files()
    assert "a.py" in files
    assert "c.py" in files
