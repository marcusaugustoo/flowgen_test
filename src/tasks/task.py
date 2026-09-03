"""
Task dataclass for representing programming tasks loaded from .txt files.

A Task is the framework's internal representation of a programming problem.
It can be converted to a Problem (the benchmark abstraction) so that agents,
processes, and the evaluator work identically regardless of input source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from src.benchmarks.base import Problem


@dataclass
class Task:
    """
    A programming task loaded from a .txt file.

    Attributes:
        task_id: Unique identifier derived from the file name (e.g., 'task_001').
        file_name: Original file name (e.g., 'task_001.txt').
        description: Full content of the .txt file (the problem statement).
        test_code: Optional canonical test code loaded from a companion
                   _test.py file. If empty, the evaluator will rely on
                   agent-generated tests or simple execution checks.
        metadata: Extra information (source path, timestamps, etc.).
    """

    task_id: str
    file_name: str
    description: str
    test_code: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_problem(self) -> Problem:
        """
        Convert this Task to a Problem for pipeline compatibility.

        The Problem is the common abstraction used by processes, agents,
        and the evaluator. This conversion ensures that tasks from .txt files
        flow through the exact same pipeline as HumanEval problems.

        Returns:
            A Problem instance with the task description as the prompt.
        """
        return Problem(
            task_id=self.task_id,
            prompt=self.description,
            entry_point="",  # Will be inferred from generated code
            test=self.test_code,
            canonical_solution="",
        )
