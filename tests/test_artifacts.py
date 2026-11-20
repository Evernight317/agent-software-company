"""Tests for the artifact store."""

from company.engine.artifacts import ArtifactStore, ArtifactType


def test_save_and_get():
    store = ArtifactStore()
    art = store.save(ArtifactType.PRD, "PRD", "content here", author="pm")
    fetched = store.get(art.id)
    assert fetched is not None
    assert fetched.title == "PRD"
    assert fetched.content == "content here"


def test_get_by_type():
    store = ArtifactStore()
    store.save(ArtifactType.PRD, "PRD v1", "c1")
    store.save(ArtifactType.DESIGN, "Design", "c2")
    prds = store.get_by_type(ArtifactType.PRD)
    assert len(prds) == 1
    designs = store.get_by_type(ArtifactType.DESIGN)
    assert len(designs) == 1


def test_update():
    store = ArtifactStore()
    art = store.save(ArtifactType.CODE, "main.py", "v1")
    updated = store.update(art.id, "v2", "dev")
    assert updated.version == 2
    assert updated.content == "v2"


def test_summary():
    store = ArtifactStore()
    store.save(ArtifactType.PRD, "p", "c")
    store.save(ArtifactType.CODE, "c1", "c")
    store.save(ArtifactType.CODE, "c2", "c")
    summary = store.summary()
    assert summary["prd"] == 1
    assert summary["code"] == 2
