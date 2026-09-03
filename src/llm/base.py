"""
Base LLM provider abstraction.

All LLM providers must inherit from BaseLLMProvider.
This ensures that agents are completely decoupled from specific LLM implementations.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LLMResponse:
    """
    Standardized response from any LLM provider.

    Attributes:
        content: The generated text response.
        model: Name of the model used.
        latency_ms: Time taken for the LLM call in milliseconds.
        prompt_tokens: Number of input tokens (when available).
        completion_tokens: Number of output tokens (when available).
        total_tokens: Total tokens used (when available).
        raw_response: Full raw response from the provider for debugging.
    """
    content: str
    model: str
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    raw_response: Optional[dict[str, Any]] = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for logging/persistence."""
        return {
            "content": self.content,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement the `generate` method.
    The provider handles model-specific API details internally.
    """

    def __init__(self, model: str, temperature: float = 0.8, **kwargs: Any):
        self.model = model
        self.temperature = temperature
        self._call_count = 0
        self._total_tokens = 0
        self._total_latency_ms = 0.0

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            prompt: The full prompt text to send to the model.
            **kwargs: Provider-specific parameters.

        Returns:
            LLMResponse with the generated content and metadata.
        """
        ...

    def _record_metrics(self, response: LLMResponse) -> None:
        """Track cumulative metrics across calls."""
        self._call_count += 1
        self._total_tokens += response.total_tokens
        self._total_latency_ms += response.latency_ms

    @property
    def call_count(self) -> int:
        """Total number of LLM calls made."""
        return self._call_count

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed across all calls."""
        return self._total_tokens

    @property
    def total_latency_ms(self) -> float:
        """Total latency across all calls in milliseconds."""
        return self._total_latency_ms

    def reset_metrics(self) -> None:
        """Reset cumulative metrics (useful between experiment runs)."""
        self._call_count = 0
        self._total_tokens = 0
        self._total_latency_ms = 0.0

    def get_metrics(self) -> dict[str, Any]:
        """Get current cumulative metrics."""
        return {
            "call_count": self._call_count,
            "total_tokens": self._total_tokens,
            "total_latency_ms": self._total_latency_ms,
            "model": self.model,
            "temperature": self.temperature,
        }
