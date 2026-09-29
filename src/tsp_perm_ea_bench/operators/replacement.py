"""Steady-state replacement policies."""

from __future__ import annotations

import random
from typing import Sequence, TypeVar


T = TypeVar("T")


def replace_worst(
    population: Sequence[T],
    values: Sequence[int | float],
    child: T,
    child_value: int | float,
    *,
    rng: random.Random,
) -> tuple[list[T], list[int | float], int]:
    """Insert one child and remove one uniformly selected worst individual."""

    if not population:
        raise ValueError("population must not be empty")
    if len(population) != len(values):
        raise ValueError("population and values must have equal length")
    candidates = list(population) + [child]
    candidate_values = list(values) + [child_value]
    worst_value = max(candidate_values)
    worst_indices = [
        index for index, value in enumerate(candidate_values) if value == worst_value
    ]
    removed_index = rng.choice(worst_indices)
    del candidates[removed_index]
    del candidate_values[removed_index]
    return candidates, candidate_values, removed_index
