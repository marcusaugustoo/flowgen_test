"""
Base benchmark abstraction.

Benchmarks provide standardized programming problems for evaluation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Problem:
    """
    A single programming problem from a benchmark.

    Attributes:
        task_id: Unique identifier (e.g., 'HumanEval/0').
        prompt: The function signature and docstring (problem statement).
        entry_point: The function name to call for testing.
        test: The test code to evaluate the solution.
        canonical_solution: The reference solution (if available).
    """
    task_id: str
    prompt: str
    entry_point: str
    test: str
    canonical_solution: str = ""


class BaseBenchmark(ABC):
    """
    Abstract base class for benchmarks.

    Subclasses load problems from specific datasets (HumanEval, MBPP, etc.).
    """

    benchmark_name: str = "base"

    @abstractmethod
    def load(self) -> list[Problem]:
        """Load all problems from the benchmark."""
        ...

    @abstractmethod
    def get_problem(self, task_id: str) -> Optional[Problem]:
        """Get a specific problem by task_id."""
        ...

    @abstractmethod
    def get_subset(self, indices: list[int]) -> list[Problem]:
        """Get a subset of problems by index."""
        ...

    @property
    @abstractmethod
    def size(self) -> int:
        """Total number of problems in the benchmark."""
        ...
