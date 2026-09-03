"""
Agent factory.

Creates agent instances from configuration.
"""

from __future__ import annotations

from typing import Any

from src.agents.base_agent import BaseAgent
from src.llm.base import BaseLLMProvider


# Lazy imports to avoid circular dependencies
_AGENT_REGISTRY: dict[str, str] = {
    "requirement_engineer": "src.agents.requirement_engineer.RequirementEngineer",
    "architect": "src.agents.architect.Architect",
    "developer": "src.agents.developer.Developer",
    "tester": "src.agents.tester.Tester",
    "scrum_master": "src.agents.scrum_master.ScrumMaster",
}


def _import_class(dotted_path: str) -> type:
    """Import a class from a dotted module path."""
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def create_agent(name: str, llm: BaseLLMProvider, **kwargs: Any) -> BaseAgent:
    """
    Create an agent instance by name.

    Args:
        name: Agent name (e.g., 'developer', 'tester').
        llm: LLM provider to inject.
        **kwargs: Additional keyword arguments for the agent.

    Returns:
        Configured BaseAgent instance.

    Raises:
        ValueError: If the agent name is not registered.
    """
    if name not in _AGENT_REGISTRY:
        available = ", ".join(_AGENT_REGISTRY.keys())
        raise ValueError(f"Unknown agent '{name}'. Available: {available}")

    agent_class = _import_class(_AGENT_REGISTRY[name])
    return agent_class(llm=llm, **kwargs)


def register_agent(name: str, dotted_path: str) -> None:
    """Register a new agent type for future extensibility."""
    _AGENT_REGISTRY[name] = dotted_path


def available_agents() -> list[str]:
    """List all registered agent names."""
    return list(_AGENT_REGISTRY.keys())
