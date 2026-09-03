"""
Base agent abstraction.

All agents inherit from BaseAgent and implement execute().
Agents are decoupled from:
- Specific LLM providers (use BaseLLMProvider)
- Process models (don't know if Waterfall/TDD/Scrum)
- Other agents (communicate only via SharedContext through Orchestrator)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from src.llm.base import BaseLLMProvider, LLMResponse
from src.orchestration.artifacts import Artifact
from src.orchestration.context import SharedContext

logger = logging.getLogger(__name__)

# Prompt templates directory
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Each agent has:
    - A name and role description
    - An LLM provider (injected, not owned)
    - A prompt template loaded from disk
    - An execute() method that produces an Artifact
    """

    # Subclasses should set these
    agent_name: str = "base"
    agent_role: str = "Base Agent"
    artifact_type: str = "generic"
    prompt_file: str = "system.txt"

    def __init__(
        self,
        llm: BaseLLMProvider,
        prompt_dir: Optional[str | Path] = None,
        **kwargs: Any,
    ):
        self.llm = llm
        self._prompt_dir = Path(prompt_dir) if prompt_dir else PROMPTS_DIR / self.agent_name
        self._prompt_template: Optional[str] = None

    @property
    def name(self) -> str:
        return self.agent_name

    @property
    def role(self) -> str:
        return self.agent_role

    def load_prompt_template(self, filename: Optional[str] = None) -> str:
        """
        Load a prompt template from the prompts directory.

        Args:
            filename: Override the default prompt file name.

        Returns:
            The prompt template string with placeholders.
        """
        filename = filename or self.prompt_file
        prompt_path = self._prompt_dir / filename

        if not prompt_path.exists():
            logger.warning(
                "Prompt template not found: %s. Using fallback.", prompt_path
            )
            return self._fallback_prompt()

        with open(prompt_path, "r") as f:
            return f.read()

    def _fallback_prompt(self) -> str:
        """Fallback prompt if template file is missing."""
        return (
            f"Role: You are a {self.agent_role}.\n\n"
            f"Instruction: Complete the task based on the provided context.\n\n"
            f"Context:\n{{context}}"
        )

    def format_prompt(self, context: dict[str, Any], template: Optional[str] = None) -> str:
        """
        Format a prompt template with context values.

        Uses Python str.format_map with a SafeDict to handle missing keys gracefully.

        Args:
            context: Dict of context values to inject.
            template: Optional template override.

        Returns:
            Formatted prompt string.
        """
        if template is None:
            template = self.load_prompt_template()

        # Use safe formatting that doesn't raise on missing keys
        try:
            return template.format_map(_SafeDict(context))
        except Exception as e:
            logger.warning("Prompt formatting error: %s. Using raw template.", e)
            return template

    def execute(self, context: SharedContext) -> Artifact:
        """
        Execute this agent's task.

        1. Get relevant context for this agent.
        2. Format the prompt template.
        3. Call the LLM.
        4. Parse the response into an Artifact.
        5. Update the SharedContext.

        Args:
            context: The shared context with all pipeline data.

        Returns:
            An Artifact containing this agent's output.
        """
        # Get filtered context
        agent_context = context.get_context_for_agent(self.agent_name)

        # Format prompt
        prompt = self.format_prompt(agent_context)

        # Call LLM
        logger.debug("Agent '%s' calling LLM with prompt length %d", self.name, len(prompt))
        response = self.llm.generate(prompt)

        # Parse into artifact
        artifact = self.parse_response(response, context)

        # Update context
        self.update_context(context, artifact)

        return artifact

    @abstractmethod
    def parse_response(self, response: LLMResponse, context: SharedContext) -> Artifact:
        """
        Parse the LLM response into a structured Artifact.

        Subclasses implement this to handle agent-specific output formats.

        Args:
            response: The raw LLM response.
            context: The shared context (for reference).

        Returns:
            A structured Artifact.
        """
        ...

    @abstractmethod
    def update_context(self, context: SharedContext, artifact: Artifact) -> None:
        """
        Update the shared context with this agent's output.

        Args:
            context: The shared context to update.
            artifact: The artifact produced by this agent.
        """
        ...


class _SafeDict(dict):
    """Dict that returns the key as placeholder for missing keys."""

    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"
