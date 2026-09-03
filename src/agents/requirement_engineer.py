"""
Requirement Engineer agent.

Analyzes the programming problem and produces structured requirements.
"""

from __future__ import annotations

import re
from typing import Any

from src.agents.base_agent import BaseAgent
from src.llm.base import LLMResponse
from src.orchestration.artifacts import Artifact
from src.orchestration.context import SharedContext


class RequirementEngineer(BaseAgent):
    """
    Analyzes the programming problem and extracts structured requirements.

    Produces:
    - Functional requirements
    - Input/output constraints
    - Edge cases
    """

    agent_name = "requirement_engineer"
    agent_role = "Requirement Engineer"
    artifact_type = "requirements"
    prompt_file = "system.txt"

    def parse_response(self, response: LLMResponse, context: SharedContext) -> Artifact:
        """Parse the LLM response into a requirements artifact."""
        return Artifact(
            type=self.artifact_type,
            content=response.content,
            created_by=self.agent_name,
            metadata={
                "model": response.model,
                "latency_ms": response.latency_ms,
                "tokens": response.total_tokens,
            },
        )

    def update_context(self, context: SharedContext, artifact: Artifact) -> None:
        """Store requirements in the shared context."""
        context.requirements = artifact.content
