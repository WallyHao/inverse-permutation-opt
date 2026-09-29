"""Variation, selection, and replacement operators."""

from .crossover import (
    CrossoverResult,
    crossover,
    edge_recombination,
    ordered_crossover,
    partially_mapped_crossover,
    switched_adaptive_crossover,
)
from .mutation import move_mutation
from .replacement import replace_worst
from .selection import inverse_tournament, random_parent_selection

__all__ = [
    "CrossoverResult",
    "crossover",
    "edge_recombination",
    "inverse_tournament",
    "move_mutation",
    "ordered_crossover",
    "partially_mapped_crossover",
    "random_parent_selection",
    "replace_worst",
    "switched_adaptive_crossover",
]
