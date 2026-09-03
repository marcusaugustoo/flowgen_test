"""
HumanEval benchmark loader.

Loads HumanEval problems from JSONL format.
Supports the full dataset (164 problems) and subsets.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from src.benchmarks.base import BaseBenchmark, Problem

logger = logging.getLogger(__name__)

# Default mini dataset path
_DEFAULT_MINI_PATH = Path(__file__).resolve().parent.parent.parent / "datasets" / "humaneval_mini.jsonl"


class HumanEvalBenchmark(BaseBenchmark):
    """
    HumanEval benchmark: 164 Python programming problems.

    Each problem consists of:
    - A function signature with docstring
    - Test cases for evaluation
    - An entry point (function name)
    """

    benchmark_name = "humaneval"

    def __init__(self, dataset_path: Optional[str | Path] = None) -> None:
        self._dataset_path = Path(dataset_path) if dataset_path else _DEFAULT_MINI_PATH
        self._problems: list[Problem] = []
        self._loaded = False

    def load(self) -> list[Problem]:
        """Load problems from JSONL file."""
        if self._loaded:
            return self._problems

        if not self._dataset_path.exists():
            raise FileNotFoundError(
                f"HumanEval dataset not found at: {self._dataset_path}. "
                f"Please provide a valid dataset path or use the built-in mini dataset."
            )

        self._problems = []
        with open(self._dataset_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                problem = Problem(
                    task_id=data.get("task_id", ""),
                    prompt=data.get("prompt", ""),
                    entry_point=data.get("entry_point", ""),
                    test=data.get("test", ""),
                    canonical_solution=data.get("canonical_solution", ""),
                )
                self._problems.append(problem)

        self._loaded = True
        logger.info(
            "Loaded %d problems from %s",
            len(self._problems),
            self._dataset_path,
        )
        return self._problems

    def get_problem(self, task_id: str) -> Optional[Problem]:
        """Get a specific problem by task_id."""
        if not self._loaded:
            self.load()
        for p in self._problems:
            if p.task_id == task_id:
                return p
        return None

    def get_subset(self, indices: list[int]) -> list[Problem]:
        """Get a subset of problems by index."""
        if not self._loaded:
            self.load()
        return [self._problems[i] for i in indices if i < len(self._problems)]

    @property
    def size(self) -> int:
        """Total number of problems."""
        if not self._loaded:
            self.load()
        return len(self._problems)
