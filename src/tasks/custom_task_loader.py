"""
Custom task loader for structured task directories.

Loads custom tasks from the tasks/custom/ directory structure where each
task is a directory containing:
  - task.txt:      The problem statement (what the agent sees)
  - metadata.json: {"task_id": "Custom/001", "entry_point": "function_name"}
  - tests.py:      HumanEval-format tests: def check(candidate): ...

Custom tasks are converted to Problem objects that are fully compatible
with the HumanEval evaluation pipeline (check_correctness).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from src.benchmarks.base import Problem

logger = logging.getLogger(__name__)


class CustomTaskLoader:
    """
    Loads custom tasks from structured directories.

    Each task directory must contain:
    - task.txt:      Problem statement for the agent.
    - metadata.json: Must have "task_id" and "entry_point" keys.
    - tests.py:      HumanEval-format test code (def check(candidate): ...).

    The loader converts these into Problem objects that flow through
    the same evaluation pipeline as HumanEval problems.
    """

    def load_task(self, task_dir: str | Path) -> Problem:
        """
        Load a single custom task from its directory.

        Args:
            task_dir: Path to the task directory (e.g., tasks/custom/task_001/).

        Returns:
            A Problem instance compatible with check_correctness.

        Raises:
            FileNotFoundError: If the directory or required files are missing.
            ValueError: If metadata is invalid or files are empty.
        """
        task_dir = Path(task_dir)

        if not task_dir.exists():
            raise FileNotFoundError(f"Custom task directory not found: {task_dir}")

        if not task_dir.is_dir():
            raise ValueError(f"Path is not a directory: {task_dir}")

        # Load task.txt (problem statement)
        task_txt = task_dir / "task.txt"
        if not task_txt.exists():
            raise FileNotFoundError(
                f"task.txt not found in custom task directory: {task_dir}"
            )

        description = task_txt.read_text(encoding="utf-8").strip()
        if not description:
            raise ValueError(f"task.txt is empty: {task_txt}")

        # Load metadata.json
        metadata_file = task_dir / "metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(
                f"metadata.json not found in custom task directory: {task_dir}"
            )

        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in metadata.json: {metadata_file}: {e}")

        task_id = metadata.get("task_id")
        if not task_id:
            raise ValueError(
                f"metadata.json must contain 'task_id': {metadata_file}"
            )

        entry_point = metadata.get("entry_point")
        if not entry_point:
            raise ValueError(
                f"metadata.json must contain 'entry_point': {metadata_file}"
            )

        # Load tests.py
        tests_file = task_dir / "tests.py"
        if not tests_file.exists():
            raise FileNotFoundError(
                f"tests.py not found in custom task directory: {task_dir}"
            )

        test_code = tests_file.read_text(encoding="utf-8").strip()
        if not test_code:
            raise ValueError(f"tests.py is empty: {tests_file}")

        # Build the Problem.
        # The 'prompt' field stores the problem description that the agent sees.
        # The 'test' field stores the HumanEval-format test code.
        problem = Problem(
            task_id=task_id,
            prompt=description,
            entry_point=entry_point,
            test=test_code,
            canonical_solution="",
        )

        logger.info(
            "Loaded custom task '%s' (entry_point='%s') from %s",
            task_id, entry_point, task_dir,
        )
        return problem

    def load_directory(self, directory: str | Path) -> list[Problem]:
        """
        Load all custom tasks from a directory.

        Each subdirectory must be a valid task directory.

        Args:
            directory: Path to the custom tasks root (e.g., tasks/custom/).

        Returns:
            List of Problem objects, sorted by task_id.

        Raises:
            FileNotFoundError: If the directory does not exist.
            ValueError: If no valid tasks are found.
        """
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(
                f"Custom tasks directory not found: {directory}"
            )

        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        # Find all subdirectories that look like task directories
        task_dirs = sorted(
            d for d in directory.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

        if not task_dirs:
            raise ValueError(
                f"No task directories found in: {directory}"
            )

        problems: list[Problem] = []
        errors: list[str] = []

        for task_dir in task_dirs:
            try:
                problem = self.load_task(task_dir)
                problems.append(problem)
            except (FileNotFoundError, ValueError) as e:
                errors.append(f"{task_dir.name}: {e}")
                logger.warning("Skipping task directory '%s': %s", task_dir.name, e)

        if not problems:
            error_details = "\n  ".join(errors) if errors else "No details."
            raise ValueError(
                f"No valid custom tasks could be loaded from: {directory}\n"
                f"Errors:\n  {error_details}"
            )

        logger.info(
            "Loaded %d custom tasks from %s",
            len(problems),
            directory,
        )
        return problems
