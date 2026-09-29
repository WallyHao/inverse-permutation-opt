"""Sequential batch execution with stable task identities and retry history."""

from __future__ import annotations

import hashlib
import json
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..core.config import ExperimentSpec, RunTask
from ..core.provenance import collect_provenance
from ..observers.logger import RunLogger
from ..problems.registry import InstanceRegistry
from ..algorithms.steady_state import run_steady_state_ga


class BatchRunner:
    """Prepare and execute all tasks in an experiment specification."""

    def __init__(
        self,
        spec: ExperimentSpec,
        *,
        repository_root: str | Path,
        output_root: str | Path | None = None,
    ) -> None:
        self.spec = spec
        self.repository_root = Path(repository_root)
        self.registry = spec.validate()
        root = self.repository_root / "results" if output_root is None else Path(output_root)
        self.experiment_directory = root / spec.experiment_id

    def prepare(self) -> list[dict[str, Any]]:
        """Write frozen experiment metadata and return its task manifest."""

        self.experiment_directory.mkdir(parents=True, exist_ok=True)
        _atomic_json(self.experiment_directory / "experiment.json", self.spec.as_dict())
        path = self.experiment_directory / "task_manifest.json"
        existing = _read_json(path) if path.exists() else None
        previous = {
            item["run_id"]: item for item in (existing or {}).get("tasks", [])
        }
        tasks: list[dict[str, Any]] = []
        for task in self.spec.tasks():
            run_id = self.spec.run_id(task)
            item = {
                "run_id": run_id,
                "instance_id": task.instance_id,
                "crossover": task.crossover,
                "repeat": task.repeat,
                "master_seed": task.master_seed,
                "status": previous.get(run_id, {}).get("status", "pending"),
                "attempt_id": previous.get(run_id, {}).get("attempt_id"),
            }
            tasks.append(item)
        manifest = {
            "schema_version": "task-manifest-v1",
            "experiment_id": self.spec.experiment_id,
            "expected_task_count": len(tasks),
            "tasks": tasks,
        }
        _atomic_json(path, manifest)
        return tasks

    def run(self) -> list[dict[str, Any]]:
        """Execute pending tasks and retain each failed attempt."""

        tasks = self.prepare()
        task_by_id = {item["run_id"]: item for item in tasks}
        for task in self.spec.tasks():
            run_id = self.spec.run_id(task)
            item = task_by_id[run_id]
            run_root = self.experiment_directory / "runs" / run_id
            if _has_complete_attempt(run_root, run_id):
                item["status"] = "success"
                continue
            attempt_id = _next_attempt_id(run_root)
            attempt_directory = run_root / attempt_id
            attempt_directory.mkdir(parents=True, exist_ok=False)
            item["attempt_id"] = attempt_id
            try:
                problem = self.registry.load(task.instance_id)
                config = self.spec.run_config(task)
                logger = RunLogger(attempt_directory)
                result = run_steady_state_ga(
                    problem,
                    config,
                    master_seed=task.master_seed,
                    instance_id=task.instance_id,
                    repeat=task.repeat,
                    observer=logger,
                )
                source_bytes = self.registry.get(task.instance_id).file.read_bytes()
                manifest = {
                    "schema_version": "run-manifest-v1",
                    "run_id": result.run_id,
                    "experiment_id": self.spec.experiment_id,
                    "instance_id": task.instance_id,
                    "instance_sha256": hashlib.sha256(source_bytes).hexdigest(),
                    "master_seed": task.master_seed,
                    "repeat": task.repeat,
                    "seed_schema_version": "seed-v1",
                    "config": config.as_dict(),
                    "problem": {
                        "name": problem.name,
                        "dimension": problem.n,
                        "edge_weight_type": problem.edge_weight_type,
                        "reference_status": problem.reference_status,
                        "reference_value": problem.reference_value,
                    },
                    "provenance": collect_provenance(self.repository_root),
                }
                best_tour = {
                    "internal_tour": list(result.best_tour or ()),
                    "original_tour": (
                        list(problem.to_original_tour(result.best_tour))
                        if result.best_tour is not None
                        else None
                    ),
                    "length": result.best_value,
                }
                logger.write(result=result, manifest=manifest, best_tour=best_tour)
                item["status"] = "success"
            except Exception as error:
                _atomic_json(
                    attempt_directory / "error.json",
                    {
                        "schema_version": "error-v1",
                        "run_id": run_id,
                        "error_type": type(error).__name__,
                        "message": str(error),
                        "traceback": traceback.format_exc(),
                    },
                )
                item["status"] = "failed"
            _write_task_manifest(self.experiment_directory, tasks)
        _write_task_manifest(self.experiment_directory, tasks)
        return tasks


def _has_complete_attempt(run_root: Path, run_id: str) -> bool:
    if not run_root.exists():
        return False
    for attempt in sorted(run_root.glob("attempt-*")):
        marker = attempt / "complete.json"
        if not marker.is_file():
            continue
        try:
            data = _read_json(marker)
            summary = _read_json(attempt / "summary.json")
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("run_id") == run_id and summary.get("run_id") == run_id:
            return True
    return False


def _next_attempt_id(run_root: Path) -> str:
    existing = [
        int(path.name.split("-")[-1])
        for path in run_root.glob("attempt-*")
        if path.name.split("-")[-1].isdigit()
    ] if run_root.exists() else []
    return f"attempt-{max(existing, default=0) + 1:04d}"


def _write_task_manifest(experiment_directory: Path, tasks: list[dict[str, Any]]) -> None:
    _atomic_json(
        experiment_directory / "task_manifest.json",
        {
            "schema_version": "task-manifest-v1",
            "experiment_id": experiment_directory.name,
            "expected_task_count": len(tasks),
            "tasks": tasks,
        },
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)
