"""
Logging configuration for the experiment platform.

Sets up structured logging:
- Console output (configurable level)
- experiment.log (file)
- llm_calls.jsonl (structured LLM call logging)
- agent_messages.jsonl (inter-agent communication)
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def setup_logging(
    log_dir: str | Path = "logs",
    level: str = "INFO",
    experiment_name: str = "",
) -> None:
    """
    Configure logging for the experiment platform.

    Args:
        log_dir: Directory for log files.
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
        experiment_name: Name to include in log files.
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler using Rich
    try:
        from rich.logging import RichHandler
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=False,
            markup=True,
        )
        console_format = logging.Formatter("%(message)s")
    except ImportError:
        console_handler = logging.StreamHandler(sys.stdout)
        console_format = logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(
        log_dir / "experiment.log",
        mode="a",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)


class LLMCallLogger:
    """
    Structured logger for LLM API calls.

    Logs each call to a JSONL file for full traceability.
    """

    def __init__(self, log_path: str | Path) -> None:
        self._log_path = Path(log_path)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_call(
        self,
        run_id: str,
        agent: str,
        model: str,
        temperature: float,
        prompt: str,
        response: str,
        latency_ms: float,
        tokens_in: int = 0,
        tokens_out: int = 0,
        error: str | None = None,
        log_full_content: bool = True,
    ) -> None:
        """
        Log a single LLM call.

        Args:
            run_id: ID of the experiment run.
            agent: Name of the calling agent.
            model: Model name used.
            temperature: Temperature setting.
            prompt: Full prompt text.
            response: Full response text.
            latency_ms: Call latency in milliseconds.
            tokens_in: Input token count.
            tokens_out: Output token count.
            error: Error message if the call failed.
            log_full_content: If False, log only content hashes/lengths.
        """
        record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "agent": agent,
            "model": model,
            "temperature": temperature,
            "latency_ms": latency_ms,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "error": error,
        }

        if log_full_content:
            record["prompt"] = prompt
            record["response"] = response
        else:
            record["prompt_length"] = len(prompt)
            record["response_length"] = len(response)

        with open(self._log_path, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
