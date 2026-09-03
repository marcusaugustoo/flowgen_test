"""
Execution metrics tracking.

Records cost and performance metrics for each experiment run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionMetrics:
    """
    Tracks execution metrics for an experiment run.

    Attributes:
        llm_calls: Total number of LLM API calls.
        total_time_ms: Total execution time in milliseconds.
        tokens_in: Total input tokens (when available).
        tokens_out: Total output tokens (when available).
        agents_executed: Number of agent executions.
        refinement_count: Number of refinement iterations performed.
        evaluation_time_ms: Time spent on evaluation.
    """
    llm_calls: int = 0
    total_time_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    agents_executed: int = 0
    refinement_count: int = 0
    evaluation_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "llm_calls": self.llm_calls,
            "total_time_ms": self.total_time_ms,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "total_tokens": self.tokens_in + self.tokens_out,
            "agents_executed": self.agents_executed,
            "refinement_count": self.refinement_count,
            "evaluation_time_ms": self.evaluation_time_ms,
        }

    def update_from_llm_metrics(self, llm_metrics: dict[str, Any]) -> None:
        """Update metrics from LLM provider metrics."""
        self.llm_calls = llm_metrics.get("call_count", 0)
        self.tokens_in = llm_metrics.get("prompt_tokens", 0)
        self.tokens_out = llm_metrics.get("completion_tokens", 0)
        self.total_time_ms = llm_metrics.get("total_latency_ms", 0.0)
