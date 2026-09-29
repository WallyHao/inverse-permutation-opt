"""Simple reference algorithms used to validate the experiment platform."""

from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import asdict

from ..core.budget import EvaluationContext, EvaluationPhase, TerminationReason
from ..core.randomness import SeedDerivation
from ..observers.events import Event, Observer
from .steady_state import RunResult, make_run_id
from ..problems.tsp import TSPProblem


def run_random_search(
    problem: TSPProblem,
    *,
    offspring_budget: int,
    master_seed: int,
    instance_id: str,
    repeat: int,
    stop_at_proven_optimum: bool = True,
    checkpoint_evaluations: tuple[int, ...] = (1, 10, 100, 1_000, 10_000),
    observer: Observer | None = None,
) -> RunResult:
    """Sample independent random tours as a platform-level sanity baseline."""

    if offspring_budget < 0:
        raise ValueError("offspring_budget must be non-negative")
    observer = observer or _NullObserver()
    context = EvaluationContext(
        problem,
        offspring_budget=offspring_budget,
        stop_at_proven_optimum=stop_at_proven_optimum,
    )
    rng = random.Random(SeedDerivation(master_seed, instance_id, repeat).seed("random_search"))
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    while context.termination_reason is None:
        tour = list(range(problem.n))
        rng.shuffle(tour)
        before_best = context.best_value
        evaluation = context.evaluate(tuple(tour), phase=EvaluationPhase.OFFSPRING)
        context.counters.iterations += 1
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
        if (
            context.counters.offspring_evaluations in checkpoint_evaluations
            or context.exhausted
        ):
            observer.on_event(
                Event.from_context(
                    "checkpoint",
                    context,
                    iteration=context.counters.iterations,
                    payload={
                        "label": "terminal" if context.exhausted else "progress",
                        "population_best": None,
                        "population_mean": None,
                        "global_best": context.best_value,
                        "global_best_tour": list(context.best_tour or ()),
                        "population_edge_distance": None,
                        "population_size": 0,
                    },
                )
            )
        if context.exhausted:
            context.finish_if_budget_exhausted()
    config = {
        "algorithm_id": "random_search",
        "offspring_budget": offspring_budget,
        "stop_at_proven_optimum": stop_at_proven_optimum,
        "checkpoint_evaluations": list(checkpoint_evaluations),
    }
    run_id = make_run_id(
        instance_id=instance_id,
        repeat=repeat,
        master_seed=master_seed,
        config=config,
        protocol_version="random-search-v1",
    )
    result = RunResult(
        run_id=run_id,
        instance_id=instance_id,
        repeat=repeat,
        master_seed=master_seed,
        termination_reason=(context.termination_reason or TerminationReason.COMPLETED).value,
        best_value=context.best_value,
        best_tour=context.best_tour,
        counters=asdict(context.counters),
        initial_population_hash=_hash_empty_population(),
        population_edge_distance=None,
        config=config,
        wall_time=time.perf_counter() - wall_start,
        process_cpu_time=time.process_time() - cpu_start,
    )
    observer.on_event(
        Event.from_context(
            "termination",
            context,
            iteration=context.counters.iterations,
            payload={"reason": result.termination_reason, "best_value": result.best_value},
        )
    )
    return result


def _hash_empty_population() -> str:
    return hashlib.sha256(json.dumps([]).encode("utf-8")).hexdigest()


class _NullObserver:
    def on_event(self, event: Event) -> None:
        del event
