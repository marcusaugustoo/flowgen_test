"""
Scrum Master agent.

Architecture-ready stub for the Scrum process model.
Minimal implementation to be extended when Scrum process is fully developed.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.llm.base import LLMResponse
from src.orchestration.artifacts import Artifact
from src.orchestration.context import SharedContext


class ScrumMaster(BaseAgent):
    """
    Scrum Master agent for coordinating sprint-based development.

    In the Scrum process:
    - Facilitates sprint meetings.
    - Synthesizes discussion into tasks.
    - Coordinates agent execution order within sprints.

    NOTE: This is an architecture-ready stub. Full Scrum logic will be
    implemented when the ScrumProcess is fully developed.
    """

    agent_name = "scrum_master"
    agent_role = "Scrum Master"
    artifact_type = "sprint_plan"
    prompt_file = "system.txt"

    def parse_response(self, response: LLMResponse, context: SharedContext) -> Artifact:
        """Parse the LLM response into a sprint plan artifact."""
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
        """Store sprint plan in context metadata."""
        context.metadata["sprint_plan"] = artifact.content
