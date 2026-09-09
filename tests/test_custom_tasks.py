"""
Tests for the custom task infrastructure.

Covers:
- CustomTaskLoader: loading, validation, error handling
- Evaluation: correct, incorrect, partial, syntax error, exception, timeout
- Integration: same evaluator for HumanEval and custom tasks
- Raw vs Waterfall: both use the same reference tests
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

from src.benchmarks.base import Problem
from src.benchmarks.custom import CustomBenchmark
from src.evaluation.evaluator import Evaluator
from src.evaluation.pass_at_1 import compute_pass_at_1
from src.tasks.custom_task_loader import CustomTaskLoader


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def custom_loader():
    """Create a CustomTaskLoader instance."""
    return CustomTaskLoader()


@pytest.fixture
def valid_task_dir(tmp_path):
    """Create a valid custom task directory."""
    task_dir = tmp_path / "task_test"
    task_dir.mkdir()

    (task_dir / "task.txt").write_text(
        "Implemente uma função chamada add(a, b) que retorne a soma de a e b.",
        encoding="utf-8",
    )
    (task_dir / "metadata.json").write_text(
        json.dumps({"task_id": "Custom/Test", "entry_point": "add"}),
        encoding="utf-8",
    )
    (task_dir / "tests.py").write_text(
        "def check(candidate):\n"
        "    assert candidate(1, 2) == 3\n"
        "    assert candidate(0, 0) == 0\n"
        "    assert candidate(-1, 1) == 0\n"
        "\ncheck(add)\n",
        encoding="utf-8",
    )
    return task_dir


@pytest.fixture
def custom_tasks_root(tmp_path):
    """Create a root directory with multiple valid custom tasks."""
    root = tmp_path / "custom"
    root.mkdir()

    for i, (name, entry, test_body) in enumerate([
        ("add", "add",
         "    assert candidate(1, 2) == 3\n"
         "    assert candidate(0, 0) == 0\n"),
        ("sub", "subtract",
         "    assert candidate(5, 3) == 2\n"
         "    assert candidate(0, 0) == 0\n"),
    ], start=1):
        task_dir = root / f"task_{i:03d}"
        task_dir.mkdir()

        (task_dir / "task.txt").write_text(
            f"Implement {name}.",
            encoding="utf-8",
        )
        (task_dir / "metadata.json").write_text(
            json.dumps({"task_id": f"Custom/{i:03d}", "entry_point": entry}),
            encoding="utf-8",
        )
        (task_dir / "tests.py").write_text(
            f"def check(candidate):\n{test_body}\ncheck({entry})\n",
            encoding="utf-8",
        )

    return root


@pytest.fixture
def sample_custom_problem():
    """A custom Problem with known correct/incorrect solutions."""
    return Problem(
        task_id="Custom/Test",
        prompt="Implemente uma função chamada add(a, b) que retorne a soma.",
        entry_point="add",
        test=(
            "def check(candidate):\n"
            "    assert candidate(1, 2) == 3\n"
            "    assert candidate(0, 0) == 0\n"
            "    assert candidate(-1, 1) == 0\n"
            "    assert candidate(100, 200) == 300\n"
            "\ncheck(add)\n"
        ),
        canonical_solution="",
    )


# ─── Test: CustomTaskLoader — Loading ────────────────────────────────────────


class TestCustomTaskLoaderLoading:
    """Tests for loading custom tasks."""

    def test_load_valid_task(self, custom_loader, valid_task_dir):
        """Load a valid custom task directory."""
        problem = custom_loader.load_task(valid_task_dir)

        assert problem.task_id == "Custom/Test"
        assert problem.entry_point == "add"
        assert "add" in problem.prompt or "soma" in problem.prompt
        assert "check(candidate)" in problem.test
        assert problem.canonical_solution == ""

    def test_load_directory(self, custom_loader, custom_tasks_root):
        """Load all tasks from a directory."""
        problems = custom_loader.load_directory(custom_tasks_root)

        assert len(problems) == 2
        assert problems[0].task_id == "Custom/001"
        assert problems[1].task_id == "Custom/002"

    def test_task_not_found(self, custom_loader, tmp_path):
        """FileNotFoundError when task directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            custom_loader.load_task(tmp_path / "nonexistent")

    def test_missing_task_txt(self, custom_loader, tmp_path):
        """FileNotFoundError when task.txt is missing."""
        task_dir = tmp_path / "task_bad"
        task_dir.mkdir()
        (task_dir / "metadata.json").write_text(
            json.dumps({"task_id": "X", "entry_point": "f"}),
            encoding="utf-8",
        )
        (task_dir / "tests.py").write_text("def check(c): pass", encoding="utf-8")

        with pytest.raises(FileNotFoundError, match="task.txt"):
            custom_loader.load_task(task_dir)

    def test_missing_tests_py(self, custom_loader, tmp_path):
        """FileNotFoundError when tests.py is missing."""
        task_dir = tmp_path / "task_bad"
        task_dir.mkdir()
        (task_dir / "task.txt").write_text("Do something.", encoding="utf-8")
        (task_dir / "metadata.json").write_text(
            json.dumps({"task_id": "X", "entry_point": "f"}),
            encoding="utf-8",
        )

        with pytest.raises(FileNotFoundError, match="tests.py"):
            custom_loader.load_task(task_dir)

    def test_missing_metadata(self, custom_loader, tmp_path):
        """FileNotFoundError when metadata.json is missing."""
        task_dir = tmp_path / "task_bad"
        task_dir.mkdir()
        (task_dir / "task.txt").write_text("Do something.", encoding="utf-8")
        (task_dir / "tests.py").write_text("def check(c): pass", encoding="utf-8")

        with pytest.raises(FileNotFoundError, match="metadata.json"):
            custom_loader.load_task(task_dir)

    def test_invalid_entry_point(self, custom_loader, tmp_path):
        """ValueError when entry_point is missing from metadata."""
        task_dir = tmp_path / "task_bad"
        task_dir.mkdir()
        (task_dir / "task.txt").write_text("Do something.", encoding="utf-8")
        (task_dir / "metadata.json").write_text(
            json.dumps({"task_id": "X"}),  # Missing entry_point
            encoding="utf-8",
        )
        (task_dir / "tests.py").write_text(
            "def check(c): pass\ncheck(f)\n", encoding="utf-8",
        )

        with pytest.raises(ValueError, match="entry_point"):
            custom_loader.load_task(task_dir)

    def test_missing_task_id(self, custom_loader, tmp_path):
        """ValueError when task_id is missing from metadata."""
        task_dir = tmp_path / "task_bad"
        task_dir.mkdir()
        (task_dir / "task.txt").write_text("Do something.", encoding="utf-8")
        (task_dir / "metadata.json").write_text(
            json.dumps({"entry_point": "f"}),  # Missing task_id
            encoding="utf-8",
        )
        (task_dir / "tests.py").write_text(
            "def check(c): pass\ncheck(f)\n", encoding="utf-8",
        )

        with pytest.raises(ValueError, match="task_id"):
            custom_loader.load_task(task_dir)

    def test_empty_task_txt(self, custom_loader, tmp_path):
        """ValueError when task.txt is empty."""
        task_dir = tmp_path / "task_bad"
        task_dir.mkdir()
        (task_dir / "task.txt").write_text("", encoding="utf-8")
        (task_dir / "metadata.json").write_text(
            json.dumps({"task_id": "X", "entry_point": "f"}),
            encoding="utf-8",
        )
        (task_dir / "tests.py").write_text(
            "def check(c): pass\ncheck(f)\n", encoding="utf-8",
        )

        with pytest.raises(ValueError, match="empty"):
            custom_loader.load_task(task_dir)


