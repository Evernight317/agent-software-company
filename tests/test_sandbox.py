"""Tests for the code sandbox."""

import os
from company.engine.sandbox import CodeSandbox


def test_write_and_read_file():
    sandbox = CodeSandbox()
    try:
        sandbox.write_file("test.txt", "hello world")
        assert sandbox.read_file("test.txt") == "hello world"
    finally:
        sandbox.cleanup()


def test_list_files():
    sandbox = CodeSandbox()
    try:
        sandbox.write_file("src/main.py", "print('hi')")
        sandbox.write_file("README.md", "# test")
        files = sandbox.list_files()
        assert "src/main.py" in files
        assert "README.md" in files
    finally:
        sandbox.cleanup()


def test_file_exists():
    sandbox = CodeSandbox()
    try:
        assert not sandbox.file_exists("nope.txt")
        sandbox.write_file("yes.txt", "content")
        assert sandbox.file_exists("yes.txt")
    finally:
        sandbox.cleanup()


def test_run_command():
    sandbox = CodeSandbox()
    try:
        result = sandbox.run_command("echo 'hello'")
        assert result.success
        assert "hello" in result.stdout
    finally:
        sandbox.cleanup()


def test_snapshot_and_restore():
    sandbox = CodeSandbox()
    try:
        sandbox.write_file("data.txt", "original")
        snap = sandbox.snapshot("v1")
        sandbox.write_file("data.txt", "modified")
        assert sandbox.read_file("data.txt") == "modified"
        sandbox.restore("v1")
        assert sandbox.read_file("data.txt") == "original"
    finally:
        sandbox.cleanup()
