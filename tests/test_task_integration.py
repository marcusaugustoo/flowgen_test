"""
Integration test for the TaskLoader -> Process pipeline.

Demonstrates the full flow: TXT -> Task -> Problem -> Orchestrator -> Process -> Code,
using MockLLMProvider to avoid Ollama dependency.
"""

import tempfile
from pathlib import Path

import pytest

from src.config import ExperimentConfig
from src.llm.mock_provider import MockLLMProvider
from src.orchestration.context import SharedContext
from src.orchestration.orchestrator import Orchestrator
from src.processes.raw import RawProcess
from src.processes.waterfall import WaterfallProcess
from src.tasks.task_loader import TaskLoader


@pytest.fixture
def task_file(tmp_path):
    """Create a temporary .txt task file."""
    task_path = tmp_path / "task_soma.txt"
    task_path.write_text(
        "Implemente uma função chamada soma que receba dois inteiros a e b "
        "e retorne a soma deles.",
        encoding="utf-8",
    )
    return task_path


@pytest.fixture
def task_file_with_tests(tmp_path):
    """Create a temporary .txt task file with companion tests."""
    task_path = tmp_path / "task_soma.txt"
    task_path.write_text(
        "Implemente uma função chamada soma que receba dois inteiros a e b "
        "e retorne a soma deles.",
        encoding="utf-8",
    )
    test_path = tmp_path / "task_soma_test.py"
    test_path.write_text(
        "def check(candidate):\n"
        "    assert candidate(1, 2) == 3\n"
        "    assert candidate(0, 0) == 0\n"
        "    assert candidate(-1, 1) == 0\n"
        "\ncheck(soma)\n",
        encoding="utf-8",
    )
    return task_path


@pytest.fixture
def mock_llm_code():
    """MockLLMProvider that returns valid Python code."""
    return MockLLMProvider(
        default_response=(
            "```python\n"
            "def soma(a, b):\n"
            "    return a + b\n"
            "```"
        ),
        latency_ms=5.0,
    )


@pytest.fixture
def raw_config():
    """ExperimentConfig for raw process."""
    return ExperimentConfig.load(
        overrides={
            "llm": {"provider": "mock"},
            "experiment": {"name": "test_task_integration", "runs": 1},
            "pipeline": {"type": "raw"},
        }
    )


@pytest.fixture
def waterfall_config():
    """ExperimentConfig for waterfall process."""
    return ExperimentConfig.load(
        overrides={
            "llm": {"provider": "mock"},
            "experiment": {"name": "test_task_integration", "runs": 1},
            "pipeline": {"type": "waterfall"},
        }
    )


class TestTaskToRawIntegration:
    """Integration: TXT -> Task -> Problem -> Raw Process -> Code."""

    def test_txt_through_raw_pipeline(self, task_file, mock_llm_code, raw_config):
        """A .txt task file flows through the Raw process and produces code."""
        # Step 1: Load task from .txt
        loader = TaskLoader()
        task = loader.load_file(task_file)

        # Step 2: Convert to Problem
        problem = task.to_problem()
        assert problem.task_id == "task_soma"
        assert "soma" in problem.prompt

        # Step 3: Create context (same as main.py does)
        context = SharedContext(
            problem=problem.prompt,
            problem_id=problem.task_id,
            entry_point=problem.entry_point,
            canonical_tests=problem.test,
        )

        # Step 4: Run Raw process
        process = RawProcess(config=raw_config, llm=mock_llm_code)
        orchestrator = Orchestrator(raw_config)
        orchestrator.reset_for_run()

        context = process.run(context, orchestrator)

        # Step 5: Verify code was generated
        assert context.code != ""
        assert "soma" in context.code or "def" in context.code

    def test_txt_with_tests_through_raw(self, task_file_with_tests, mock_llm_code, raw_config):
        """A .txt with companion test file loads test_code into the Problem."""
        loader = TaskLoader()
        task = loader.load_file(task_file_with_tests)
        problem = task.to_problem()

        # The companion test file should be loaded
        assert "check(candidate)" in problem.test
        assert "soma" in problem.test


class TestTaskToWaterfallIntegration:
    """Integration: TXT -> Task -> Problem -> Waterfall Process -> Code."""

    def test_txt_through_waterfall_pipeline(self, task_file, waterfall_config):
        """A .txt task flows through the full Waterfall pipeline."""
        # Load task
        loader = TaskLoader()
        task = loader.load_file(task_file)
        problem = task.to_problem()

        # Create mock LLM with multiple responses for each agent
        mock_llm = MockLLMProvider(
            default_response="```python\ndef soma(a, b):\n    return a + b\n```",
            latency_ms=5.0,
        )

        # Create context
        context = SharedContext(
            problem=problem.prompt,
            problem_id=problem.task_id,
            entry_point=problem.entry_point,
            canonical_tests=problem.test,
        )

        # Run Waterfall
        process = WaterfallProcess(config=waterfall_config, llm=mock_llm)
        orchestrator = Orchestrator(waterfall_config)
        orchestrator.reset_for_run()

        context = process.run(context, orchestrator)

        # Verify that the pipeline ran and produced artifacts
        assert context.code != ""
        assert len(orchestrator.artifact_store.all_artifacts) > 0
        assert len(orchestrator.message_bus.all_messages) > 0


class TestTaskDirectoryIntegration:
    """Integration: Directory of .txt -> list[Task] -> list[Problem]."""

    def test_directory_to_problems(self, tmp_path):
        """A directory of .txt files converts cleanly to a list of Problems."""
        # Create task files
        (tmp_path / "task_a.txt").write_text("Implement function a.", encoding="utf-8")
        (tmp_path / "task_b.txt").write_text("Implement function b.", encoding="utf-8")
        (tmp_path / "task_c.txt").write_text("Implement function c.", encoding="utf-8")

        loader = TaskLoader()
        tasks = loader.load_directory(tmp_path)
        problems = [t.to_problem() for t in tasks]

        assert len(problems) == 3
        assert all(isinstance(p.task_id, str) for p in problems)
        assert all(p.prompt for p in problems)
        assert problems[0].task_id == "task_a"
        assert problems[1].task_id == "task_b"
        assert problems[2].task_id == "task_c"