# ─── Test: Evaluation with HumanEval check_correctness ───────────────────────


class TestCustomTaskEvaluation:
    """Tests that custom tasks are evaluated by HumanEval's check_correctness."""

    def test_correct_solution(self, sample_custom_problem):
        """A correct solution passes all tests."""
        evaluator = Evaluator(timeout=10.0)
        code = "def add(a, b):\n    return a + b\n"
        result = evaluator.evaluate_single(code, sample_custom_problem)

        assert result["passed"] is True
        assert result["task_id"] == "Custom/Test"
        assert result["evaluation_status"] == "completed"

    def test_incorrect_solution(self, sample_custom_problem):
        """An incorrect solution fails."""
        evaluator = Evaluator(timeout=10.0)
        code = "def add(a, b):\n    return a - b\n"
        result = evaluator.evaluate_single(code, sample_custom_problem)

        assert result["passed"] is False

    def test_partial_pass_is_fail(self):
        """A solution that passes some but not all tests is FAIL (not partial)."""
        problem = Problem(
            task_id="Custom/Partial",
            prompt="Implement abs_val.",
            entry_point="abs_val",
            test=(
                "def check(candidate):\n"
                "    assert candidate(5) == 5\n"      # This would pass
                "    assert candidate(-5) == 5\n"     # This would fail
                "\ncheck(abs_val)\n"
            ),
        )
        evaluator = Evaluator(timeout=10.0)
        # This returns x unchanged — passes for positive, fails for negative
        code = "def abs_val(x):\n    return x\n"
        result = evaluator.evaluate_single(code, problem)

        assert result["passed"] is False

    def test_syntax_error(self, sample_custom_problem):
        """Code with syntax errors fails."""
        evaluator = Evaluator(timeout=10.0)
        code = "def add(a, b)\n    return a + b\n"  # Missing colon
        result = evaluator.evaluate_single(code, sample_custom_problem)

        assert result["passed"] is False

    def test_runtime_exception(self, sample_custom_problem):
        """Code that raises an exception fails."""
        evaluator = Evaluator(timeout=10.0)
        code = "def add(a, b):\n    raise ValueError('boom')\n"
        result = evaluator.evaluate_single(code, sample_custom_problem)

        assert result["passed"] is False

    def test_timeout(self):
        """Code that runs too long is timed out."""
        problem = Problem(
            task_id="Custom/Timeout",
            prompt="Implement slow_func.",
            entry_point="slow_func",
            test=(
                "def check(candidate):\n"
                "    assert candidate() == 42\n"
                "\ncheck(slow_func)\n"
            ),
        )
        evaluator = Evaluator(timeout=2.0)
        code = (
            "import time\n"
            "def slow_func():\n"
            "    time.sleep(10)\n"
            "    return 42\n"
        )
        result = evaluator.evaluate_single(code, problem)

        assert result["passed"] is False


