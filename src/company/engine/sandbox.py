"""Code sandbox — isolated file system and command execution."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str
    duration: float

    @property
    def success(self) -> bool:
        return self.exit_code == 0


@dataclass
class TestResult:
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
    raw_output: str = ""
    duration: float = 0.0

    @property
    def success(self) -> bool:
        return self.failed == 0 and self.total > 0

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0


@dataclass
class Snapshot:
    id: str
    path: str
    timestamp: float = field(default_factory=time.time)


class CodeSandbox:
    """Isolated execution environment using subprocess + temp directory."""

    def __init__(self, project_dir: str | None = None, timeout: int = 120) -> None:
        self.timeout = timeout
        if project_dir:
            self.workdir = Path(project_dir)
            self.workdir.mkdir(parents=True, exist_ok=True)
        else:
            self._tmpdir = tempfile.mkdtemp(prefix="asc_sandbox_")
            self.workdir = Path(self._tmpdir)
        self._snapshots: list[Snapshot] = []

    @property
    def root(self) -> Path:
        return self.workdir

    # --- File operations ---

    def write_file(self, path: str, content: str) -> Path:
        full = self.workdir / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        return full

    def read_file(self, path: str) -> str:
        full = self.workdir / path
        return full.read_text(encoding="utf-8")

    def list_files(self, directory: str = ".") -> list[str]:
        full = self.workdir / directory
        if not full.exists():
            return []
        return [
            str(f.relative_to(self.workdir))
            for f in full.rglob("*")
            if f.is_file() and "__pycache__" not in str(f)
        ]

    def file_exists(self, path: str) -> bool:
        return (self.workdir / path).exists()

    def delete_file(self, path: str) -> None:
        full = self.workdir / path
        if full.exists():
            full.unlink()

    # --- Command execution ---

    def run_command(self, cmd: str | list[str], cwd: str | None = None) -> CommandResult:
        if isinstance(cmd, str):
            shell_cmd: str | list[str] = cmd
            shell_flag = True
        else:
            shell_cmd = cmd
            shell_flag = False

        work_path = self.workdir / (cwd or "")
        work_path.mkdir(parents=True, exist_ok=True)

        start = time.time()
        try:
            proc = subprocess.run(
                shell_cmd,
                cwd=str(work_path),
                shell=shell_flag,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            duration = time.time() - start
            return CommandResult(
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration=duration,
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            return CommandResult(
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {self.timeout}s",
                duration=duration,
            )

    def install_deps(self, deps: list[str], manager: str = "pip") -> CommandResult:
        if manager == "pip":
            cmd = ["pip", "install"] + deps
        elif manager == "npm":
            cmd = ["npm", "install"] + deps
        else:
            cmd = [manager, "install"] + deps
        return self.run_command(cmd)

    def run_tests(self, test_cmd: str | None = None) -> TestResult:
        if test_cmd is None:
            test_cmd = "python -m pytest -v --tb=short 2>&1"
        result = self.run_command(test_cmd)
        return self._parse_test_output(result)

    def _parse_test_output(self, result: CommandResult) -> TestResult:
        output = result.stdout + result.stderr
        test_result = TestResult(raw_output=output, duration=result.duration)

        # Parse pytest output
        for line in output.splitlines():
            line = line.strip()
            if "passed" in line and "failed" in line:
                # "3 passed, 1 failed"
                parts = line.split(",")
                for part in parts:
                    part = part.strip()
                    if "passed" in part:
                        try:
                            test_result.passed = int(part.split()[0])
                        except ValueError:
                            pass
                    elif "failed" in part:
                        try:
                            test_result.failed = int(part.split()[0])
                        except ValueError:
                            pass
            elif "passed" in line and "failed" not in line:
                try:
                    test_result.passed = int(line.split()[0])
                except ValueError:
                    pass
            elif "failed" in line:
                try:
                    test_result.failed = int(line.split()[0])
                except ValueError:
                    pass
            if "FAILED" in line or "ERROR" in line:
                test_result.errors.append(line)

        test_result.total = test_result.passed + test_result.failed
        return test_result

    # --- Snapshots ---

    def snapshot(self, name: str | None = None) -> Snapshot:
        snap_id = name or f"snap_{len(self._snapshots)}"
        snap_dir = self.workdir / ".snapshots" / snap_id
        if snap_dir.exists():
            shutil.rmtree(snap_dir)
        snap_dir.mkdir(parents=True)
        for item in self.workdir.iterdir():
            if item.name == ".snapshots":
                continue
            dest = snap_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        snap = Snapshot(id=snap_id, path=str(snap_dir))
        self._snapshots.append(snap)
        return snap

    def restore(self, snapshot_id: str) -> bool:
        snap = next((s for s in self._snapshots if s.id == snapshot_id), None)
        if snap is None:
            return False
        snap_path = Path(snap.path)
        # Clear current workdir (except .snapshots)
        for item in self.workdir.iterdir():
            if item.name == ".snapshots":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        # Restore from snapshot
        for item in snap_path.iterdir():
            dest = self.workdir / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        return True

    # --- Cleanup ---

    def cleanup(self) -> None:
        if hasattr(self, "_tmpdir") and os.path.exists(self._tmpdir):
            shutil.rmtree(self._tmpdir)
