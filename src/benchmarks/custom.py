"""
Custom benchmark loader.

Loads custom tasks from structured directories and presents them
through the BaseBenchmark interface, allowing them to flow through
the same evaluation pipeline as HumanEval problems.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from src.benchmarks.base import BaseBenchmark, Problem
from src.tasks.custom_task_loader import CustomTaskLoader

logger = logging.getLogger(__name__)

# Default custom tasks path
_DEFAULT_CUSTOM_PATH = Path(__file__).resolve().parent.parent.parent / "tasks" / "custom"


class CustomBenchmark(BaseBenchmark):
    """
    Custom benchmark: user-defined programming problems.

    Each problem is a directory under tasks/custom/ containing:
    - task.txt:      Problem statement
    - metadata.json: task_id and entry_point
    - tests.py:      HumanEval-format tests

    All problems are evaluated using the same HumanEval evaluation
    mechanism (check_correctness).
    """

    benchmark_name = "custom"

    def __init__(self, dataset_path: Optional[str | Path] = None) -> None:
        self._dataset_path = Path(dataset_path) if dataset_path else _DEFAULT_CUSTOM_PATH
        self._problems: list[Problem] = []
        self._loaded = False

    def load(self) -> list[Problem]:
        """Load all custom tasks from the directory."""
        if self._loaded:
            return self._problems

        if not self._dataset_path.exists():
            raise FileNotFoundError(
                f"Custom tasks directory not found at: {self._dataset_path}. "
                f"Create task directories under tasks/custom/."
            )

        loader = CustomTaskLoader()
        self._problems = loader.load_directory(self._dataset_path)
        self._loaded = True

        logger.info(
            "Loaded %d custom problems from %s",
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
        """Total number of custom problems."""
        if not self._loaded:
            self.load()
        return len(self._problems)
