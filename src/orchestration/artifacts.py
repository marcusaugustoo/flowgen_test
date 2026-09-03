"""
Artifact storage and management.

Each agent produces structured artifacts that are persisted and
passed through the context to subsequent agents.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class Artifact:
    """
    A structured output produced by an agent.

    Attributes:
        artifact_id: Unique identifier.
        type: Artifact type (e.g., 'requirements', 'design', 'code', 'tests', 'test_failure_report').
        content: The main content of the artifact.
        language: Programming language (for code artifacts).
        created_by: Name of the agent that created this artifact.
        timestamp: ISO 8601 creation timestamp.
        metadata: Additional metadata.
    """
    artifact_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: str = ""
    content: str = ""
    language: str = "python"
    created_by: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "artifact_id": self.artifact_id,
            "type": self.type,
            "content": self.content,
            "language": self.language,
            "created_by": self.created_by,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class ArtifactStore:
    """
    Stores and persists artifacts produced during an experiment run.

    Artifacts are indexed by artifact_id and can be queried by type or creator.
    """

    def __init__(self) -> None:
        self._artifacts: dict[str, Artifact] = {}

    def store(self, artifact: Artifact) -> str:
        """Store an artifact and return its ID."""
        self._artifacts[artifact.artifact_id] = artifact
        return artifact.artifact_id

    def get(self, artifact_id: str) -> Optional[Artifact]:
        """Retrieve an artifact by ID."""
        return self._artifacts.get(artifact_id)

    def get_by_type(self, artifact_type: str) -> list[Artifact]:
        """Get all artifacts of a specific type."""
        return [a for a in self._artifacts.values() if a.type == artifact_type]

    def get_by_creator(self, creator: str) -> list[Artifact]:
        """Get all artifacts created by a specific agent."""
        return [a for a in self._artifacts.values() if a.created_by == creator]

    def get_latest_by_type(self, artifact_type: str) -> Optional[Artifact]:
        """Get the most recent artifact of a given type."""
        artifacts = self.get_by_type(artifact_type)
        if not artifacts:
            return None
        return max(artifacts, key=lambda a: a.timestamp)

    @property
    def all_artifacts(self) -> list[Artifact]:
        """Get all stored artifacts."""
        return list(self._artifacts.values())

    @property
    def count(self) -> int:
        """Number of stored artifacts."""
        return len(self._artifacts)

    def clear(self) -> None:
        """Clear all artifacts."""
        self._artifacts.clear()

    def save(self, directory: str | Path) -> None:
        """Save all artifacts to a directory (one JSON file per artifact)."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        for artifact in self._artifacts.values():
            filepath = directory / f"{artifact.artifact_id}.json"
            with open(filepath, "w") as f:
                f.write(artifact.to_json())

    @classmethod
    def load(cls, directory: str | Path) -> ArtifactStore:
        """Load all artifacts from a directory."""
        store = cls()
        directory = Path(directory)
        if directory.exists():
            for filepath in directory.glob("*.json"):
                with open(filepath, "r") as f:
                    data = json.load(f)
                    artifact = Artifact(**data)
                    store.store(artifact)
        return store
