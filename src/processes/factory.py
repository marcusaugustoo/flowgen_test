"""
Process model factory.

Creates process instances from configuration.
"""

from __future__ import annotations

from typing import Any

from src.config import ExperimentConfig
from src.llm.base import BaseLLMProvider
from src.processes.base import BaseProcess


# Registry of available process models
_PROCESS_REGISTRY: dict[str, str] = {
    "raw": "src.processes.raw.RawProcess",
    "waterfall": "src.processes.waterfall.WaterfallProcess",
    "tdd": "src.processes.tdd.TDDProcess",
    "scrum": "src.processes.scrum.ScrumProcess",
}


def _import_class(dotted_path: str) -> type:
    """Import a class from a dotted module path."""
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def create_process(
    config: ExperimentConfig,
    llm: BaseLLMProvider,
) -> BaseProcess:
    """
    Create a process model from configuration.

    Args:
        config: Experiment configuration.
        llm: LLM provider to inject into the process.

    Returns:
        Configured BaseProcess instance.

    Raises:
        ValueError: If the process type is not registered.
    """
    process_type = config.pipeline.type.lower()

    if process_type not in _PROCESS_REGISTRY:
        available = ", ".join(_PROCESS_REGISTRY.keys())
        raise ValueError(
            f"Unknown process type '{process_type}'. Available: {available}"
        )

    process_class = _import_class(_PROCESS_REGISTRY[process_type])
    return process_class(config=config, llm=llm)


def register_process(name: str, dotted_path: str) -> None:
    """Register a new process model type."""
    _PROCESS_REGISTRY[name] = dotted_path


def available_processes() -> list[str]:
    """List all registered process model names."""
    return list(_PROCESS_REGISTRY.keys())
