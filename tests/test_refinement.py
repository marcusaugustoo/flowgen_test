"""Tests for the refinement system."""

import pytest

from src.agents.requirement_engineer import RequirementEngineer
from src.config import ExperimentConfig
from src.llm.mock_provider import MockLLMProvider
from src.orchestration.orchestrator import Orchestrator
from src.refinement.self_refinement import SelfRefinement


class TestSelfRefinement:
    """Tests for SelfRefinement."""

    def test_refine(self, sample_config, sample_context):
        llm = MockLLMProvider(
            response_queue=[
                "Initial requirements",
                "Refined requirements v1",
                "Refined requirements v2",
                "Refined requirements v3",
            ]
        )
        agent = RequirementEngineer(llm=llm)
        orchestrator = Orchestrator(sample_config)
        orchestrator.new_run_id()

        strategy = SelfRefinement(iterations=2)
        artifact = strategy.refine(agent, sample_context, orchestrator)

        # Initial + 2 refinements = 3 calls total
        assert llm.call_count == 3
        assert artifact is not None
        assert artifact.type == "requirements"

    def test_zero_iterations(self, sample_config, sample_context):
        llm = MockLLMProvider(default_response="Initial response")
        agent = RequirementEngineer(llm=llm)
        orchestrator = Orchestrator(sample_config)
        orchestrator.new_run_id()

        strategy = SelfRefinement(iterations=0)
        artifact = strategy.refine(agent, sample_context, orchestrator)

        assert llm.call_count == 1  # Only initial generation
        assert artifact is not None