# ─── Test: Same Evaluator for HumanEval and Custom ──────────────────────────


class TestSameEvaluator:
    """Verify that HumanEval tasks and custom tasks use the same evaluator."""

    def test_humaneval_task_passes(self, sample_problem):
        """A real HumanEval task evaluated by the refactored evaluator passes."""
        evaluator = Evaluator(timeout=10.0)
        code = (
            "    for i in range(len(numbers)):\n"
            "        for j in range(i + 1, len(numbers)):\n"
            "            if abs(numbers[i] - numbers[j]) < threshold:\n"
            "                return True\n"
            "    return False\n"
        )
        result = evaluator.evaluate_single(code, sample_problem)
        assert result["passed"] is True
        assert result["task_id"] == "HumanEval/0"

    def test_humaneval_task_fails(self, sample_problem):
        """A wrong HumanEval solution fails."""
        evaluator = Evaluator(timeout=10.0)
        code = "    return False\n"
        result = evaluator.evaluate_single(code, sample_problem)
        assert result["passed"] is False

    def test_custom_task_passes(self, sample_custom_problem):
        """A correct custom task solution passes."""
        evaluator = Evaluator(timeout=10.0)
        code = "def add(a, b):\n    return a + b\n"
        result = evaluator.evaluate_single(code, sample_custom_problem)
        assert result["passed"] is True

    def test_batch_mixed_tasks(self, sample_problem, sample_custom_problem):
        """Batch evaluation handles both HumanEval and custom tasks."""
        evaluator = Evaluator(timeout=10.0)

        he_code = (
            "    for i in range(len(numbers)):\n"
            "        for j in range(i + 1, len(numbers)):\n"
            "            if abs(numbers[i] - numbers[j]) < threshold:\n"
            "                return True\n"
            "    return False\n"
        )
        custom_code = "def add(a, b):\n    return a + b\n"

        code_results = [
            {"task_id": "HumanEval/0", "code": he_code},
            {"task_id": "Custom/Test", "code": custom_code},
        ]
        problems = [sample_problem, sample_custom_problem]

        batch_result = evaluator.evaluate_batch(code_results, problems)
        assert batch_result["pass_at_1"] == 1.0
        assert batch_result["passed"] == 2
        assert batch_result["total"] == 2


