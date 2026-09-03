"""
Iteration tracking for per-stage evaluation.

Records the Pass@1 result at each evaluable stage of the pipeline
(developer_initial, refinement_1, refinement_2, etc.) so the researcher
can observe how the solution evolves over refinement iterations.

This module does NOT change the definition of Pass@1. It simply records
each evaluation that happens during the process and provides aggregation
functions to compute Pass@1 per iteration across tasks and runs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class EvaluationRecord:
    """
    A single evaluation of generated code at a specific stage.

    Attributes:
        task_id: The task being evaluated.
        iteration: 0 = developer_initial, 1+ = refinement iteration.
        stage: Human-readable stage name ('developer_initial' or 'refinement').
        passed: True if tests passed, False if failed, None if infrastructure error.
        evaluation_status: 'success' (evaluation ran) or 'error' (infrastructure issue).
        error_message: Description of the error if evaluation_status is 'error'.
        code: The code that was evaluated.
        test_output: stdout/stderr from the test execution.
        timestamp: ISO timestamp of when the evaluation occurred.
    """

    task_id: str
    iteration: int
    stage: str
    passed: Optional[bool]
    evaluation_status: str = "success"
    error_message: str = ""
    code: str = ""
    test_output: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for persistence."""
        return {
            "task_id": self.task_id,
            "iteration": self.iteration,
            "stage": self.stage,
            "passed": self.passed,
            "evaluation_status": self.evaluation_status,
            "error_message": self.error_message,
            "code": self.code,
            "test_output": self.test_output,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvaluationRecord:
        """Deserialize from dict."""
        return cls(
            task_id=data.get("task_id", ""),
            iteration=data.get("iteration", 0),
            stage=data.get("stage", ""),
            passed=data.get("passed"),
            evaluation_status=data.get("evaluation_status", "success"),
            error_message=data.get("error_message", ""),
            code=data.get("code", ""),
            test_output=data.get("test_output", ""),
            timestamp=data.get("timestamp", ""),
        )


class IterationTracker:
    """
    Tracks evaluation results across iterations for a single task.

    Usage:
        tracker = IterationTracker(task_id="task_001")
        tracker.record(EvaluationRecord(...))  # iteration 0
        tracker.record(EvaluationRecord(...))  # iteration 1
        ...
        final = tracker.get_final_result()
    """

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        self._records: list[EvaluationRecord] = []

    def record(self, evaluation: EvaluationRecord) -> None:
        """Record an evaluation result for this task."""
        self._records.append(evaluation)
        logger.debug(
            "Task '%s' iteration %d: passed=%s (stage=%s)",
            evaluation.task_id,
            evaluation.iteration,
            evaluation.passed,
            evaluation.stage,
        )

    @property
    def records(self) -> list[EvaluationRecord]:
        """All recorded evaluations, in order."""
        return list(self._records)

    @property
    def iteration_count(self) -> int:
        """Number of evaluations recorded."""
        return len(self._records)

    def get_final_result(self) -> Optional[EvaluationRecord]:
        """
        Get the final (last) evaluation result.

        Returns:
            The last EvaluationRecord, or None if no evaluations recorded.
        """
        if not self._records:
            return None
        return self._records[-1]

    def get_result_at(self, iteration: int) -> Optional[EvaluationRecord]:
        """
        Get the evaluation result for a specific iteration.

        Args:
            iteration: The iteration number (0-based).

        Returns:
            The EvaluationRecord for that iteration, or None.
        """
        for record in self._records:
            if record.iteration == iteration:
                return record
        return None

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to dict for result persistence.

        Produces the format specified in the requirements:
        {
            "task_id": "task_001",
            "iterations": [...],
            "final_passed": true/false/null
        }
        """
        final = self.get_final_result()
        return {
            "task_id": self.task_id,
            "iterations": [r.to_dict() for r in self._records],
            "final_passed": final.passed if final else None,
        }


def compute_iteration_pass_at_1(
    trackers: list[IterationTracker],
) -> dict[int, float]:
    """
    Compute Pass@1 for each iteration number across all tasks.

    For each iteration number, counts how many tasks passed and divides
    by the number of tasks that have a result at that iteration.

    Args:
        trackers: List of IterationTrackers, one per task.

    Returns:
        Dict mapping iteration number to Pass@1 score.
        Example: {0: 0.70, 1: 0.78, 2: 0.83}
    """
    if not trackers:
        return {}

    # Find the max iteration across all trackers
    max_iteration = 0
    for tracker in trackers:
        for record in tracker.records:
            if record.iteration > max_iteration:
                max_iteration = record.iteration

    result: dict[int, float] = {}

    for iteration in range(max_iteration + 1):
        passed_count = 0
        total_count = 0

        for tracker in trackers:
            record = tracker.get_result_at(iteration)
            if record is not None and record.evaluation_status == "success":
                total_count += 1
                if record.passed:
                    passed_count += 1

        if total_count > 0:
            result[iteration] = passed_count / total_count

    return result


def compute_final_pass_at_1(trackers: list[IterationTracker]) -> float:
    """
    Compute Pass@1 using only the final solution from each task.

    This is the primary metric for comparing experimental conditions.

    Args:
        trackers: List of IterationTrackers, one per task.

    Returns:
        Pass@1 score based on final solutions.
    """
    if not trackers:
        return 0.0

    passed = 0
    total = 0

    for tracker in trackers:
        final = tracker.get_final_result()
        if final is not None and final.evaluation_status == "success":
            total += 1
            if final.passed:
                passed += 1

    return passed / total if total > 0 else 0.0
