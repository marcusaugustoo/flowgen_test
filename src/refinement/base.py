"""
Base refinement strategy abstraction.

Refinement strategies are independent of agents and processes.
They define how artifacts are reviewed and improved iteratively.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agents.base_agent import BaseAgent
    from src.orchestration.artifacts import Artifact
    from src.orchestration.context import SharedContext
    from src.orchestration.orchestrator import Orchestrator


class BaseRefinementStrategy(ABC):
    """
    Abstract base class for refinement strategies.

    A refinement strategy defines how an agent's output is iteratively
    improved through review and regeneration cycles.
    """

    strategy_name: str = "base"

    def __init__(self, iterations: int = 3) -> None:
        self.iterations = iterations

    @abstractmethod
    def refine(
        self,
        agent: BaseAgent,
        context: SharedContext,
        orchestrator: Orchestrator,
    ) -> Artifact:
        """
        Refine an agent's output through iterative improvement.

        Args:
            agent: The agent whose output is being refined.
            context: The shared context.
            orchestrator: The orchestrator managing execution.

        Returns:
            The refined artifact.
        """
        ...
