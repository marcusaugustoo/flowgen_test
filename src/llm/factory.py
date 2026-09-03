"""
LLM provider factory.

Creates the appropriate LLM provider based on configuration.
"""

from __future__ import annotations

from typing import Any

from src.config import ExperimentConfig, LLMConfig
from src.llm.base import BaseLLMProvider
from src.llm.mock_provider import MockLLMProvider
from src.llm.ollama_provider import OllamaProvider


# Registry of available providers
_PROVIDERS: dict[str, type[BaseLLMProvider]] = {
    "ollama": OllamaProvider,
    "mock": MockLLMProvider,
}


def register_provider(name: str, provider_class: type[BaseLLMProvider]) -> None:
    """Register a new LLM provider type."""
    _PROVIDERS[name] = provider_class


def create_llm_provider(
    config: ExperimentConfig | LLMConfig | dict[str, Any],
    **kwargs: Any,
) -> BaseLLMProvider:
    """
    Create an LLM provider from configuration.

    Args:
        config: ExperimentConfig, LLMConfig, or dict with llm settings.
        **kwargs: Additional keyword arguments passed to the provider.

    Returns:
        Configured BaseLLMProvider instance.

    Raises:
        ValueError: If the provider type is not registered.
    """
    if isinstance(config, ExperimentConfig):
        llm_config = config.llm
    elif isinstance(config, LLMConfig):
        llm_config = config
    elif isinstance(config, dict):
        llm_config = LLMConfig(**config.get("llm", config))
    else:
        raise TypeError(f"Unsupported config type: {type(config)}")

    provider_name = llm_config.provider.lower()

    if provider_name not in _PROVIDERS:
        available = ", ".join(_PROVIDERS.keys())
        raise ValueError(
            f"Unknown LLM provider '{provider_name}'. Available: {available}"
        )

    provider_class = _PROVIDERS[provider_name]

    # Build kwargs for the provider constructor
    provider_kwargs: dict[str, Any] = {
        "model": llm_config.model,
        "temperature": llm_config.temperature,
        **kwargs,
    }

    # Add provider-specific kwargs
    if provider_name == "ollama":
        provider_kwargs["base_url"] = llm_config.base_url
        provider_kwargs["timeout"] = llm_config.timeout
        provider_kwargs["max_retries"] = llm_config.max_retries

    return provider_class(**provider_kwargs)
