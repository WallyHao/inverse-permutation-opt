"""Structural metrics for legal symmetric-TSP tours and populations."""

from __future__ import annotations

from collections import Counter
from math import comb
from typing import Iterable, Sequence


Edge = tuple[int, int]


def canonical_edge(source: int, target: int) -> Edge:
    """Return an undirected edge in canonical endpoint order."""

    return (source, target) if source < target else (target, source)


def edge_set(tour: Sequence[int]) -> frozenset[Edge]:
    """Return the closed undirected edge set of a legal tour."""

    if len(tour) < 3 or len(set(tour)) != len(tour):
        raise ValueError("edge_set requires a legal permutation of at least three cities")
    return frozenset(
        canonical_edge(tour[index], tour[(index + 1) % len(tour)])
        for index in range(len(tour))
    )


def edge_distance(first: Sequence[int], second: Sequence[int]) -> float:
    """Return ``1 - shared_edges / n`` for two tours of equal size."""

    if len(first) != len(second):
        raise ValueError("tours must have equal size")
    return 1.0 - len(edge_set(first) & edge_set(second)) / len(first)


def edge_retention(child: Sequence[int], first: Sequence[int], second: Sequence[int]) -> float:
    """Return the child edge fraction inherited from either parent."""

    inherited = edge_set(first) | edge_set(second)
    return len(edge_set(child) & inherited) / len(child)


def position_retention(child: Sequence[int], first: Sequence[int], second: Sequence[int]) -> float:
    """Return the fraction of positions matching at least one parent."""

    if not (len(child) == len(first) == len(second)):
        raise ValueError("tours must have equal size")
    return sum(
        child[index] in {first[index], second[index]} for index in range(len(child))
    ) / len(child)


def exact_population_edge_distance(population: Iterable[Sequence[int]]) -> float | None:
    """Compute mean pairwise edge distance, or ``None`` for fewer than two tours."""

    tours = list(population)
    if len(tours) < 2:
        return None
    counts: Counter[Edge] = Counter()
    for tour in tours:
        counts.update(edge_set(tour))
    n = len(tours[0])
    if any(len(tour) != n for tour in tours):
        raise ValueError("population tours must have equal size")
    shared_pairs = sum(comb(count, 2) for count in counts.values())
    return 1.0 - shared_pairs / (n * comb(len(tours), 2))
