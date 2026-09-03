"""
Central orchestrator for pipeline execution.

Controls agent invocation, context passing, message recording, and artifact persistence.
Agents NEVER call other agents directly — all communication flows through the orchestrator.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING, Any, Optional

from src.orchestration.artifacts import Artifact, ArtifactStore
from src.orchestration.context import SharedContext
from src.orchestration.messages import AgentMessage, MessageBus

if TYPE_CHECKING:
    from src.agents.base_agent import BaseAgent
    from src.config import ExperimentConfig

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Controls the execution flow of a pipeline.

    Responsibilities:
    - Invoke agents in the order defined by the process model.
    - Pass relevant context to each agent.
    - Record all messages and artifacts.
    - Track execution metrics.
    """

    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config
        self.message_bus = MessageBus()
        self.artifact_store = ArtifactStore()
        self._run_id = ""
        self._execution_log: list[dict[str, Any]] = []

    def new_run_id(self) -> str:
        """Generate a new unique run ID."""
        self._run_id = str(uuid.uuid4())[:8]
        return self._run_id

    @property
    def run_id(self) -> str:
        return self._run_id

    def execute_agent(
        self,
        agent: BaseAgent,
        context: SharedContext,
        previous_agent: Optional[str] = None,
    ) -> Artifact:
        """
        Execute a single agent and record the interaction.

        Args:
            agent: The agent to execute.
            context: The shared context (agent receives filtered view).
            previous_agent: Name of the previous agent (for message recording).

        Returns:
            The artifact produced by the agent.
        """
        logger.info(
            "Executing agent '%s' (run=%s)", agent.name, self._run_id
        )

        start_time = time.perf_counter()

        # Execute the agent
        artifact = agent.execute(context)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Store the artifact
        self.artifact_store.store(artifact)

        # Record the message from previous agent → this agent
        if previous_agent:
            self.message_bus.create_and_record(
                sender=previous_agent,
                receiver=agent.name,
                message_type="artifact",
                content=f"Passed context to {agent.name}",
                run_id=self._run_id,
                artifact_id=artifact.artifact_id,
            )

        # Record the output message from this agent
        self.message_bus.create_and_record(
            sender=agent.name,
            receiver="orchestrator",
            message_type="artifact_produced",
            content=f"Produced {artifact.type} artifact",
            run_id=self._run_id,
            artifact_id=artifact.artifact_id,
        )

        # Log execution
        self._execution_log.append({
            "agent": agent.name,
            "artifact_id": artifact.artifact_id,
            "artifact_type": artifact.type,
            "elapsed_ms": elapsed_ms,
            "run_id": self._run_id,
        })

        logger.info(
            "Agent '%s' completed in %.1fms, produced artifact '%s' (type=%s)",
            agent.name,
            elapsed_ms,
            artifact.artifact_id,
            artifact.type,
        )

        return artifact

    def get_execution_log(self) -> list[dict[str, Any]]:
        """Get the execution log for the current run."""
        return list(self._execution_log)

    def reset_for_run(self) -> None:
        """Reset orchestrator state for a new run (preserves config)."""
        self.message_bus.clear()
        self.artifact_store.clear()
        self._execution_log.clear()
        self.new_run_id()
