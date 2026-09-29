"""CLI for validation and one-run execution."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ..algorithms.steady_state import (
    SteadyStateConfig,
    make_run_id,
    run_steady_state_ga,
)
from ..analysis.summarize import summarize_experiment
from ..core.config import ExperimentSpec
from ..observers.logger import RunLogger
from ..problems.registry import InstanceRegistry
from ..problems.tsp import ReferenceStatus, load_tsplib
from ..runner.batch import BatchRunner


def build_parser() -> argparse.ArgumentParser:
    """Build the public command-line parser."""

    parser = argparse.ArgumentParser(prog="tsp-perm-ea")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="run one steady-state GA task")
    run_parser.add_argument("--instance", type=Path, required=True)
    run_parser.add_argument("--instance-id", required=True)
    run_parser.add_argument("--output-directory", type=Path, required=True)
    run_parser.add_argument("--seed", type=int, required=True)
    run_parser.add_argument("--repeat", type=int, required=True)
    run_parser.add_argument("--crossover", choices=("ox", "pmx", "erx", "sax"), default="ox")
    run_parser.add_argument("--population-size", type=int, default=200)
    run_parser.add_argument("--inverse-tournament-size", type=int, default=2)
    run_parser.add_argument("--mutation-probability", type=float, default=0.05)
    run_parser.add_argument("--offspring-budget", type=int, default=500_000)
    run_parser.add_argument("--reference-value", type=int)
    run_parser.add_argument(
        "--reference-status",
        choices=tuple(status.value for status in ReferenceStatus),
        default=ReferenceStatus.UNKNOWN.value,
    )
    validate_parser = subparsers.add_parser("validate", help="validate a benchmark manifest")
    validate_parser.add_argument("--manifest", type=Path, required=True)
    plan_parser = subparsers.add_parser("plan", help="preview expanded experiment tasks")
    plan_parser.add_argument("--config", type=Path, required=True)
    batch_parser = subparsers.add_parser("batch", help="run an experiment specification")
    batch_parser.add_argument("--config", type=Path, required=True)
    batch_parser.add_argument("--output-root", type=Path)
    batch_parser.add_argument("--dry-run", action="store_true")
    summary_parser = subparsers.add_parser("summarize", help="analyze completed run artifacts")
    summary_parser.add_argument("--experiment-directory", type=Path, required=True)
    summary_parser.add_argument("--output-directory", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the selected CLI command."""

    arguments = build_parser().parse_args(argv)
    if arguments.command == "run":
        return _run(arguments)
    if arguments.command == "validate":
        registry = InstanceRegistry.from_manifest(arguments.manifest)
        print(json.dumps({"instances": registry.validate_all()}))
        return 0
    if arguments.command == "plan":
        spec = ExperimentSpec.from_file(arguments.config)
        registry = spec.validate()
        del registry
        print(
            json.dumps(
                {
                    "experiment_id": spec.experiment_id,
                    "task_count": len(spec.tasks()),
                    "runs": [
                        {
                            "run_id": spec.run_id(task),
                            "instance_id": task.instance_id,
                            "crossover": task.crossover,
                            "repeat": task.repeat,
                            "master_seed": task.master_seed,
                        }
                        for task in spec.tasks()
                    ],
                }
            )
        )
        return 0
    if arguments.command == "batch":
        spec = ExperimentSpec.from_file(arguments.config)
        if arguments.dry_run:
            spec.validate()
            print(
                json.dumps(
                    {
                        "experiment_id": spec.experiment_id,
                        "task_count": len(spec.tasks()),
                        "offspring_evaluations": len(spec.tasks()) * spec.offspring_budget,
                        "output_root": str(arguments.output_root or "results"),
                    }
                )
            )
            return 0
        repository_root = arguments.config.resolve().parents[1]
        runner = BatchRunner(
            spec,
            repository_root=repository_root,
            output_root=arguments.output_root,
        )
        tasks = runner.run()
        print(json.dumps({"experiment_id": spec.experiment_id, "tasks": tasks}))
        return 0
    if arguments.command == "summarize":
        output = summarize_experiment(
            arguments.experiment_directory,
            output_directory=arguments.output_directory,
        )
        print(json.dumps({"analysis_directory": str(output)}))
        return 0
    raise AssertionError(f"unhandled command: {arguments.command}")


def _run(arguments: argparse.Namespace) -> int:
    instance_bytes = arguments.instance.read_bytes()
    problem = load_tsplib(
        arguments.instance,
        reference_value=arguments.reference_value,
        reference_status=arguments.reference_status,
    )
    config = SteadyStateConfig(
        population_size=arguments.population_size,
        inverse_tournament_size=arguments.inverse_tournament_size,
        mutation_probability=arguments.mutation_probability,
        crossover=arguments.crossover,
        offspring_budget=arguments.offspring_budget,
    )
    run_id = make_run_id(
        instance_id=arguments.instance_id,
        repeat=arguments.repeat,
        master_seed=arguments.seed,
        config=config.as_dict(),
        protocol_version=config.protocol_version,
    )
    logger = RunLogger(arguments.output_directory / run_id)
    result = run_steady_state_ga(
        problem,
        config,
        master_seed=arguments.seed,
        instance_id=arguments.instance_id,
        repeat=arguments.repeat,
        observer=logger,
    )
    manifest = {
        "schema_version": "run-manifest-v1",
        "run_id": result.run_id,
        "instance_id": arguments.instance_id,
        "instance_path": str(arguments.instance),
        "instance_sha256": hashlib.sha256(instance_bytes).hexdigest(),
        "master_seed": arguments.seed,
        "repeat": arguments.repeat,
        "seed_schema_version": "seed-v1",
        "config": config.as_dict(),
        "problem": {
            "name": problem.name,
            "dimension": problem.n,
            "edge_weight_type": problem.edge_weight_type,
            "reference_status": problem.reference_status,
            "reference_value": problem.reference_value,
        },
    }
    best_tour = {
        "internal_tour": list(result.best_tour or ()),
        "original_tour": list(problem.to_original_tour(result.best_tour))
        if result.best_tour is not None
        else None,
        "length": result.best_value,
    }
    logger.write(result=result, manifest=manifest, best_tour=best_tour)
    print(json.dumps({"run_id": result.run_id, "termination_reason": result.termination_reason}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
