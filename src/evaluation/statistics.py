"""
Statistical analysis for experiment results.

Computes mean, standard deviation, and aggregations across runs.
"""

from __future__ import annotations

import math
from typing import Any


def compute_mean(values: list[float]) -> float:
    """Compute arithmetic mean."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def compute_std(values: list[float]) -> float:
    """Compute sample standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = compute_mean(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def compute_confidence_interval(
    values: list[float],
    confidence: float = 0.95,
) -> tuple[float, float]:
    """
    Compute confidence interval using t-distribution approximation.

    Args:
        values: List of measurements.
        confidence: Confidence level (default 0.95 for 95% CI).

    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    if len(values) < 2:
        mean = compute_mean(values)
        return (mean, mean)

    mean = compute_mean(values)
    std = compute_std(values)
    n = len(values)

    # Approximate t-value for 95% CI (good enough for n >= 5)
    # For more precise values, use scipy.stats.t.ppf
    t_values = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    t_val = t_values.get(confidence, 1.96)

    margin = t_val * (std / math.sqrt(n))
    return (mean - margin, mean + margin)


def aggregate_results(
    run_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Aggregate results across multiple runs.

    Args:
        run_results: List of result dicts from individual runs.
            Each should contain 'pass_at_1' and optionally 'total_time_ms',
            'total_tokens', 'llm_calls'.

    Returns:
        Aggregated statistics dict.
    """
    if not run_results:
        return {"mean_pass_at_1": 0.0, "std_pass_at_1": 0.0, "runs": 0}

    pass_scores = [r.get("pass_at_1", 0.0) for r in run_results]

    agg = {
        "runs": len(run_results),
        "mean_pass_at_1": compute_mean(pass_scores),
        "std_pass_at_1": compute_std(pass_scores),
        "min_pass_at_1": min(pass_scores),
        "max_pass_at_1": max(pass_scores),
    }

    if len(pass_scores) >= 2:
        ci_low, ci_high = compute_confidence_interval(pass_scores)
        agg["ci_95_lower"] = ci_low
        agg["ci_95_upper"] = ci_high

    # Aggregate timing if available
    times = [r.get("total_time_ms", 0) for r in run_results if "total_time_ms" in r]
    if times:
        agg["mean_time_ms"] = compute_mean(times)
        agg["std_time_ms"] = compute_std(times)

    # Aggregate token usage if available
    tokens = [r.get("total_tokens", 0) for r in run_results if "total_tokens" in r]
    if tokens:
        agg["mean_tokens"] = compute_mean(tokens)
        agg["total_tokens"] = sum(tokens)

    # Aggregate LLM calls if available
    calls = [r.get("llm_calls", 0) for r in run_results if "llm_calls" in r]
    if calls:
        agg["mean_llm_calls"] = compute_mean(calls)
        agg["total_llm_calls"] = sum(calls)

    return agg
