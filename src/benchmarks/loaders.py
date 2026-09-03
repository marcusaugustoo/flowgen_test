"""
Benchmark loaders and utilities.

Factory for creating benchmark instances from configuration.
"""

from __future__ import annotations

from typing import Optional

from src.benchmarks.base import BaseBenchmark
from src.benchmarks.humaneval import HumanEvalBenchmark
from src.config import ExperimentConfig


# Registry of available benchmarks
_BENCHMARK_REGISTRY: dict[str, type[BaseBenchmark]] = {
    "humaneval": HumanEvalBenchmark,
}


def create_benchmark(config: ExperimentConfig) -> BaseBenchmark:
    """
    Create a benchmark from configuration.

    Args:
        config: Experiment configuration.

    Returns:
        Configured benchmark instance.

    Raises:
        ValueError: If the benchmark name is not registered.
    """
    name = config.benchmark.name.lower()

    if name not in _BENCHMARK_REGISTRY:
        available = ", ".join(_BENCHMARK_REGISTRY.keys())
        raise ValueError(
            f"Unknown benchmark '{name}'. Available: {available}"
        )

    benchmark_class = _BENCHMARK_REGISTRY[name]

    kwargs = {}
    if config.benchmark.dataset_path:
        kwargs["dataset_path"] = config.benchmark.dataset_path

    return benchmark_class(**kwargs)


def register_benchmark(name: str, benchmark_class: type[BaseBenchmark]) -> None:
    """Register a new benchmark type."""
    _BENCHMARK_REGISTRY[name] = benchmark_class
