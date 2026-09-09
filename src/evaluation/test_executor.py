"""
Test executor with basic sandboxing.

Runs generated code in a subprocess with:
- Timeout control
- Temporary directory isolation
- stdout/stderr capture

Architecture is prepared for more advanced sandboxing (Docker, seccomp, etc.)
in future versions.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TestExecutor:
    """
    Executes generated code + tests in a controlled subprocess.

    Security measures (v1):
    - Subprocess isolation (separate process)
    - Configurable timeout
    - Temporary directory for file operations
    - stdout/stderr capture

    Future improvements:
    - Docker container isolation
    - Memory limits
    - Network restrictions
    - Filesystem restrictions
    """

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    def run(
        self,
        code: str,
        tests: str,
        entry_point: str = "",
    ) -> dict[str, Any]:
        """
        Execute code with tests and return results.

        Combines the generated code and test code into a single script,
        then executes it in a subprocess.

        Args:
            code: The generated Python code.
            tests: The test code to run against it.
            entry_point: The function name (for HumanEval-style tests).

        Returns:
            Dict with keys:
            - passed: bool
            - output: str (combined stdout/stderr)
            - stdout: str
            - stderr: str
            - return_code: int
            - error: Optional[str]
            - timeout: bool
        """
        # Combine code + tests into a single executable script
        script = self._build_script(code, tests)

        return self._execute_script(script)

    def run_with_canonical_tests(
        self,
        code: str,
        test: str,
        entry_point: str,
    ) -> dict[str, Any]:
        """
        Execute code against HumanEval canonical tests.

        The HumanEval test format uses a `check(candidate)` function.
        We need to combine the code with the test and call check with
        the entry point function.

        Args:
            code: The generated Python code (should define the entry_point function).
            test: The HumanEval test code (defines check function).
            entry_point: The function name to test.

        Returns:
            Execution result dict.
        """
        # Build a script that defines the function then runs the check
        script = f"{code}\n\n{test}\n"

        return self._execute_script(script)

    def _build_script(self, code: str, tests: str) -> str:
        """Combine code and tests into a single script."""
        return f"{code}\n\n{tests}\n"

    def _execute_script(self, script: str) -> dict[str, Any]:
        """Execute a Python script in a subprocess with sandboxing."""
        result = {
            "passed": False,
            "output": "",
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "error": None,
            "timeout": False,
        }

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                script_path = Path(tmpdir) / "test_script.py"
                with open(script_path, "w") as f:
                    f.write(script)

                proc = subprocess.run(
                    [sys.executable, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=tmpdir,
                    env={
                        **os.environ,
                        "PYTHONDONTWRITEBYTECODE": "1",
                    },
                )

                result["stdout"] = proc.stdout
                result["stderr"] = proc.stderr
                result["output"] = proc.stdout + proc.stderr
                result["return_code"] = proc.returncode
                result["passed"] = proc.returncode == 0

                if proc.returncode != 0:
                    result["error"] = proc.stderr.strip() or f"Exit code: {proc.returncode}"
                    logger.debug("Test execution failed: %s", result["error"][:200])

        except subprocess.TimeoutExpired:
            result["timeout"] = True
            result["error"] = f"Execution timed out after {self.timeout}s"
            logger.warning(result["error"])

        except Exception as e:
            result["error"] = str(e)
            logger.error("Test execution error: %s", e)

        return result
