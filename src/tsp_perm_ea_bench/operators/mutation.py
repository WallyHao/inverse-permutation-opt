"""Permutation mutation operators."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class MutationResult:
    """A child and the move used to produce it."""

    tour: tuple[int, ...]
    applied: bool
    source_position: int | None = None
    insertion_position: int | None = None


def move_mutation(
    tour: Sequence[int],
    *,
    probability: float,
    rng: random.Random,
) -> MutationResult:
    """Apply one city move with a fixed probability.

    ``source_position`` and ``insertion_position`` are both positions in the
    original tour, and the latter is the final position after removal. Ordered
    pairs ``i != j`` are sampled uniformly.
    """

    if len(tour) < 3 or len(set(tour)) != len(tour):
        raise ValueError("move_mutation requires a legal permutation")
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0, 1]")
    original = tuple(tour)
    if rng.random() >= probability:
        return MutationResult(original, applied=False)

    source = rng.randrange(len(original))
    insertion = rng.randrange(len(original) - 1)
    if insertion >= source:
        insertion += 1
    remaining = list(original)
    city = remaining.pop(source)
    remaining.insert(insertion, city)
    result = tuple(remaining)
    if len(result) != len(original) or set(result) != set(original):
        raise AssertionError("move mutation produced an invalid permutation")
    return MutationResult(result, applied=True, source_position=source, insertion_position=insertion)
