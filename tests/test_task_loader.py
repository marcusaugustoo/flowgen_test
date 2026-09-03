"""
Unit tests for the TaskLoader module.

Covers:
- Loading a single task from .txt
- Loading multiple tasks from a directory
- Empty file handling
- Missing file handling
- Missing directory handling
- Invalid extension handling
- Correct task_id derivation
- Task -> Problem conversion
- Companion test file detection
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.tasks.task import Task
from src.tasks.task_loader import TaskLoader


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def loader():
    """Create a TaskLoader instance."""
    return TaskLoader()


@pytest.fixture
def tasks_dir(tmp_path):
    """Create a temporary directory with sample task files."""
    # task_001.txt
    (tmp_path / "task_001.txt").write_text(
        "Implemente uma função chamada soma que receba dois inteiros e retorne a soma.",
        encoding="utf-8",
    )
    # task_002.txt
    (tmp_path / "task_002.txt").write_text(
        "Implemente uma função chamada fatorial que receba n e retorne n!.",
        encoding="utf-8",
    )
    # A non-.txt file (should be ignored)
    (tmp_path / "notes.md").write_text("This is a markdown file.", encoding="utf-8")

    return tmp_path


@pytest.fixture
def task_with_tests(tmp_path):
    """Create a task file with a companion test file."""
    (tmp_path / "task_prime.txt").write_text(
        "Implemente a função is_prime que retorne True se o número for primo.",
        encoding="utf-8",
    )
    (tmp_path / "task_prime_test.py").write_text(
        "def check(candidate):\n"
        "    assert candidate(2) == True\n"
        "    assert candidate(4) == False\n"
        "\ncheck(is_prime)\n",
        encoding="utf-8",
    )
    return tmp_path / "task_prime.txt"


@pytest.fixture
def empty_task(tmp_path):
    """Create an empty task file."""
    path = tmp_path / "empty.txt"
    path.write_text("", encoding="utf-8")
    return path


@pytest.fixture
def whitespace_task(tmp_path):
    """Create a task file with only whitespace."""
    path = tmp_path / "whitespace.txt"
    path.write_text("   \n  \n  ", encoding="utf-8")
    return path


# ─── Test: Load Single File ──────────────────────────────────────────────────


class TestLoadFile:
    """Tests for TaskLoader.load_file()."""

    def test_load_valid_file(self, loader, tasks_dir):
        """Load a valid .txt file and verify all fields."""
        task = loader.load_file(tasks_dir / "task_001.txt")

        assert task.task_id == "task_001"
        assert task.file_name == "task_001.txt"
        assert "soma" in task.description
        assert task.test_code == ""
        assert "source_path" in task.metadata

    def test_task_id_derived_from_filename(self, loader, tasks_dir):
        """task_id should be the file stem (name without extension)."""
        task = loader.load_file(tasks_dir / "task_002.txt")
        assert task.task_id == "task_002"

    def test_file_not_found(self, loader, tmp_path):
        """FileNotFoundError when file does not exist."""
        with pytest.raises(FileNotFoundError, match="not found"):
            loader.load_file(tmp_path / "nonexistent.txt")

    def test_invalid_extension(self, loader, tasks_dir):
        """ValueError when file has wrong extension."""
        with pytest.raises(ValueError, match="Invalid file extension"):
            loader.load_file(tasks_dir / "notes.md")

    def test_empty_file(self, loader, empty_task):
        """ValueError when file is empty."""
        with pytest.raises(ValueError, match="empty"):
            loader.load_file(empty_task)

    def test_whitespace_only_file(self, loader, whitespace_task):
        """ValueError when file contains only whitespace."""
        with pytest.raises(ValueError, match="empty"):
            loader.load_file(whitespace_task)

    def test_directory_as_file(self, loader, tasks_dir):
        """ValueError when path points to a directory."""
        with pytest.raises(ValueError, match="not a file"):
            loader.load_file(tasks_dir)

    def test_companion_test_loaded(self, loader, task_with_tests):
        """Companion _test.py file should be loaded as test_code."""
        task = loader.load_file(task_with_tests)

        assert task.task_id == "task_prime"
        assert "check(candidate)" in task.test_code
        assert "is_prime" in task.test_code

    def test_no_companion_test(self, loader, tasks_dir):
        """No test_code when companion file doesn't exist."""
        task = loader.load_file(tasks_dir / "task_001.txt")
        assert task.test_code == ""


# ─── Test: Load Directory ────────────────────────────────────────────────────


class TestLoadDirectory:
    """Tests for TaskLoader.load_directory()."""

    def test_load_all_tasks(self, loader, tasks_dir):
        """Load all .txt files from a directory."""
        tasks = loader.load_directory(tasks_dir)

        assert len(tasks) == 2
        ids = [t.task_id for t in tasks]
        assert "task_001" in ids
        assert "task_002" in ids

    def test_sorted_by_filename(self, loader, tasks_dir):
        """Tasks should be sorted alphabetically by filename."""
        tasks = loader.load_directory(tasks_dir)
        assert tasks[0].task_id == "task_001"
        assert tasks[1].task_id == "task_002"

    def test_ignores_non_txt_files(self, loader, tasks_dir):
        """Non-.txt files should be ignored."""
        tasks = loader.load_directory(tasks_dir)
        ids = [t.task_id for t in tasks]
        assert "notes" not in ids

    def test_directory_not_found(self, loader, tmp_path):
        """FileNotFoundError when directory does not exist."""
        with pytest.raises(FileNotFoundError, match="not found"):
            loader.load_directory(tmp_path / "nonexistent_dir")

    def test_not_a_directory(self, loader, tasks_dir):
        """ValueError when path is a file, not a directory."""
        with pytest.raises(ValueError, match="not a directory"):
            loader.load_directory(tasks_dir / "task_001.txt")

    def test_empty_directory(self, loader, tmp_path):
        """ValueError when directory has no .txt files."""
        empty_dir = tmp_path / "empty_dir"
        empty_dir.mkdir()
        with pytest.raises(ValueError, match="No .txt task files"):
            loader.load_directory(empty_dir)

    def test_skips_empty_files(self, loader, tmp_path):
        """Empty .txt files are skipped with a warning, valid ones still load."""
        (tmp_path / "good.txt").write_text("A valid task.", encoding="utf-8")
        (tmp_path / "bad.txt").write_text("", encoding="utf-8")

        tasks = loader.load_directory(tmp_path)
        assert len(tasks) == 1
        assert tasks[0].task_id == "good"


# ─── Test: Task -> Problem Conversion ────────────────────────────────────────


class TestTaskToProblem:
    """Tests for Task.to_problem()."""

    def test_basic_conversion(self):
        """Task converts to Problem with correct field mapping."""
        task = Task(
            task_id="task_test",
            file_name="task_test.txt",
            description="Implement a function called hello.",
        )
        problem = task.to_problem()

        assert problem.task_id == "task_test"
        assert problem.prompt == "Implement a function called hello."
        assert problem.entry_point == ""
        assert problem.test == ""
        assert problem.canonical_solution == ""

    def test_conversion_with_test_code(self):
        """Task with test_code converts to Problem with the test field populated."""
        task = Task(
            task_id="task_prime",
            file_name="task_prime.txt",
            description="Implement is_prime.",
            test_code="def check(c):\n    assert c(2) == True\ncheck(is_prime)\n",
        )
        problem = task.to_problem()

        assert problem.test == task.test_code
        assert "check" in problem.test
