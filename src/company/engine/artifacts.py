"""Artifact store — manage project deliverables (PRD, design, code, tests, deploy)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ArtifactType(str, Enum):
    PRD = "prd"
    DESIGN = "design"
    CODE = "code"
    TEST_REPORT = "test_report"
    DEPLOY_CONFIG = "deploy_config"
    README = "readme"
    OTHER = "other"


@dataclass
class Artifact:
    id: str
    type: ArtifactType
    title: str
    content: str
    file_path: Optional[str] = None  # path in sandbox
    author: str = ""  # Agent ID
    version: int = 1
    dependencies: list[str] = field(default_factory=list)  # other artifact IDs
    created_at: float = field(default_factory=time.time)


class ArtifactStore:
    """Central store for all project deliverables."""

    def __init__(self) -> None:
        self._artifacts: dict[str, Artifact] = {}
        self._by_type: dict[ArtifactType, list[str]] = {}

    def save(
        self,
        type: ArtifactType,
        title: str,
        content: str,
        author: str = "",
        file_path: str | None = None,
        dependencies: list[str] | None = None,
    ) -> Artifact:
        artifact_id = str(uuid.uuid4())[:8]
        artifact = Artifact(
            id=artifact_id,
            type=type,
            title=title,
            content=content,
            file_path=file_path,
            author=author,
            dependencies=dependencies or [],
        )
        self._artifacts[artifact_id] = artifact
        self._by_type.setdefault(type, []).append(artifact_id)
        return artifact

    def get(self, artifact_id: str) -> Optional[Artifact]:
        return self._artifacts.get(artifact_id)

    def get_by_type(self, type: ArtifactType) -> list[Artifact]:
        ids = self._by_type.get(type, [])
        return [self._artifacts[i] for i in ids if i in self._artifacts]

    def get_latest(self, type: ArtifactType) -> Optional[Artifact]:
        artifacts = self.get_by_type(type)
        if not artifacts:
            return None
        return max(artifacts, key=lambda a: a.version)

    def update(
        self,
        artifact_id: str,
        content: str,
        author: str = "",
    ) -> Optional[Artifact]:
        artifact = self.get(artifact_id)
        if artifact is None:
            return None
        artifact.version += 1
        artifact.content = content
        artifact.author = author or artifact.author
        artifact.created_at = time.time()
        return artifact

    def list_all(self) -> list[Artifact]:
        return list(self._artifacts.values())

    def summary(self) -> dict[str, int]:
        return {t.value: len(self._by_type.get(t, [])) for t in ArtifactType}
