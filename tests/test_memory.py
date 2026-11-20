"""Tests for agent memory system."""

from company.agents.memory import AgentMemory


def test_working_memory():
    mem = AgentMemory()
    mem.remember_working("Task started", importance=0.8)
    items = mem.working
    assert len(items) == 1
    assert items[0].content == "Task started"


def test_long_term_memory():
    mem = AgentMemory()
    mem.remember_long_term("Use FastAPI for backend", category="decision", importance=0.9)
    assert len(mem.long_term) == 1


def test_recall():
    mem = AgentMemory()
    mem.remember_long_term("FastAPI backend design", category="design")
    mem.remember_long_term("Database uses SQLite", category="decision")
    results = mem.recall("FastAPI design")
    assert len(results) > 0
    assert "FastAPI" in results[0].content


def test_working_overflow():
    mem = AgentMemory(max_working=3)
    for i in range(5):
        mem.remember_working(f"item {i}")
    assert len(mem.working) == 3


def test_get_context():
    mem = AgentMemory()
    mem.remember_working("Current task: implement API")
    mem.remember_long_term("Decision: use REST", category="decision", importance=0.9)
    ctx = mem.get_context()
    assert "Current task" in ctx
    assert "Decision" in ctx
