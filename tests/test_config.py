"""Tests for the configuration system."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.config import ExperimentConfig, deep_merge


class TestDeepMerge:
    """Tests for deep_merge function."""

    def test_simple_merge(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 99, "z": 100}}
        result = deep_merge(base, override)
        assert result == {"a": {"x": 1, "y": 99, "z": 100}, "b": 3}

    def test_does_not_mutate_base(self):
        base = {"a": {"x": 1}}
        override = {"a": {"x": 2}}
        deep_merge(base, override)
        assert base["a"]["x"] == 1


class TestExperimentConfig:
    """Tests for ExperimentConfig."""

    def test_default_loading(self):
        config = ExperimentConfig.load()
        assert config.name == "flowgen_baseline"
        assert config.llm.provider == "ollama"
        assert config.llm.temperature == 0.8
        assert config.pipeline.type == "waterfall"

    def test_override_values(self):
        config = ExperimentConfig.load(
            overrides={
                "experiment": {"name": "test", "runs": 5},
                "llm": {"model": "test-model"},
                "pipeline": {"type": "raw"},
            }
        )
        assert config.name == "test"
        assert config.runs == 5
        assert config.llm.model == "test-model"
        assert config.pipeline.type == "raw"

    def test_load_experiment_yaml(self):
        config = ExperimentConfig.load(
            config_path="config/experiments/raw_baseline.yaml"
        )
        assert config.name == "raw_baseline"
        assert config.pipeline.type == "raw"
        assert config.refinement.enabled is False

    def test_to_dict_and_back(self):
        config = ExperimentConfig.load()
        d = config.to_dict()
        config2 = ExperimentConfig.from_dict(d)
        assert config.name == config2.name
        assert config.llm.model == config2.llm.model
        assert config.pipeline.type == config2.pipeline.type

    def test_save_and_load(self):
        config = ExperimentConfig.load(
            overrides={"experiment": {"name": "save_test"}}
        )
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            config.save(f.name)
            loaded = yaml.safe_load(open(f.name))
            assert loaded["experiment"]["name"] == "save_test"

    def test_agents_config(self):
        config = ExperimentConfig.load()
        assert config.agents.requirement_engineer is True
        assert config.agents.scrum_master is False

    def test_refinement_config(self):
        config = ExperimentConfig.load()
        assert config.refinement.enabled is True
        assert config.refinement.iterations == 3
