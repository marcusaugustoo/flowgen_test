"""Tests for the benchmark loader."""

import pytest

from src.benchmarks.humaneval import HumanEvalBenchmark


class TestHumanEvalBenchmark:
    """Tests for HumanEvalBenchmark."""

    def test_load_mini_dataset(self):
        benchmark = HumanEvalBenchmark()
        problems = benchmark.load()
        assert len(problems) == 5
        assert problems[0].task_id == "HumanEval/0"
        assert problems[0].entry_point == "has_close_elements"

    def test_get_problem(self):
        benchmark = HumanEvalBenchmark()
        benchmark.load()
        problem = benchmark.get_problem("HumanEval/0")
        assert problem is not None
        assert problem.entry_point == "has_close_elements"

    def test_get_nonexistent_problem(self):
        benchmark = HumanEvalBenchmark()
        benchmark.load()
        assert benchmark.get_problem("HumanEval/999") is None

    def test_get_subset(self):
        benchmark = HumanEvalBenchmark()
        benchmark.load()
        subset = benchmark.get_subset([0, 2, 4])
        assert len(subset) == 3
        assert subset[0].task_id == "HumanEval/0"
        assert subset[1].task_id == "HumanEval/2"

    def test_size(self):
        benchmark = HumanEvalBenchmark()
        assert benchmark.size == 5

    def test_problem_has_tests(self):
        benchmark = HumanEvalBenchmark()
        benchmark.load()
        problem = benchmark.get_problem("HumanEval/0")
        assert problem is not None
        assert "check" in problem.test
        assert "assert" in problem.test

    def test_problem_has_prompt(self):
        benchmark = HumanEvalBenchmark()
        benchmark.load()
        problem = benchmark.get_problem("HumanEval/0")
        assert problem is not None
        assert "def has_close_elements" in problem.prompt

    def test_nonexistent_file_raises(self):
        benchmark = HumanEvalBenchmark(dataset_path="/nonexistent/path.jsonl")
        with pytest.raises(FileNotFoundError):
            benchmark.load()
