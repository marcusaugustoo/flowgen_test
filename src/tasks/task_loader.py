"""
Task loader for .txt files.

Reads programming tasks from plain text files and converts them to Task objects.
Supports loading a single file or all .txt files from a directory.

Usage:
    loader = TaskLoader()
    task = loader.load_file("tasks/task_001.txt")
    tasks = loader.load_directory("tasks/")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from src.tasks.task import Task

logger = logging.getLogger(__name__)


class TaskLoader:
    """
    Loads programming tasks from .txt files.

    Features:
    - Load a single .txt file into a Task
    - Load all .txt files from a directory
    - Automatic detection of companion test files (task_001_test.py)
    - Validation: empty files, missing files, invalid extensions, duplicates
    """

    VALID_EXTENSIONS = {".txt"}

    def load_file(self, path: str | Path) -> Task:
        """
        Load a single task from a .txt file.

        Args:
            path: Path to the .txt file.

        Returns:
            A Task object with the file content as description.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file has an invalid extension or is empty.
            OSError: If the file cannot be read.
        """
        path = Path(path)

        # Validate existence
        if not path.exists():
            raise FileNotFoundError(f"Task file not found: {path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # Validate extension
        if path.suffix.lower() not in self.VALID_EXTENSIONS:
            raise ValueError(
                f"Invalid file extension '{path.suffix}' for task file: {path}. "
                f"Expected: {', '.join(self.VALID_EXTENSIONS)}"
            )

        # Read content
        try:
            content = path.read_text(encoding="utf-8").strip()
        except Exception as e:
            raise OSError(f"Error reading task file '{path}': {e}") from e

        # Validate non-empty
        if not content:
            raise ValueError(f"Task file is empty: {path}")

        # Derive task_id from file name (e.g., 'task_001.txt' -> 'task_001')
        task_id = path.stem

        # Check for companion test file (e.g., task_001_test.py)
        test_code = self._load_companion_tests(path)

        task = Task(
            task_id=task_id,
            file_name=path.name,
            description=content,
            test_code=test_code,
            metadata={"source_path": str(path.resolve())},
        )

        logger.info("Loaded task '%s' from %s", task_id, path)
        return task

    def load_directory(self, directory: str | Path) -> list[Task]:
        """
        Load all .txt tasks from a directory.

        Files are loaded in alphabetical order. Duplicate task IDs
        (same file stem) are detected and raise an error.

        Args:
            directory: Path to the directory containing .txt files.

        Returns:
            List of Task objects, sorted by task_id.

        Raises:
            FileNotFoundError: If the directory does not exist.
            ValueError: If no .txt files are found or duplicates exist.
        """
        directory = Path(directory)

        # Validate existence
        if not directory.exists():
            raise FileNotFoundError(f"Tasks directory not found: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        # Find all .txt files
        txt_files = sorted(
            f for f in directory.iterdir()
            if f.is_file() and f.suffix.lower() in self.VALID_EXTENSIONS
        )

        if not txt_files:
            raise ValueError(
                f"No .txt task files found in directory: {directory}"
            )

        # Load tasks and check for duplicates
        tasks: list[Task] = []
        seen_ids: set[str] = set()

        for txt_file in txt_files:
            try:
                task = self.load_file(txt_file)
            except (ValueError, OSError) as e:
                logger.warning("Skipping file '%s': %s", txt_file, e)
                continue

            if task.task_id in seen_ids:
                raise ValueError(
                    f"Duplicate task_id '{task.task_id}' found. "
                    f"Each .txt file must have a unique name."
                )

            seen_ids.add(task.task_id)
            tasks.append(task)

        if not tasks:
            raise ValueError(
                f"No valid task files could be loaded from: {directory}"
            )

        logger.info(
            "Loaded %d tasks from %s",
            len(tasks),
            directory,
        )
        return tasks

    def _load_companion_tests(self, task_path: Path) -> str:
        """
        Look for a companion test file next to the task file.

        If task_001.txt exists, looks for task_001_test.py in the same
        directory and loads its content as canonical test code.

        Args:
            task_path: Path to the .txt task file.

        Returns:
            Test code string, or empty string if no companion test found.
        """
        test_file = task_path.parent / f"{task_path.stem}_test.py"

        if test_file.exists() and test_file.is_file():
            try:
                test_code = test_file.read_text(encoding="utf-8").strip()
                if test_code:
                    logger.info(
                        "Found companion test file for '%s': %s",
                        task_path.stem,
                        test_file.name,
                    )
                    return test_code
            except Exception as e:
                logger.warning(
                    "Error reading companion test file '%s': %s",
                    test_file, e,
                )

        return ""
