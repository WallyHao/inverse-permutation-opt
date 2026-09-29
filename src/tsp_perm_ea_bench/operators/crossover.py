"""Permutation crossovers used by the first experiment matrix."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Sequence

from ..problems.metrics import edge_distance, edge_set


@dataclass(frozen=True)
class CrossoverResult:
    """One legal child and mechanism data that is free to observe."""

    child: tuple[int, ...]
    operator: str
    parent_edge_distance: float | None = None
    delegate: str | None = None


def _cut_points(length: int, rng: random.Random) -> tuple[int, int]:
    if length < 3:
        raise ValueError("crossover requires tours with at least three cities")
    left = rng.randrange(length - 1)
    right = rng.randrange(left + 1, length)
    return left, right


def ordered_crossover(
    first: Sequence[int], second: Sequence[int], *, rng: random.Random
) -> CrossoverResult:
    """Copy a segment from parent one and fill remaining positions from parent two."""

    _validate_parents(first, second)
    left, right = _cut_points(len(first), rng)
    child: list[int | None] = [None] * len(first)
    child[left : right + 1] = first[left : right + 1]
    used = set(child[left : right + 1])
    fill = [city for city in second if city not in used]
    fill_index = 0
    for index in list(range(right + 1, len(first))) + list(range(0, left)):
        child[index] = fill[fill_index]
        fill_index += 1
    result = tuple(city for city in child if city is not None)
    _validate_child(result, first)
    return CrossoverResult(result, operator="ox")


def _pmx_child(
    first: Sequence[int], second: Sequence[int], left: int, right: int
) -> tuple[int, ...]:
    child: list[int | None] = [None] * len(first)
    child[left : right + 1] = first[left : right + 1]
    first_segment = set(first[left : right + 1])
    for index, city in enumerate(second):
        if left <= index <= right:
            continue
        candidate = city
        while candidate in first_segment:
            mapped_index = first.index(candidate)
            candidate = second[mapped_index]
        child[index] = candidate
    result = tuple(city for city in child if city is not None)
    _validate_child(result, first)
    return result


def partially_mapped_crossover(
    first: Sequence[int], second: Sequence[int], *, rng: random.Random
) -> CrossoverResult:
    """Apply standard one-child PMX with the same cut-point protocol as OX."""

    _validate_parents(first, second)
    left, right = _cut_points(len(first), rng)
    child = _pmx_child(first, second, left, right)
    return CrossoverResult(child, operator="pmx")


def edge_recombination(
    first: Sequence[int], second: Sequence[int], *, rng: random.Random
) -> CrossoverResult:
    """Build one child using shared-edge priority and minimum adjacency degree."""

    _validate_parents(first, second)
    first_edges = edge_set(first)
    second_edges = edge_set(second)
    adjacency: dict[int, set[int]] = {city: set() for city in first}
    for tour in (first, second):
        for index, city in enumerate(tour):
            adjacency[city].add(tour[(index - 1) % len(tour)])
            adjacency[city].add(tour[(index + 1) % len(tour)])

    child = [first[0]]
    unused = set(first[1:])
    while unused:
        current = child[-1]
        candidates = adjacency[current] & unused
        for neighbours in adjacency.values():
            neighbours.discard(current)
        if candidates:
            shared_candidates = {
                city
                for city in candidates
                if (min(current, city), max(current, city)) in first_edges
                and (min(current, city), max(current, city)) in second_edges
            }
            pool = shared_candidates or candidates
            minimum_degree = min(len(adjacency[city] & unused) for city in pool)
            tied = sorted(
                city for city in pool if len(adjacency[city] & unused) == minimum_degree
            )
            next_city = rng.choice(tied)
        else:
            next_city = rng.choice(sorted(unused))
        child.append(next_city)
        unused.remove(next_city)

    result = tuple(child)
    _validate_child(result, first)
    return CrossoverResult(result, operator="erx")


def switched_adaptive_crossover(
    first: Sequence[int], second: Sequence[int], *, rng: random.Random
) -> CrossoverResult:
    """Delegate to ERX for high parent edge distance and OX otherwise."""

    distance = edge_distance(first, second)
    delegate = "erx" if rng.random() < distance else "ox"
    result = edge_recombination(first, second, rng=rng) if delegate == "erx" else ordered_crossover(first, second, rng=rng)
    return CrossoverResult(
        result.child,
        operator="sax",
        parent_edge_distance=distance,
        delegate=delegate,
    )


def crossover(
    name: str,
    first: Sequence[int],
    second: Sequence[int],
    *,
    rng: random.Random,
) -> CrossoverResult:
    """Dispatch a registered crossover variant by its protocol identifier."""

    operators: dict[str, Callable[..., CrossoverResult]] = {
        "ox": ordered_crossover,
        "pmx": partially_mapped_crossover,
        "erx": edge_recombination,
        "sax": switched_adaptive_crossover,
    }
    try:
        operator = operators[name]
    except KeyError as error:
        raise ValueError(f"unsupported crossover: {name}") from error
    return operator(first, second, rng=rng)


def _validate_parents(first: Sequence[int], second: Sequence[int]) -> None:
    if len(first) != len(second) or len(first) < 3:
        raise ValueError("parents must have equal size of at least three")
    if set(first) != set(second) or len(set(first)) != len(first):
        raise ValueError("parents must be permutations of the same cities")


def _validate_child(child: Sequence[int], parent: Sequence[int]) -> None:
    if tuple(sorted(child)) != tuple(sorted(parent)):
        raise AssertionError("crossover produced an invalid permutation")
