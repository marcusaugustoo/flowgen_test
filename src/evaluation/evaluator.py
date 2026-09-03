"""
Evaluator: orchestrates evaluation of generated code against benchmark tests.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.benchmarks.base import Problem
from src.evaluation.pass_at_1 import compute_pass_at_1
from src.evaluation.test_executor import TestExecutor

logger = logging.getLogger(__name__)


class Evaluator:
    """
    Evaluates generated code against benchmark tests.

    Uses TestExecutor for sandboxed execution and computes Pass@1.
    """

    def __init__(self, timeout: int = 30) -> None:
        self.test_executor = TestExecutor(timeout=timeout)

    def evaluate_single(
        self,
        code: str,
        problem: Problem,
    ) -> dict[str, Any]:
        """
        Evaluate a single generated code against a problem's tests.

        Args:
            code: The generated Python code.
            problem: The benchmark problem with tests.

        Returns:
            Result dict with 'passed', 'output', 'task_id', etc.
        """
        start_time = time.perf_counter()

        result = self.test_executor.run_with_canonical_tests(
            code=code,
            test=problem.test,
            entry_point=problem.entry_point,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        result["task_id"] = problem.task_id
        result["entry_point"] = problem.entry_point
        result["evaluation_time_ms"] = elapsed_ms
        result["prompt"] = problem.prompt

        logger.info(
            "Evaluated %s: passed=%s (%.1fms)",
            problem.task_id,
            result["passed"],
            elapsed_ms,
        )

        return result

    def evaluate_batch(
        self,
        code_results: list[dict[str, Any]],
        problems: list[Problem],
    ) -> dict[str, Any]:
        """
        Evaluate a batch of generated code against problems.

        Args:
            code_results: List of dicts with 'task_id' and 'code' keys.
            problems: List of Problem objects.

        Returns:
            Summary dict with individual results and Pass@1 score.
        """
        # Build problem lookup
        problem_map = {p.task_id: p for p in problems}

        results = []
        for cr in code_results:
            task_id = cr["task_id"]
            code = cr["code"]

            if task_id not in problem_map:
                logger.warning("Problem %s not found in benchmark", task_id)
                continue

            result = self.evaluate_single(code, problem_map[task_id])
            results.append(result)

        # Compute Pass@1
        pass_at_1 = compute_pass_at_1(results) if results else 0.0

        return {
            "results": results,
            "pass_at_1": pass_at_1,
            "total": len(results),
            "passed": sum(1 for r in results if r["passed"]),
            "failed": sum(1 for r in results if not r["passed"]),
        }
