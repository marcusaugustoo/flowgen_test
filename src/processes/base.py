"""
Base process model abstraction.

A ProcessModel defines:
- The order in which agents execute
- What artifacts are required at each step
- Transitions between steps
- Refinement rules
- Repetition conditions

The agent does NOT know which process model it is running in.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.config import ExperimentConfig
    from src.llm.base import BaseLLMProvider
    from src.orchestration.context import SharedContext
    from src.orchestration.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class BaseProcess(ABC):
    """
    Abstract base class for process models.

    Subclasses implement `run()` to define the agent execution sequence.
    """

    process_name: str = "base"

    def __init__(self, config: ExperimentConfig, llm: BaseLLMProvider) -> None:
        self.config = config
        self.llm = llm

    @abstractmethod
    def run(
        self,
        context: SharedContext,
        orchestrator: Orchestrator,
    ) -> SharedContext:
        """
        Execute the process model.

        Args:
            context: SharedContext initialized with the problem.
            orchestrator: Orchestrator to manage agent execution.

        Returns:
            Updated SharedContext with all artifacts.
        """
        ...

    def get_enabled_agents(self) -> list[str]:
        """Get the list of agents enabled in config."""
        agents = []
        if self.config.agents.requirement_engineer:
            agents.append("requirement_engineer")
        if self.config.agents.architect:
            agents.append("architect")
        if self.config.agents.developer:
            agents.append("developer")
        if self.config.agents.tester:
            agents.append("tester")
        if self.config.agents.scrum_master:
            agents.append("scrum_master")
        return agents
