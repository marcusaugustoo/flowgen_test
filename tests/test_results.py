"""Tests for the result store."""

import tempfile
from pathlib import Path

import pytest

from src.results.result_store import ResultStore


class TestResultStore:
    """Tests for ResultStore."""

    def test_initialize_experiment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(output_dir=tmpdir)
            exp_id = store.initialize_experiment(
                experiment_name="test_exp",
                config_dict={"experiment": {"name": "test"}},
            )
            assert exp_id.startswith("EXP-")
            assert store.experiment_dir is not None
            assert (store.experiment_dir / "config.yaml").exists()
            assert (store.experiment_dir / "runs").is_dir()
            assert (store.experiment_dir / "logs").is_dir()

    def test_save_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(output_dir=tmpdir)
            store.initialize_experiment("test", {"config": "value"})
            run_dir = store.save_run(
                run_number=1,
                results={"pass_at_1": 0.5, "passed": 3, "failed": 2},
                messages=[{"sender": "a", "receiver": "b"}],
            )
            assert (run_dir / "results.json").exists()
            assert (run_dir / "messages.jsonl").exists()

    def test_save_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(output_dir=tmpdir)
            store.initialize_experiment("test", {})
            summary_path = store.save_summary({"mean_pass_at_1": 0.6})
            assert summary_path.exists()

    def test_experiment_id_increment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store1 = ResultStore(output_dir=tmpdir)
            id1 = store1.initialize_experiment("exp1", {})
            store2 = ResultStore(output_dir=tmpdir)
            id2 = store2.initialize_experiment("exp2", {})
            assert id1 == "EXP-001"
            assert id2 == "EXP-002"

    def test_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(output_dir=tmpdir)
            store.initialize_experiment("exp", {})
            store.save_run(1, {"run": 1})
            store.save_run(2, {"run": 2})
            runs_dir = store.experiment_dir / "runs"
            assert (runs_dir / "run_001").exists()
            assert (runs_dir / "run_002").exists()
