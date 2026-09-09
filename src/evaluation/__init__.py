"""Evaluation module: test execution, metrics, and statistical analysis.

The primary evaluator uses HumanEval's check_correctness for all
evaluation (both HumanEval and custom tasks).

TestExecutor remains available for agent-generated test execution
during the Waterfall process (Tester feedback), but is NOT used
for final reference test evaluation.
"""

from src.evaluation.evaluator import Evaluator
from src.evaluation.pass_at_1 import compute_pass_at_1
from src.evaluation.test_executor import TestExecutor

__all__ = ["Evaluator", "compute_pass_at_1", "TestExecutor"]
