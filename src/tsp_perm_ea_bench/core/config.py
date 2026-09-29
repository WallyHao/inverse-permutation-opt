"""Frozen experiment specifications and deterministic task expansion."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..problems.registry import InstanceRegistry
from ..problems.tsp import TSPProblem
from ..algorithms.steady_state import SteadyStateConfig, make_run_id


@dataclass(frozen=True)
class Replicate:
    """One explicit repeat and master seed pair."""

    repeat: int
    master_seed: int


@dataclass(frozen=True)
class RunTask:
    """One instance, operator, and replicate combination."""

    instance_id: str
    crossover: str
    repeat: int
    master_seed: int


@dataclass(frozen=True)
class ExperimentSpec:
    """A versioned, JSON-serializable experiment definition."""

    experiment_id: str
    benchmark_manifest: Path
    instance_ids: tuple[str, ...]
    crossovers: tuple[str, ...]
    replicates: tuple[Replicate, ...]
    population_size: int = 200
    inverse_tournament_size: int = 2
    mutation_probability: float = 0.05
    offspring_budget: int = 500_000
    stop_at_proven_optimum: bool = True
    checkpoint_evaluations: tuple[int, ...] = (
        1,
        10,
        100,
        1_000,
        10_000,
        100_000,
        500_000,
    )
    schema_version: str = "experiment-spec-v1"

    def __post_init__(self) -> None:
        if not self.experiment_id:
            raise ValueError("experiment_id must not be empty")
        if not self.instance_ids or len(set(self.instance_ids)) != len(self.instance_ids):
            raise ValueError("instance_ids must be a non-empty unique sequence")
        if not self.crossovers or any(name not in {"ox", "pmx", "erx", "sax"} for name in self.crossovers):
            raise ValueError("crossovers must be chosen from ox, pmx, erx, sax")
        if len(set(self.crossovers)) != len(self.crossovers):
            raise ValueError("crossovers must be unique")
        if not self.replicates or len({item.repeat for item in self.replicates}) != len(self.replicates):
            raise ValueError("replicates must contain unique repeat identifiers")
        if any(item.repeat < 0 for item in self.replicates):
            raise ValueError("repeat identifiers must be non-negative")
        if self.population_size < 1 or self.inverse_tournament_size < 1:
            raise ValueError("population and tournament sizes must be positive")
        if not 0.0 <= self.mutation_probability <= 1.0:
            raise ValueError("mutation_probability must be in [0, 1]")
        if self.offspring_budget < 0:
            raise ValueError("offspring_budget must be non-negative")

    @classmethod
    def from_file(cls, path: str | Path) -> "ExperimentSpec":
        """Read a JSON experiment specification and resolve its manifest path."""

        source = Path(path)
        document = json.loads(source.read_text(encoding="utf-8"))
        if document.get("schema_version") != "experiment-spec-v1":
            raise ValueError("unsupported experiment specification schema")
        replicates = tuple(
            Replicate(int(item["repeat"]), int(item["master_seed"]))
            for item in document["replicates"]
        )
        manifest = Path(document["benchmark_manifest"])
        if not manifest.is_absolute():
            manifest = (source.parent / manifest).resolve()
        return cls(
            experiment_id=str(document["experiment_id"]),
            benchmark_manifest=manifest,
            instance_ids=tuple(str(item) for item in document["instance_ids"]),
            crossovers=tuple(str(item) for item in document["crossovers"]),
            replicates=replicates,
            population_size=int(document.get("population_size", 200)),
            inverse_tournament_size=int(document.get("inverse_tournament_size", 2)),
            mutation_probability=float(document.get("mutation_probability", 0.05)),
            offspring_budget=int(document.get("offspring_budget", 500_000)),
            stop_at_proven_optimum=bool(document.get("stop_at_proven_optimum", True)),
            checkpoint_evaluations=tuple(
                int(item)
                for item in document.get(
                    "checkpoint_evaluations",
                    [1, 10, 100, 1_000, 10_000, 100_000, 500_000],
                )
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        """Return a normalized JSON-compatible specification."""

        data = asdict(self)
        data["benchmark_manifest"] = str(self.benchmark_manifest)
        data["replicates"] = [asdict(item) for item in self.replicates]
        data["instance_ids"] = list(self.instance_ids)
        data["crossovers"] = list(self.crossovers)
        data["checkpoint_evaluations"] = list(self.checkpoint_evaluations)
        return data

    def validate(self, registry: InstanceRegistry | None = None) -> InstanceRegistry:
        """Validate config values and all selected benchmark sources."""

        active_registry = registry or InstanceRegistry.from_manifest(self.benchmark_manifest)
        for instance_id in self.instance_ids:
            active_registry.load(instance_id)
        SteadyStateConfig(
            population_size=self.population_size,
            inverse_tournament_size=self.inverse_tournament_size,
            mutation_probability=self.mutation_probability,
            offspring_budget=self.offspring_budget,
            stop_at_proven_optimum=self.stop_at_proven_optimum,
            checkpoint_evaluations=self.checkpoint_evaluations,
        )
        return active_registry

    def tasks(self) -> tuple[RunTask, ...]:
        """Expand the Cartesian product in declared order."""

        return tuple(
            RunTask(
                instance_id=instance_id,
                crossover=crossover,
                repeat=replicate.repeat,
                master_seed=replicate.master_seed,
            )
            for instance_id in self.instance_ids
            for crossover in self.crossovers
            for replicate in self.replicates
        )

    def run_config(self, task: RunTask) -> SteadyStateConfig:
        """Build the algorithm config for one expanded task."""

        return SteadyStateConfig(
            population_size=self.population_size,
            inverse_tournament_size=self.inverse_tournament_size,
            mutation_probability=self.mutation_probability,
            crossover=task.crossover,
            offspring_budget=self.offspring_budget,
            stop_at_proven_optimum=self.stop_at_proven_optimum,
            checkpoint_evaluations=self.checkpoint_evaluations,
        )

    def run_id(self, task: RunTask) -> str:
        """Return the stable run identity for one task."""

        config = self.run_config(task)
        return make_run_id(
            instance_id=task.instance_id,
            repeat=task.repeat,
            master_seed=task.master_seed,
            config=config.as_dict(),
            protocol_version=config.protocol_version,
        )