# ─── Test: Raw vs Waterfall Use Same Tests ───────────────────────────────────


class TestRawVsWaterfallSameTests:
    """Verify that Raw and Waterfall conditions use the exact same tests."""

    def test_same_tests_different_code(self, sample_custom_problem):
        """
        Two different code solutions evaluated against the same problem
        use exactly the same test suite (the reference tests from tests.py).
        """
        evaluator = Evaluator(timeout=10.0)

        # Simulate "Raw" output
        raw_code = "def add(a, b):\n    return a + b\n"
        raw_result = evaluator.evaluate_single(raw_code, sample_custom_problem)

        # Simulate "Waterfall" output (same correct solution)
        waterfall_code = (
            "def add(a, b):\n"
            "    \"\"\"Add two numbers.\"\"\"\n"
            "    result = a + b\n"
            "    return result\n"
        )
        waterfall_result = evaluator.evaluate_single(
            waterfall_code, sample_custom_problem,
        )

        # Both should pass against the SAME tests
        assert raw_result["passed"] is True
        assert waterfall_result["passed"] is True
        assert raw_result["task_id"] == waterfall_result["task_id"]

    def test_same_tests_one_fails(self, sample_custom_problem):
        """One condition passes, the other fails — same tests."""
        evaluator = Evaluator(timeout=10.0)

        correct_code = "def add(a, b):\n    return a + b\n"
        wrong_code = "def add(a, b):\n    return a * b\n"

        correct_result = evaluator.evaluate_single(correct_code, sample_custom_problem)
        wrong_result = evaluator.evaluate_single(wrong_code, sample_custom_problem)

        assert correct_result["passed"] is True
        assert wrong_result["passed"] is False


# ─── Test: CustomBenchmark ───────────────────────────────────────────────────


class TestCustomBenchmark:
    """Tests for the CustomBenchmark (BaseBenchmark implementation)."""

    def test_load_real_custom_tasks(self):
        """Load the actual custom tasks from tasks/custom/."""
        benchmark = CustomBenchmark()
        problems = benchmark.load()

        assert len(problems) == 5
        task_ids = [p.task_id for p in problems]
        assert "Custom/001" in task_ids
        assert "Custom/005" in task_ids

    def test_get_problem(self):
        """Get a specific custom problem by task_id."""
        benchmark = CustomBenchmark()
        benchmark.load()
        problem = benchmark.get_problem("Custom/001")
        assert problem is not None
        assert problem.entry_point == "merge_sorted_arrays"

    def test_get_nonexistent_problem(self):
        """Returns None for a nonexistent task_id."""
        benchmark = CustomBenchmark()
        benchmark.load()
        assert benchmark.get_problem("Custom/999") is None

    def test_all_tasks_have_tests(self):
        """Every custom task has non-empty test code."""
        benchmark = CustomBenchmark()
        problems = benchmark.load()
        for p in problems:
            assert p.test, f"Task {p.task_id} has no tests"
            assert "check" in p.test, f"Task {p.task_id} tests missing check()"

    def test_all_tasks_have_entry_points(self):
        """Every custom task has a non-empty entry_point."""
        benchmark = CustomBenchmark()
        problems = benchmark.load()
        for p in problems:
            assert p.entry_point, f"Task {p.task_id} missing entry_point"


