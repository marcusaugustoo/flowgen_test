"""Tests for the evaluator and Pass@1 computation."""

import pytest

from src.evaluation.pass_at_1 import compute_pass_at_1, compute_pass_at_k
from src.evaluation.evaluator import Evaluator
from src.evaluation.statistics import compute_mean, compute_std, aggregate_results


class TestPassAt1:
    """Tests for Pass@1 computation."""

    def test_all_pass(self):
        results = [{"passed": True}, {"passed": True}, {"passed": True}]
        assert compute_pass_at_1(results) == 1.0

    def test_none_pass(self):
        results = [{"passed": False}, {"passed": False}]
        assert compute_pass_at_1(results) == 0.0

    def test_partial_pass(self):
        results = [{"passed": True}, {"passed": False}, {"passed": True}, {"passed": False}]
        assert compute_pass_at_1(results) == 0.5

    def test_single_pass(self):
        assert compute_pass_at_1([{"passed": True}]) == 1.0

    def test_single_fail(self):
        assert compute_pass_at_1([{"passed": False}]) == 0.0

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            compute_pass_at_1([])


class TestPassAtK:
    """Tests for Pass@k computation."""

    def test_pass_at_1_equivalence(self):
        """Pass@1 with single samples should match compute_pass_at_1."""
        results = [[{"passed": True}], [{"passed": False}], [{"passed": True}]]
        score = compute_pass_at_k(results, k=1)
        assert abs(score - 2 / 3) < 1e-6

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            compute_pass_at_k([], k=1)


class TestStatistics:
    """Tests for statistical functions."""

    def test_mean(self):
        assert compute_mean([1.0, 2.0, 3.0]) == 2.0
        assert compute_mean([]) == 0.0

    def test_std(self):
        std = compute_std([1.0, 2.0, 3.0])
        assert abs(std - 1.0) < 1e-6
        assert compute_std([]) == 0.0
        assert compute_std([5.0]) == 0.0

    def test_aggregate_results(self):
        run_results = [
            {"pass_at_1": 0.5, "total_time_ms": 1000, "llm_calls": 4},
            {"pass_at_1": 0.6, "total_time_ms": 1200, "llm_calls": 4},
            {"pass_at_1": 0.7, "total_time_ms": 1100, "llm_calls": 4},
        ]
        agg = aggregate_results(run_results)
        assert agg["runs"] == 3
        assert abs(agg["mean_pass_at_1"] - 0.6) < 1e-6
        assert agg["min_pass_at_1"] == 0.5
        assert agg["max_pass_at_1"] == 0.7
        assert agg["total_llm_calls"] == 12


class TestEvaluator:
    """Tests for the Evaluator."""

    def test_evaluate_single_passing(self, sample_problem):
        evaluator = Evaluator(timeout=10)
        code = (
            "from typing import List\n"
            "def has_close_elements(numbers: List[float], threshold: float) -> bool:\n"
            "    for i in range(len(numbers)):\n"
            "        for j in range(i + 1, len(numbers)):\n"
            "            if abs(numbers[i] - numbers[j]) < threshold:\n"
            "                return True\n"
            "    return False\n"
        )
        result = evaluator.evaluate_single(code, sample_problem)
        assert result["passed"] is True
        assert result["task_id"] == "HumanEval/0"

    def test_evaluate_single_failing(self, sample_problem):
        evaluator = Evaluator(timeout=10)
        code = "def has_close_elements(numbers, threshold): return False\n"
        result = evaluator.evaluate_single(code, sample_problem)
        assert result["passed"] is False

    def test_evaluate_batch(self, sample_problem):
        evaluator = Evaluator(timeout=10)
        code = (
            "from typing import List\n"
            "def has_close_elements(numbers: List[float], threshold: float) -> bool:\n"
            "    for i in range(len(numbers)):\n"
            "        for j in range(i + 1, len(numbers)):\n"
            "            if abs(numbers[i] - numbers[j]) < threshold:\n"
            "                return True\n"
            "    return False\n"
        )
        code_results = [{"task_id": "HumanEval/0", "code": code}]
        batch_result = evaluator.evaluate_batch(code_results, [sample_problem])
        assert batch_result["pass_at_1"] == 1.0
        assert batch_result["passed"] == 1
