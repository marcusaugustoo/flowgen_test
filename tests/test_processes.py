"""Tests for process models."""

import pytest

from src.config import ExperimentConfig
from src.llm.mock_provider import MockLLMProvider
from src.orchestration.context import SharedContext
from src.orchestration.orchestrator import Orchestrator
from src.processes.factory import create_process, available_processes
from src.processes.raw import RawProcess
from src.processes.waterfall import WaterfallProcess


class TestProcessFactory:
    """Tests for process factory."""

    def test_available_processes(self):
        procs = available_processes()
        assert "raw" in procs
        assert "waterfall" in procs
        assert "tdd" in procs
        assert "scrum" in procs

    def test_create_raw_process(self, raw_config):
        llm = MockLLMProvider()
        process = create_process(raw_config, llm)
        assert isinstance(process, RawProcess)

    def test_create_waterfall_process(self, sample_config):
        llm = MockLLMProvider()
        process = create_process(sample_config, llm)
        assert isinstance(process, WaterfallProcess)

    def test_unknown_process_raises(self):
        config = ExperimentConfig.load(
            overrides={"pipeline": {"type": "nonexistent"}, "llm": {"provider": "mock"}}
        )
        llm = MockLLMProvider()
        with pytest.raises(ValueError, match="Unknown process type"):
            create_process(config, llm)


class TestRawProcess:
    """Tests for the Raw process model."""

    def test_raw_execution(self, raw_config):
        code_response = (
            "```python\n"
            "def has_close_elements(numbers, threshold):\n"
            "    for i in range(len(numbers)):\n"
            "        for j in range(i+1, len(numbers)):\n"
            "            if abs(numbers[i]-numbers[j]) < threshold:\n"
            "                return True\n"
            "    return False\n"
            "```"
        )
        llm = MockLLMProvider(default_response=code_response)
        process = create_process(raw_config, llm)
        orchestrator = Orchestrator(raw_config)
        orchestrator.new_run_id()

        context = SharedContext(
            problem="Implement has_close_elements",
            problem_id="HumanEval/0",
        )

        result = process.run(context, orchestrator)
        assert result.code
        assert "def has_close_elements" in result.code
        assert llm.call_count == 1


class TestWaterfallProcess:
    """Tests for the Waterfall process model."""

    def test_waterfall_execution(self):
        """Test full waterfall pipeline with mock LLM."""
        config = ExperimentConfig.load(
            overrides={
                "llm": {"provider": "mock"},
                "pipeline": {"type": "waterfall"},
                "self_refinement": {"enabled": False, "iterations": 0},
                "evaluation": {"timeout": 5},
            }
        )

        # Queue responses for each agent
        responses = [
            # RequirementEngineer
            "Requirements: Implement has_close_elements function",
            # Architect
            "Design: Use nested loop to compare all pairs",
            # Developer
            (
                "```python\n"
                "def has_close_elements(numbers, threshold):\n"
                "    return False\n"
                "```"
            ),
            # Tester
            (
                "```python\n"
                "assert has_close_elements([1.0, 2.0], 0.5) == False\n"
                "```"
            ),
        ]

        llm = MockLLMProvider(response_queue=responses)
        process = create_process(config, llm)
        orchestrator = Orchestrator(config)
        orchestrator.new_run_id()

        context = SharedContext(
            problem="Implement has_close_elements",
            problem_id="HumanEval/0",
            entry_point="has_close_elements",
        )

        result = process.run(context, orchestrator)

        assert result.requirements  # RE executed
        assert result.design  # Architect executed
        assert result.code  # Developer executed
        assert llm.call_count >= 3  # At least RE + Arch + Dev
