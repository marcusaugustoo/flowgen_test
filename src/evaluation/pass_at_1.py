"""
Pass@1 metric computation.

Pass@1: probability that a single generated code sample passes all tests.
This is the primary evaluation metric used in the FlowGen paper.
"""

from __future__ import annotations

from typing import Any


def compute_pass_at_1(results: list[dict[str, Any]]) -> float:
    """
    Compute Pass@1 score.

    Pass@1 = (number of problems passed on first attempt) / (total problems)

    Args:
        results: List of result dicts, each with a 'passed' boolean key.

    Returns:
        Pass@1 score as a float between 0.0 and 1.0.

    Raises:
        ValueError: If results is empty.
    """
    if not results:
        raise ValueError("Cannot compute Pass@1 on empty results")

    passed = sum(1 for r in results if r.get("passed", False))
    total = len(results)

    return passed / total


def compute_pass_at_k(
    results_per_problem: list[list[dict[str, Any]]],
    k: int = 1,
) -> float:
    """
    Compute Pass@k using the unbiased estimator.

    For each problem, given n total samples and c correct samples:
    pass@k = 1 - C(n-c, k) / C(n, k)

    When k=1, this simplifies to c/n per problem, averaged across problems.

    Args:
        results_per_problem: List of lists, where each inner list contains
            the results of multiple runs for a single problem.
        k: The k value for pass@k.

    Returns:
        Pass@k score as a float between 0.0 and 1.0.
    """
    if not results_per_problem:
        raise ValueError("Cannot compute Pass@k on empty results")

    scores = []
    for problem_results in results_per_problem:
        n = len(problem_results)
        c = sum(1 for r in problem_results if r.get("passed", False))

        if n < k:
            # Not enough samples
            scores.append(c / n if n > 0 else 0.0)
        elif n - c < k:
            # Enough correct samples to guarantee pass@k = 1
            scores.append(1.0)
        else:
            # Unbiased estimator: 1 - C(n-c, k) / C(n, k)
            score = 1.0 - _comb_ratio(n - c, n, k)
            scores.append(score)

    return sum(scores) / len(scores)


def _comb_ratio(a: int, b: int, k: int) -> float:
    """Compute C(a, k) / C(b, k) without overflow."""
    result = 1.0
    for i in range(k):
        result *= (a - i) / (b - i)
    return result
