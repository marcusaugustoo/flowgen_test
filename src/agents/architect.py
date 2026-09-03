"""
Architect agent.

Designs the solution architecture based on requirements.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.llm.base import LLMResponse
from src.orchestration.artifacts import Artifact
from src.orchestration.context import SharedContext


class Architect(BaseAgent):
    """
    Designs the solution architecture from requirements.

    Produces:
    - Function signature design
    - Algorithm/approach description
    - Data structures to use
    - Edge case handling strategy
    """

    agent_name = "architect"
    agent_role = "Software Architect"
    artifact_type = "design"
    prompt_file = "system.txt"

    def parse_response(self, response: LLMResponse, context: SharedContext) -> Artifact:
        """Parse the LLM response into a design artifact."""
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
        """Store design in the shared context."""
        context.design = artifact.content
