"""
Centralized experiment configuration system.

Loads default.yaml and merges with experiment-specific overrides.
All experimental parameters are accessed through ExperimentConfig.
"""

from __future__ import annotations

import copy
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


# Project root: two levels up from src/config.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "default.yaml"


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base dict. Override values take precedence."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str = "ollama"
    model: str = "qwen2.5-coder:7b"
    temperature: float = 0.8
    base_url: str = "http://localhost:11434"
    timeout: int = 120
    max_retries: int = 2


@dataclass
class BenchmarkConfig:
    """Benchmark dataset configuration."""
    name: str = "humaneval"
    dataset_path: Optional[str] = None
    subset: Optional[list[int]] = None


@dataclass
class PipelineConfig:
    """Process model configuration."""
    type: str = "waterfall"


@dataclass
class AgentsConfig:
    """Agent enablement flags."""
    requirement_engineer: bool = True
    architect: bool = True
    developer: bool = True
    tester: bool = True
    scrum_master: bool = False


@dataclass
class RefinementConfig:
    """Self-refinement configuration."""
    enabled: bool = True
    iterations: int = 3


@dataclass
class EvaluationConfig:
    """Evaluation parameters."""
    timeout: int = 30
    pass_k: int = 1


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    log_prompts: bool = True
    log_dir: str = "logs"


@dataclass
class TasksConfig:
    """Tasks configuration for .txt file loading."""
    path: Optional[str] = None  # Path to a .txt file or directory of .txt files


@dataclass
class ResultsConfig:
    """Results storage configuration."""
    output_dir: str = "results"


@dataclass
class ExperimentConfig:
    """
    Central experiment configuration.

    Loads from default.yaml and merges with experiment-specific overrides.
    All experimental parameters are accessed through this dataclass.
    """
    name: str = "flowgen_baseline"
    seed: Optional[int] = None
    runs: int = 1

    llm: LLMConfig = field(default_factory=LLMConfig)
    benchmark: BenchmarkConfig = field(default_factory=BenchmarkConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    agents: AgentsConfig = field(default_factory=AgentsConfig)
    refinement: RefinementConfig = field(default_factory=RefinementConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    results: ResultsConfig = field(default_factory=ResultsConfig)
    tasks: TasksConfig = field(default_factory=TasksConfig)

    # Raw dict for any extra keys
    _raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> ExperimentConfig:
        """Create ExperimentConfig from a flat dictionary (merged YAML)."""
        experiment = data.get("experiment", {})
        config = cls(
            name=experiment.get("name", "flowgen_baseline"),
            seed=experiment.get("seed"),
            runs=experiment.get("runs", 1),
            llm=LLMConfig(**{k: v for k, v in data.get("llm", {}).items()}),
            benchmark=BenchmarkConfig(**{k: v for k, v in data.get("benchmark", {}).items()}),
            pipeline=PipelineConfig(**{k: v for k, v in data.get("pipeline", {}).items()}),
            agents=AgentsConfig(**{k: v for k, v in data.get("agents", {}).items()}),
            refinement=RefinementConfig(
                **{k: v for k, v in data.get("self_refinement", data.get("refinement", {})).items()}
            ),
            evaluation=EvaluationConfig(**{k: v for k, v in data.get("evaluation", {}).items()}),
            logging=LoggingConfig(**{k: v for k, v in data.get("logging", {}).items()}),
            results=ResultsConfig(**{k: v for k, v in data.get("results", {}).items()}),
            tasks=TasksConfig(**{k: v for k, v in data.get("tasks", {}).items()}),
            _raw=data,
        )
        return config

    @classmethod
    def load(
        cls,
        config_path: Optional[str | Path] = None,
        overrides: Optional[dict] = None,
    ) -> ExperimentConfig:
        """
        Load configuration from YAML files.

        1. Loads default.yaml
        2. Merges with experiment-specific config if provided
        3. Applies any programmatic overrides

        Args:
            config_path: Path to experiment-specific YAML (optional).
            overrides: Dict of programmatic overrides (optional).

        Returns:
            Fully merged ExperimentConfig.
        """
        # Load defaults
        if DEFAULT_CONFIG_PATH.exists():
            with open(DEFAULT_CONFIG_PATH, "r") as f:
                base = yaml.safe_load(f) or {}
        else:
            base = {}

        # Merge experiment-specific config
        if config_path is not None:
            config_path = Path(config_path)
            if not config_path.is_absolute():
                config_path = PROJECT_ROOT / config_path
            with open(config_path, "r") as f:
                experiment_data = yaml.safe_load(f) or {}
            base = deep_merge(base, experiment_data)

        # Apply programmatic overrides
        if overrides:
            base = deep_merge(base, overrides)

        return cls.from_dict(base)

    def to_dict(self) -> dict:
        """Serialize config back to a plain dict for persistence."""
        return {
            "experiment": {
                "name": self.name,
                "seed": self.seed,
                "runs": self.runs,
            },
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "temperature": self.llm.temperature,
                "base_url": self.llm.base_url,
                "timeout": self.llm.timeout,
                "max_retries": self.llm.max_retries,
            },
            "benchmark": {
                "name": self.benchmark.name,
                "dataset_path": self.benchmark.dataset_path,
                "subset": self.benchmark.subset,
            },
            "pipeline": {
                "type": self.pipeline.type,
            },
            "agents": {
                "requirement_engineer": self.agents.requirement_engineer,
                "architect": self.agents.architect,
                "developer": self.agents.developer,
                "tester": self.agents.tester,
                "scrum_master": self.agents.scrum_master,
            },
            "self_refinement": {
                "enabled": self.refinement.enabled,
                "iterations": self.refinement.iterations,
            },
            "evaluation": {
                "timeout": self.evaluation.timeout,
                "pass_k": self.evaluation.pass_k,
            },
            "logging": {
                "level": self.logging.level,
                "log_prompts": self.logging.log_prompts,
                "log_dir": self.logging.log_dir,
            },
            "results": {
                "output_dir": self.results.output_dir,
            },
            "tasks": {
                "path": self.tasks.path,
            },
        }

    def save(self, path: str | Path) -> None:
        """Save current config to YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
