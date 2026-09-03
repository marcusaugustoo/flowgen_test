"""Tests for SharedContext."""

import json
import tempfile
from pathlib import Path

import pytest

from src.orchestration.context import SharedContext


class TestSharedContext:
    """Tests for SharedContext."""

    def test_initial_state(self):
        ctx = SharedContext()
        assert ctx.problem == ""
        assert ctx.code == ""
        assert ctx.failure_reports == []

    def test_get_context_for_requirement_engineer(self, sample_context):
        ctx_dict = sample_context.get_context_for_agent("requirement_engineer")
        assert "problem" in ctx_dict
        assert "requirements" not in ctx_dict
        assert "design" not in ctx_dict

    def test_get_context_for_architect(self, sample_context):
        sample_context.requirements = "Some requirements"
        ctx_dict = sample_context.get_context_for_agent("architect")
        assert "problem" in ctx_dict
        assert "requirements" in ctx_dict
        assert "design" not in ctx_dict

    def test_get_context_for_developer(self, sample_context):
        sample_context.requirements = "req"
        sample_context.design = "design"
        ctx_dict = sample_context.get_context_for_agent("developer")
        assert "problem" in ctx_dict
        assert "requirements" in ctx_dict
        assert "design" in ctx_dict

    def test_get_context_for_developer_with_failures(self, sample_context):
        sample_context.requirements = "req"
        sample_context.design = "design"
        sample_context.failure_reports = ["error 1"]
        ctx_dict = sample_context.get_context_for_agent("developer")
        assert "failure_reports" in ctx_dict

    def test_empty_values_filtered(self, sample_context):
        ctx_dict = sample_context.get_context_for_agent("architect")
        # requirements is empty, should not be in dict
        assert "requirements" not in ctx_dict

    def test_to_dict(self, sample_context):
        d = sample_context.to_dict()
        assert d["problem_id"] == "HumanEval/0"
        assert isinstance(d["failure_reports"], list)

    def test_from_dict(self):
        data = {"problem": "test", "code": "def f(): pass", "failure_reports": ["err"]}
        ctx = SharedContext.from_dict(data)
        assert ctx.problem == "test"
        assert ctx.code == "def f(): pass"
        assert ctx.failure_reports == ["err"]

    def test_save_and_load(self, sample_context):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            sample_context.save(f.name)
            loaded = SharedContext.load(f.name)
            assert loaded.problem_id == sample_context.problem_id
