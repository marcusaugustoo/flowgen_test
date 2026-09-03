"""
Ollama LLM provider.

Communicates with a local Ollama instance via REST API.
Uses the /api/generate endpoint for text generation.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

import requests

from src.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    LLM provider for Ollama local models.

    Uses the Ollama REST API (http://localhost:11434/api/generate by default).
    The model must be pulled locally before use (e.g., `ollama pull qwen2.5-coder:7b`).
    """

    def __init__(
        self,
        model: str = "qwen2.5-coder:7b",
        temperature: float = 0.8,
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        max_retries: int = 2,
        **kwargs: Any,
    ):
        super().__init__(model=model, temperature=temperature, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        Generate a response from the Ollama model.

        Args:
            prompt: The full prompt text.
            **kwargs: Additional Ollama-specific options (e.g., num_predict, top_p).

        Returns:
            LLMResponse with content and metadata.

        Raises:
            ConnectionError: If Ollama is not reachable.
            RuntimeError: If the API returns an error after retries.
        """
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
            },
        }

        # Add any extra options
        for key in ("num_predict", "top_p", "top_k", "seed"):
            if key in kwargs:
                payload["options"][key] = kwargs[key]

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.perf_counter()
                resp = requests.post(url, json=payload, timeout=self.timeout)
                elapsed_ms = (time.perf_counter() - start_time) * 1000

                if resp.status_code != 200:
                    raise RuntimeError(
                        f"Ollama API error (HTTP {resp.status_code}): {resp.text}"
                    )

                data = resp.json()
                content = data.get("response", "")

                # Ollama provides token counts in some versions
                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                total_tokens = prompt_tokens + completion_tokens

                response = LLMResponse(
                    content=content,
                    model=self.model,
                    latency_ms=elapsed_ms,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    raw_response=data,
                )

                self._record_metrics(response)

                logger.debug(
                    "Ollama call: model=%s, latency=%.1fms, tokens=%d",
                    self.model,
                    elapsed_ms,
                    total_tokens,
                )

                return response

            except requests.ConnectionError as e:
                last_error = ConnectionError(
                    f"Cannot connect to Ollama at {self.base_url}. "
                    f"Is Ollama running? (attempt {attempt + 1}/{self.max_retries + 1})"
                )
                logger.warning(str(last_error))
            except requests.Timeout as e:
                last_error = RuntimeError(
                    f"Ollama request timed out after {self.timeout}s "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
                logger.warning(str(last_error))
            except Exception as e:
                last_error = e
                logger.warning(
                    "Ollama call failed (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    str(e),
                )

        raise last_error  # type: ignore[misc]

    def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                available = [m.get("name", "") for m in models]
                return any(self.model in name for name in available)
            return False
        except Exception:
            return False
