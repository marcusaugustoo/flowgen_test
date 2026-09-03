"""
Mock LLM provider for testing.

Returns deterministic or scripted responses without calling any real LLM.
Essential for testing the full pipeline infrastructure without Ollama.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any, Optional

from src.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM provider for testing infrastructure without a real model.

    Supports:
    - Default response: returns the same response for every call.
    - Response queue: returns scripted responses in order.
    - Custom response function: dynamic responses based on prompt.
    - Call recording: stores all prompts for assertions.
    """

    def __init__(
        self,
        model: str = "mock-model",
        temperature: float = 0.8,
        default_response: str = "Mock LLM response.",
        response_queue: Optional[list[str]] = None,
        response_fn: Optional[Any] = None,  # Callable[[str], str]
        latency_ms: float = 10.0,
        **kwargs: Any,
    ):
        super().__init__(model=model, temperature=temperature, **kwargs)
        self.default_response = default_response
        self._response_queue: deque[str] = deque(response_queue or [])
        self._response_fn = response_fn
        self._simulated_latency_ms = latency_ms

        # Record all calls for test assertions
        self.call_history: list[dict[str, Any]] = []

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        Return a mock response.

        Priority:
        1. response_fn (if set)
        2. Next item from response_queue (if non-empty)
        3. default_response

        Args:
            prompt: The prompt text (recorded but not sent to any model).

        Returns:
            LLMResponse with mock content.
        """
        start_time = time.perf_counter()

        # Determine response content
        if self._response_fn is not None:
            content = self._response_fn(prompt)
        elif self._response_queue:
            content = self._response_queue.popleft()
        else:
            content = self.default_response

        elapsed_ms = (time.perf_counter() - start_time) * 1000 + self._simulated_latency_ms

        # Estimate tokens (rough: 1 token ≈ 4 chars)
        prompt_tokens = len(prompt) // 4
        completion_tokens = len(content) // 4
        total_tokens = prompt_tokens + completion_tokens

        response = LLMResponse(
            content=content,
            model=self.model,
            latency_ms=elapsed_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            raw_response={"mock": True},
        )

        # Record the call
        self.call_history.append({
            "prompt": prompt,
            "response": content,
            "kwargs": kwargs,
        })

        self._record_metrics(response)

        logger.debug("MockLLM call #%d: prompt_len=%d", self._call_count, len(prompt))

        return response

    def add_response(self, response: str) -> None:
        """Add a response to the queue."""
        self._response_queue.append(response)

    def add_responses(self, responses: list[str]) -> None:
        """Add multiple responses to the queue."""
        self._response_queue.extend(responses)

    def reset(self) -> None:
        """Clear call history and response queue."""
        self.call_history.clear()
        self._response_queue.clear()
        self.reset_metrics()

    def get_last_prompt(self) -> Optional[str]:
        """Get the most recent prompt sent to this mock."""
        if self.call_history:
            return self.call_history[-1]["prompt"]
        return None
