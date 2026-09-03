"""
Raw process model — Baseline A.

Single LLM call: Problem → LLM → Code.
No agents, no refinement.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from src.agents.base_agent import PROMPTS_DIR
from src.llm.base import BaseLLMProvider
from src.orchestration.artifacts import Artifact
from src.orchestration.context import SharedContext
from src.orchestration.orchestrator import Orchestrator
from src.processes.base import BaseProcess

logger = logging.getLogger(__name__)


class RawProcess(BaseProcess):
    """
    Raw baseline process: single LLM call.

    This serves as the control baseline (Baseline A).
    No agents are used — the problem is sent directly to the LLM.
    """

    process_name = "raw"

    def run(
        self,
        context: SharedContext,
        orchestrator: Orchestrator,
    ) -> SharedContext:
        """Execute raw single-shot code generation."""
        logger.info("Running Raw process (single LLM call)")

        # Load raw prompt template
        prompt_path = PROMPTS_DIR / "raw" / "system.txt"
        if prompt_path.exists():
            with open(prompt_path, "r") as f:
                template = f.read()
        else:
            template = (
                "Implement the following function in Python.\n"
                "Output ONLY the Python code in ```python ... ``` markers.\n\n"
                "Problem:\n{problem}"
            )

        prompt = template.format(problem=context.problem)

        # Single LLM call
        response = self.llm.generate(prompt)

        # Extract code
        code = self._extract_code(response.content)

        # Create artifact
        artifact = Artifact(
            type="code",
            content=code,
            language="python",
            created_by="raw_llm",
            metadata={
                "model": response.model,
                "latency_ms": response.latency_ms,
                "tokens": response.total_tokens,
                "process": "raw",
            },
        )

        # Store artifact and update context
        orchestrator.artifact_store.store(artifact)
        context.code = code

        # Record message
        orchestrator.message_bus.create_and_record(
            sender="raw_llm",
            receiver="orchestrator",
            message_type="artifact_produced",
            content="Generated code via single LLM call",
            run_id=orchestrator.run_id,
            artifact_id=artifact.artifact_id,
        )

        logger.info("Raw process completed. Code length: %d chars", len(code))

        return context

    @staticmethod
    def _extract_code(text: str) -> str:
        """Extract Python code from LLM response."""
        pattern = r"```python\s*\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return "\n".join(matches).strip()

        pattern = r"```\s*\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return "\n".join(matches).strip()

        return text.strip()
