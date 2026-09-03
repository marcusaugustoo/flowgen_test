"""
Waterfall process model — Baseline B.

Sequential flow:
  Problem → Requirement Engineer → Architect → Developer → Tester → Developer Refinement

With configurable self-refinement iterations.
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


class WaterfallProcess(BaseProcess):
    """
    Waterfall process model: sequential agent execution.

    Flow:
    1. Requirement Engineer → requirements
    2. Architect → design
    3. Developer → code
    4. Tester → tests
    5. Execute tests
    6. If failures and refinement enabled:
       a. Developer refinement → new code
       b. Execute tests again
       c. Repeat up to N iterations
    """

    process_name = "waterfall"

    def run(
        self,
        context: SharedContext,
        orchestrator: Orchestrator,
    ) -> SharedContext:
        """Execute the waterfall pipeline."""
        logger.info("Running Waterfall process")

        prev_agent = None

        # Step 1: Requirement Engineer
        if self.config.agents.requirement_engineer:
            agent = create_agent("requirement_engineer", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=prev_agent)
            prev_agent = "requirement_engineer"
            logger.info("Requirements generated")

        # Step 2: Architect
        if self.config.agents.architect:
            agent = create_agent("architect", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=prev_agent)
            prev_agent = "architect"
            logger.info("Design generated")

        # Step 3: Developer
        if self.config.agents.developer:
            agent = create_agent("developer", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=prev_agent)
            prev_agent = "developer"
            logger.info("Code generated")

        # Step 4: Tester (generate tests)
        if self.config.agents.tester:
            agent = create_agent("tester", self.llm)
            orchestrator.execute_agent(agent, context, previous_agent=prev_agent)
            prev_agent = "tester"
            logger.info("Tests generated")

            # Step 5: Execute tests
            test_executor = TestExecutor(timeout=self.config.evaluation.timeout)
            test_result = test_executor.run(
                code=context.code,
                tests=context.tests,
            )
            context.test_results = test_result["output"]

            if not test_result["passed"]:
                logger.info("Tests failed. Starting refinement loop.")

                # Step 6: Self-refinement loop
                if self.config.refinement.enabled:
                    for iteration in range(self.config.refinement.iterations):
                        logger.info(
                            "Refinement iteration %d/%d",
                            iteration + 1,
                            self.config.refinement.iterations,
                        )

                        # Tester produces failure report
                        tester_agent = create_agent("tester", self.llm)
                        orchestrator.execute_agent(
                            tester_agent, context, previous_agent="test_executor"
                        )

                        # Developer refines code
                        dev_agent = create_agent("developer", self.llm)
                        orchestrator.execute_agent(
                            dev_agent, context, previous_agent="tester"
                        )

                        # Re-execute tests
                        test_result = test_executor.run(
                            code=context.code,
                            tests=context.tests,
                        )
                        context.test_results = test_result["output"]

                        if test_result["passed"]:
                            logger.info(
                                "All tests passed after %d refinement iterations",
                                iteration + 1,
                            )
                            break
                    else:
                        logger.info(
                            "Refinement completed without passing all tests"
                        )
            else:
                logger.info("All tests passed on first attempt")

        logger.info("Waterfall process completed")
        return context
