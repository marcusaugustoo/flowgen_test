"""Tests for the Orchestrator."""

import pytest

from src.agents.requirement_engineer import RequirementEngineer
from src.agents.developer import Developer
from src.config import ExperimentConfig
from src.orchestration.orchestrator import Orchestrator


class TestOrchestrator:
    """Tests for the Orchestrator."""

    def test_new_run_id(self, sample_config):
        orch = Orchestrator(sample_config)
        run_id = orch.new_run_id()
        assert run_id
        assert len(run_id) == 8

    def test_execute_agent(self, mock_llm, sample_config, sample_context):
        orch = Orchestrator(sample_config)
        orch.new_run_id()
        agent = RequirementEngineer(llm=mock_llm)
        artifact = orch.execute_agent(agent, sample_context)
        assert artifact.type == "requirements"
        assert orch.artifact_store.count == 1
        assert orch.message_bus.count >= 1

    def test_agent_chain(self, mock_llm_with_code, sample_config, sample_context):
        orch = Orchestrator(sample_config)
        orch.new_run_id()

        # RE → Architect → Developer
        re_agent = RequirementEngineer(llm=mock_llm_with_code)
        orch.execute_agent(re_agent, sample_context)
        assert sample_context.requirements  # Updated

        from src.agents.architect import Architect
        arch_agent = Architect(llm=mock_llm_with_code)
        orch.execute_agent(arch_agent, sample_context, previous_agent="requirement_engineer")
        assert sample_context.design

        dev_agent = Developer(llm=mock_llm_with_code)
        orch.execute_agent(dev_agent, sample_context, previous_agent="architect")
        assert sample_context.code

        # Check artifacts and messages were recorded
        assert orch.artifact_store.count == 3
        assert orch.message_bus.count >= 3

    def test_reset_for_run(self, sample_config, mock_llm, sample_context):
        orch = Orchestrator(sample_config)
        orch.new_run_id()
        agent = RequirementEngineer(llm=mock_llm)
        orch.execute_agent(agent, sample_context)
        orch.reset_for_run()
        assert orch.artifact_store.count == 0
        assert orch.message_bus.count == 0

    def test_execution_log(self, mock_llm, sample_config, sample_context):
        orch = Orchestrator(sample_config)
        orch.new_run_id()
        agent = RequirementEngineer(llm=mock_llm)
        orch.execute_agent(agent, sample_context)
        log = orch.get_execution_log()
        assert len(log) == 1
        assert log[0]["agent"] == "requirement_engineer"
        assert "elapsed_ms" in log[0]
