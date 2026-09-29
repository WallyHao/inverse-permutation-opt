"""The common ``(mu+1)`` steady-state GA execution framework."""

from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

from ..core.budget import (
    BudgetExceeded,
    EvaluationContext,
    EvaluationPhase,
    TerminationReason,
)
from ..core.randomness import SeedDerivation
from ..observers.events import Event, Observer
from ..operators.crossover import crossover
from ..operators.mutation import move_mutation
from ..operators.replacement import replace_worst
from ..operators.selection import inverse_tournament, random_parent_selection
from ..problems.metrics import (
    edge_retention,
    exact_population_edge_distance,
    position_retention,
)
from ..problems.tsp import TSPProblem


@dataclass(frozen=True)
class SteadyStateConfig:
    """Explicit parameters for one controlled steady-state GA run."""

    population_size: int = 200
    inverse_tournament_size: int = 2
    mutation_probability: float = 0.05
    crossover: str = "ox"
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
    protocol_version: str = "steady-state-ga-v1"

    def __post_init__(self) -> None:
        if self.population_size < 1:
            raise ValueError("population_size must be positive")
        if self.inverse_tournament_size < 1:
            raise ValueError("inverse_tournament_size must be positive")
        if not 0.0 <= self.mutation_probability <= 1.0:
            raise ValueError("mutation_probability must be in [0, 1]")
        if self.offspring_budget < 0:
            raise ValueError("offspring_budget must be non-negative")
        if any(point < 1 for point in self.checkpoint_evaluations):
            raise ValueError("checkpoint_evaluations must contain positive values")
        if tuple(sorted(set(self.checkpoint_evaluations))) != self.checkpoint_evaluations:
            raise ValueError("checkpoint_evaluations must be sorted and unique")
        if self.crossover not in {"ox", "pmx", "erx", "sax"}:
            raise ValueError(f"unsupported crossover: {self.crossover}")

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible configuration mapping."""

        return asdict(self)


@dataclass(frozen=True)
class RunResult:
    """Logical result and final state of one run."""

    run_id: str
    instance_id: str
    repeat: int
    master_seed: int
    termination_reason: str
    best_value: int | float | None
    best_tour: tuple[int, ...] | None
    counters: dict[str, int]
    initial_population_hash: str
    population_edge_distance: float | None
    config: dict[str, Any]
    wall_time: float = field(compare=False)
    process_cpu_time: float = field(compare=False)


@dataclass
class _Individual:
    identity: int
    tour: tuple[int, ...]
    value: int | float


def run_steady_state_ga(
    problem: TSPProblem,
    config: SteadyStateConfig,
    *,
    master_seed: int,
    instance_id: str,
    repeat: int,
    observer: Observer | None = None,
) -> RunResult:
    """Run one paired, auditable steady-state GA instance."""

    if repeat < 0:
        raise ValueError("repeat must be non-negative")
    observer = observer or _NullObserver()
    seeds = SeedDerivation(master_seed, instance_id, repeat)
    initialization_rng = random.Random(seeds.seed("initialization"))
    selection_rng = random.Random(seeds.seed("selection"))
    crossover_rng = random.Random(seeds.seed("crossover"))
    mutation_rng = random.Random(seeds.seed("mutation"))
    replacement_rng = random.Random(seeds.seed("replacement"))
    context = EvaluationContext(
        problem,
        offspring_budget=config.offspring_budget,
        stop_at_proven_optimum=config.stop_at_proven_optimum,
    )

    population: list[_Individual] = []
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    next_identity = 0
    initial_tours: list[tuple[int, ...]] = []
    try:
        for _ in range(config.population_size):
            tour = list(range(problem.n))
            initialization_rng.shuffle(tour)
            tour_tuple = tuple(tour)
            result = context.evaluate(tour_tuple, phase=EvaluationPhase.INITIALIZATION)
            population.append(_Individual(next_identity, tour_tuple, result.value))
            initial_tours.append(tour_tuple)
            next_identity += 1
        initial_hash = _hash_tours(initial_tours)
        _emit_checkpoint(observer, context, population, iteration=0, label="initialization")
        if (
            config.stop_at_proven_optimum
            and problem.reference_status == "proven_optimum"
            and problem.reference_value is not None
            and context.best_value == problem.reference_value
        ):
            context.termination_reason = TerminationReason.OPTIMUM_REACHED

        while context.termination_reason is None:
            values = [individual.value for individual in population]
            first_index = inverse_tournament(
                population,
                values,
                tournament_size=config.inverse_tournament_size,
                rng=selection_rng,
            )
            second_index = random_parent_selection(population, rng=selection_rng)
            first = population[first_index]
            second = population[second_index]
            crossover_result = crossover(
                config.crossover,
                first.tour,
                second.tour,
                rng=crossover_rng,
            )
            mutation_result = move_mutation(
                crossover_result.child,
                probability=config.mutation_probability,
                rng=mutation_rng,
            )
            before_best = context.best_value
            evaluation = context.evaluate(
                mutation_result.tour,
                phase=EvaluationPhase.OFFSPRING,
            )
            child = _Individual(next_identity, mutation_result.tour, evaluation.value)
            next_identity += 1
            population, _, _ = replace_worst(
                population,
                values,
                child,
                child.value,
                rng=replacement_rng,
            )
            context.counters.iterations += 1
            observer.on_event(
                Event.from_context(
                    "offspring",
                    context,
                    iteration=context.counters.iterations,
                    payload={
                        "crossover": crossover_result.operator,
                        "delegate": crossover_result.delegate,
                        "parent_edge_distance": crossover_result.parent_edge_distance,
                        "parent_one_identity": first.identity,
                        "parent_two_identity": second.identity,
                        "child_value": evaluation.value,
                        "mutation_applied": mutation_result.applied,
                        "edge_retention": edge_retention(
                            crossover_result.child, first.tour, second.tour
                        ),
                        "position_retention": position_retention(
                            crossover_result.child, first.tour, second.tour
                        ),
                    },
                )
            )
            if before_best is None or evaluation.best_value < before_best:
                observer.on_event(
                    Event.from_context(
                        "improvement",
                        context,
                        iteration=context.counters.iterations,
                        payload={
                            "best_value": evaluation.best_value,
                            "tour": list(context.best_tour or ()),
                        },
                    )
                )
            if context.exhausted:
                context.finish_if_budget_exhausted()
            if (
                context.counters.offspring_evaluations in config.checkpoint_evaluations
                or context.exhausted
            ):
                _emit_checkpoint(
                    observer,
                    context,
                    population,
                    iteration=context.counters.iterations,
                    label="terminal" if context.exhausted else "progress",
                )
    except BudgetExceeded:
        if context.termination_reason is None:
            context.termination_reason = TerminationReason.BUDGET_EXHAUSTED
    except KeyboardInterrupt:
        context.termination_reason = TerminationReason.INTERRUPTED
    except Exception:
        context.termination_reason = TerminationReason.FAILED
        raise

    if context.termination_reason is None:
        context.termination_reason = TerminationReason.COMPLETED
    final_distance = exact_population_edge_distance(
        [individual.tour for individual in population]
    )
    config_dict = config.as_dict()
    run_id = make_run_id(
        instance_id=instance_id,
        repeat=repeat,
        master_seed=master_seed,
        config=config_dict,
        protocol_version=config.protocol_version,
    )
    result = RunResult(
        run_id=run_id,
        instance_id=instance_id,
        repeat=repeat,
        master_seed=master_seed,
        termination_reason=context.termination_reason.value,
        best_value=context.best_value,
        best_tour=context.best_tour,
        counters=asdict(context.counters),
        initial_population_hash=initial_hash,
        population_edge_distance=final_distance,
        config=config_dict,
        wall_time=time.perf_counter() - wall_start,
        process_cpu_time=time.process_time() - cpu_start,
    )
    observer.on_event(
        Event.from_context(
            "termination",
            context,
            iteration=context.counters.iterations,
            payload={
                "reason": result.termination_reason,
                "best_value": result.best_value,
            },
        )
    )
    return result


def make_run_id(
    *,
    instance_id: str,
    repeat: int,
    master_seed: int,
    config: dict[str, Any],
    protocol_version: str,
) -> str:
    """Create a stable identity from normalized run inputs."""

    payload = json.dumps(
        [protocol_version, instance_id, repeat, master_seed, config],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _hash_tours(tours: Sequence[Sequence[int]]) -> str:
    payload = json.dumps([list(tour) for tour in tours], separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _emit_checkpoint(
    observer: Observer,
    context: EvaluationContext,
    population: Sequence[_Individual],
    *,
    iteration: int,
    label: str,
) -> None:
    values = [individual.value for individual in population]
    observer.on_event(
        Event.from_context(
            "checkpoint",
            context,
            iteration=iteration,
            payload={
                "label": label,
                "population_best": min(values),
                "population_mean": sum(values) / len(values),
                "global_best": context.best_value,
                "global_best_tour": list(context.best_tour or ()),
                "population_edge_distance": exact_population_edge_distance(
                    [individual.tour for individual in population]
                ),
                "population_size": len(population),
            },
        )
    )


class _NullObserver:
    def on_event(self, event: Event) -> None:
        del event
