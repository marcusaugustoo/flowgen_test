"""Tests for the artifact system."""

import tempfile
from pathlib import Path

import pytest

from src.orchestration.artifacts import Artifact, ArtifactStore


class TestArtifact:
    """Tests for Artifact."""

    def test_creation(self):
        artifact = Artifact(type="code", content="def f(): pass", created_by="developer")
        assert artifact.type == "code"
        assert artifact.artifact_id  # Auto-generated
        assert artifact.timestamp

    def test_to_dict(self):
        artifact = Artifact(type="requirements", content="req content", created_by="RE")
        d = artifact.to_dict()
        assert d["type"] == "requirements"
        assert d["created_by"] == "RE"

    def test_to_json(self):
        artifact = Artifact(type="code", content="code", created_by="dev")
        j = artifact.to_json()
        assert '"type": "code"' in j


class TestArtifactStore:
    """Tests for ArtifactStore."""

    def test_store_and_get(self):
        store = ArtifactStore()
        art = Artifact(type="code", content="code", created_by="dev")
        art_id = store.store(art)
        retrieved = store.get(art_id)
        assert retrieved is not None
        assert retrieved.content == "code"

    def test_get_nonexistent(self):
        store = ArtifactStore()
        assert store.get("nonexistent") is None

    def test_get_by_type(self):
        store = ArtifactStore()
        store.store(Artifact(type="code", content="c1", created_by="dev"))
        store.store(Artifact(type="requirements", content="r1", created_by="re"))
        store.store(Artifact(type="code", content="c2", created_by="dev"))
        assert len(store.get_by_type("code")) == 2
        assert len(store.get_by_type("requirements")) == 1

    def test_get_by_creator(self):
        store = ArtifactStore()
        store.store(Artifact(type="code", content="c1", created_by="dev"))
        store.store(Artifact(type="req", content="r1", created_by="re"))
        assert len(store.get_by_creator("dev")) == 1

    def test_save_and_load(self):
        store = ArtifactStore()
        store.store(Artifact(type="code", content="hello", created_by="dev"))
        store.store(Artifact(type="req", content="world", created_by="re"))

        with tempfile.TemporaryDirectory() as tmpdir:
            store.save(tmpdir)
            loaded = ArtifactStore.load(tmpdir)
            assert loaded.count == 2

    def test_clear(self):
        store = ArtifactStore()
        store.store(Artifact(type="code", content="c", created_by="dev"))
        store.clear()
        assert store.count == 0