# ─── Test: Evaluate Real Custom Tasks ────────────────────────────────────────


class TestEvaluateRealCustomTasks:
    """Evaluate real custom tasks with known correct solutions."""

    def test_custom_001_correct(self):
        """Custom/001: merge_sorted_arrays with correct solution."""
        benchmark = CustomBenchmark()
        problem = benchmark.get_problem("Custom/001")
        assert problem is not None

        code = (
            "def merge_sorted_arrays(arr1, arr2):\n"
            "    result = []\n"
            "    i = j = 0\n"
            "    while i < len(arr1) and j < len(arr2):\n"
            "        if arr1[i] <= arr2[j]:\n"
            "            result.append(arr1[i])\n"
            "            i += 1\n"
            "        else:\n"
            "            result.append(arr2[j])\n"
            "            j += 1\n"
            "    result.extend(arr1[i:])\n"
            "    result.extend(arr2[j:])\n"
            "    return result\n"
        )

        evaluator = Evaluator(timeout=10.0)
        result = evaluator.evaluate_single(code, problem)
        assert result["passed"] is True

    def test_custom_002_correct(self):
        """Custom/002: is_anagram with correct solution."""
        benchmark = CustomBenchmark()
        problem = benchmark.get_problem("Custom/002")
        assert problem is not None

        code = (
            "from collections import Counter\n"
            "def is_anagram(s1, s2):\n"
            "    s1 = s1.lower().replace(' ', '')\n"
            "    s2 = s2.lower().replace(' ', '')\n"
            "    return Counter(s1) == Counter(s2)\n"
        )

        evaluator = Evaluator(timeout=10.0)
        result = evaluator.evaluate_single(code, problem)
        assert result["passed"] is True

    def test_custom_005_correct(self):
        """Custom/005: flatten_nested with correct solution."""
        benchmark = CustomBenchmark()
        problem = benchmark.get_problem("Custom/005")
        assert problem is not None

        code = (
            "def flatten_nested(data):\n"
            "    result = []\n"
            "    for item in data:\n"
            "        if isinstance(item, list):\n"
            "            result.extend(flatten_nested(item))\n"
            "        else:\n"
            "            result.append(item)\n"
            "    return result\n"
        )

        evaluator = Evaluator(timeout=10.0)
        result = evaluator.evaluate_single(code, problem)
        assert result["passed"] is True

    def test_custom_001_incorrect(self):
        """Custom/001: wrong solution fails."""
        benchmark = CustomBenchmark()
        problem = benchmark.get_problem("Custom/001")
        assert problem is not None

        code = (
            "def merge_sorted_arrays(arr1, arr2):\n"
            "    return arr1 + arr2\n"  # Not sorted
        )

        evaluator = Evaluator(timeout=10.0)
        result = evaluator.evaluate_single(code, problem)
        assert result["passed"] is False


# ─── Test: Pass@1 Correctness ────────────────────────────────────────────────


class TestPassAt1Correctness:
    """Verify Pass@1 logic: all-or-nothing per task."""

    def test_all_pass(self):
        """10/10 tasks correct → Pass@1 = 1.0."""
        results = [{"passed": True} for _ in range(10)]
        assert compute_pass_at_1(results) == 1.0

    def test_seven_of_ten(self):
        """7/10 tasks correct → Pass@1 = 0.7."""
        results = [{"passed": True}] * 7 + [{"passed": False}] * 3
        assert abs(compute_pass_at_1(results) - 0.7) < 1e-6

    def test_none_pass(self):
        """0/10 tasks correct → Pass@1 = 0.0."""
        results = [{"passed": False} for _ in range(10)]
        assert compute_pass_at_1(results) == 0.0
