"""Parent-selection operators for the steady-state protocol."""

from __future__ import annotations

import random
from typing import Sequence, TypeVar


T = TypeVar("T")


def inverse_tournament(
    population: Sequence[T],
    values: Sequence[int | float],
    *,
    tournament_size: int,
    rng: random.Random,
) -> int:
    """Select the longest tour among candidates sampled with replacement.

    The returned value is an individual index. Ties are resolved uniformly
    among the tied candidates, preserving individual identity even when tours
    have the same genotype.
    """

    if len(population) == 0:
        raise ValueError("population must not be empty")
    if len(population) != len(values):
        raise ValueError("population and values must have equal length")
    if tournament_size < 1:
        raise ValueError("tournament_size must be positive")
    candidates = [rng.randrange(len(population)) for _ in range(tournament_size)]
    worst_value = max(values[index] for index in candidates)
    tied = [index for index in candidates if values[index] == worst_value]
    return rng.choice(tied)


def random_parent_selection(population: Sequence[T], *, rng: random.Random) -> int:
    """Select a parent uniformly with replacement from the full population."""

    if not population:
        raise ValueError("population must not be empty")
    return rng.randrange(len(population))
