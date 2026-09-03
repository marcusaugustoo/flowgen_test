"""Tests for the test executor."""

import pytest

from src.evaluation.test_executor import TestExecutor


class TestTestExecutor:
    """Tests for TestExecutor."""

    def test_passing_code(self):
        executor = TestExecutor(timeout=10)
        result = executor.run(
            code="def add(a, b): return a + b",
            tests="assert add(1, 2) == 3\nassert add(0, 0) == 0\n",
        )
        assert result["passed"] is True
        assert result["return_code"] == 0
        assert result["error"] is None

    def test_failing_code(self):
        executor = TestExecutor(timeout=10)
        result = executor.run(
            code="def add(a, b): return a - b",
            tests="assert add(1, 2) == 3\n",
        )
        assert result["passed"] is False
        assert result["return_code"] != 0

    def test_syntax_error(self):
        executor = TestExecutor(timeout=10)
        result = executor.run(
            code="def add(a, b) return a + b",  # Missing colon
            tests="assert add(1, 2) == 3\n",
        )
        assert result["passed"] is False

    def test_timeout(self):
        executor = TestExecutor(timeout=2)
        result = executor.run(
            code="import time\ndef slow(): time.sleep(10)\n",
            tests="slow()\n",
        )
        assert result["passed"] is False
        assert result["timeout"] is True

    def test_canonical_tests(self, sample_problem):
        """Test with HumanEval canonical test format."""
        executor = TestExecutor(timeout=10)
        code = (
            "from typing import List\n"
            "def has_close_elements(numbers: List[float], threshold: float) -> bool:\n"
            "    for i in range(len(numbers)):\n"
            "        for j in range(i + 1, len(numbers)):\n"
            "            if abs(numbers[i] - numbers[j]) < threshold:\n"
            "                return True\n"
            "    return False\n"
        )
        result = executor.run_with_canonical_tests(
            code=code,
            test=sample_problem.test,
            entry_point=sample_problem.entry_point,
        )
        assert result["passed"] is True

    def test_empty_code(self):
        executor = TestExecutor(timeout=10)
        result = executor.run(code="", tests="print('no code')\n")
        # Empty code but print doesn't fail
        assert result["passed"] is True
