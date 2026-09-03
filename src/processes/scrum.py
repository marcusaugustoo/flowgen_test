"""
Scrum process model — Baseline D (architecture-ready stub).

Flow:
  Problem → Sprint Meeting → Agents Discuss → Scrum Master Synthesizes
  → Tasks → Agent Execution → Sprint Review → Refinement

NOTE: This is an architecture-ready stub. The full Scrum logic
will be implemented when this baseline is activated.
"""

from __future__ import annotations

import logging
from typing import Any

from src.agents.factory import create_agent
from src.orchestration.context import SharedContext
from src.orchestration.orchestrator import Orchestrator
from src.processes.base import BaseProcess

logger = logging.getLogger(__name__)


class ScrumProcess(BaseProcess):
    """
    Scrum process model: sprint-based development.

    Key differences from Waterfall:
    - Agents operate in sprints (iterative).
    - Scrum Master coordinates and synthesizes.
    - Discussion phase before execution.

    NOTE: Current implementation falls back to a simplified sequential
    execution. Full sprint meeting / discussion logic is planned for
    future implementation.
    """

    process_name = "scrum"

    def run(
        self,
        context: SharedContext,
        orchestrator: Orchestrator,
    ) -> SharedContext:
        """Execute the Scrum pipeline (simplified version)."""
        logger.info("Running Scrum process (simplified)")

        # Sprint 1: Planning
        if self.config.agents.scrum_master:
            agent = create_agent("scrum_master", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=None)
            logger.info("Sprint planning completed")

        prev_agent = "scrum_master" if self.config.agents.scrum_master else None

        # Sprint execution: agents execute in sequence
        # (Simplified — full Scrum will have discussion rounds)
        if self.config.agents.requirement_engineer:
            agent = create_agent("requirement_engineer", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=prev_agent)
            prev_agent = "requirement_engineer"

        if self.config.agents.architect:
            agent = create_agent("architect", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=prev_agent)
            prev_agent = "architect"

        if self.config.agents.developer:
            agent = create_agent("developer", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=prev_agent)
            prev_agent = "developer"

        if self.config.agents.tester:
            agent = create_agent("tester", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=prev_agent)
            prev_agent = "tester"

        # Sprint Review (Scrum Master reviews)
        if self.config.agents.scrum_master and context.code:
            agent = create_agent("scrum_master", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=prev_agent)
            logger.info("Sprint review completed")

        logger.info("Scrum process completed")
        return context
