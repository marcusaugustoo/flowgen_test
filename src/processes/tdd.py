"""
TDD process model — Baseline C (architecture-ready stub).

Flow:
  Problem → Requirement Engineer → Architect → Tester (test design)
  → Developer → Test Execution → Developer refinement

NOTE: This is an architecture-ready stub. The full TDD logic
will be implemented when this baseline is activated.
"""

from __future__ import annotations

import logging
from typing import Any

from src.agents.factory import create_agent
from src.evaluation.test_executor import TestExecutor
from src.orchestration.context import SharedContext
from src.orchestration.orchestrator import Orchestrator
from src.processes.base import BaseProcess

logger = logging.getLogger(__name__)


class TDDProcess(BaseProcess):
    """
    TDD process model: test-first development.

    Key difference from Waterfall:
    - Tests are designed BEFORE code implementation.
    - Developer receives test expectations as part of context.
    - Iterative test-execute-fix cycle.
    """

    process_name = "tdd"

    def run(
        self,
        context: SharedContext,
        orchestrator: Orchestrator,
    ) -> SharedContext:
        """Execute the TDD pipeline."""
        logger.info("Running TDD process")

        prev_agent = None

        # Step 1: Requirement Engineer
        if self.config.agents.requirement_engineer:
            agent = create_agent("requirement_engineer", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=prev_agent)
            prev_agent = "requirement_engineer"

        # Step 2: Architect
        if self.config.agents.architect:
            agent = create_agent("architect", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=prev_agent)
            prev_agent = "architect"

        # Step 3: Tester — TEST DESIGN FIRST (TDD difference)
        if self.config.agents.tester:
            # In TDD, the tester creates tests before the developer writes code.
            # We need to set a placeholder so the tester prompt works.
            context.code = "# Code not yet implemented (TDD: tests first)"
            agent = create_agent("tester", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=prev_agent)
            prev_agent = "tester"
            context.code = ""  # Clear placeholder

        # Step 4: Developer (with test expectations in context)
        if self.config.agents.developer:
            agent = create_agent("developer", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=prev_agent)
            prev_agent = "developer"

        # Step 5: Execute tests & refinement
        if self.config.agents.tester and context.code:
            test_executor = TestExecutor(timeout=self.config.evaluation.timeout)
            test_result = test_executor.run(
                code=context.code,
                tests=context.tests,
            )
            context.test_results = test_result["output"]

            # Refinement loop
            if not test_result["passed"] and self.config.refinement.enabled:
                for iteration in range(self.config.refinement.iterations):
                    logger.info(
                        "TDD refinement iteration %d/%d",
                        iteration + 1,
                        self.config.refinement.iterations,
                    )

                    tester_agent = create_agent("tester", self.llm)
                    orchestrator.execute_agent(
                        tester_agent, context, previous_agent="test_executor"
                    )

                    dev_agent = create_agent("developer", self.llm)
                    orchestrator.execute_agent(
                        dev_agent, context, previous_agent="tester"
                    )

                    test_result = test_executor.run(
                        code=context.code,
                        tests=context.tests,
                    )
                    context.test_results = test_result["output"]

                    if test_result["passed"]:
                        logger.info(
                            "TDD: All tests passed after %d iterations",
                            iteration + 1,
                        )
                        break

        logger.info("TDD process completed")
        return context
