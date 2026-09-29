"""Pure analysis functions with explicit missing and censoring semantics."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median, stdev
from typing import Iterable, Sequence


def gap_ratio(best_value: float | int | None, reference_value: float | int | None) -> float | None:
    """Return the signed relative gap; preserve negative best-known gaps."""

    if best_value is None or reference_value is None:
        return None
    if reference_value <= 0:
        raise ValueError("reference_value must be positive for a relative gap")
    return (best_value - reference_value) / reference_value


def first_hit(
    checkpoints: Iterable[tuple[int, float | int]],
    *,
    reference_value: float | int | None,
    target_gap: float,
) -> int | None:
    """Return the first budget position at or below a relative target gap."""

    if reference_value is None:
        return None
    if reference_value <= 0:
        raise ValueError("reference_value must be positive for target gaps")
    for budget, value in sorted(checkpoints):
        if gap_ratio(value, reference_value) <= target_gap:
            return budget
    return None


def ert(hit_positions: Sequence[int | None], *, budget: int) -> float | None:
    """Compute ERT with right-censoring for complete fixed-budget runs.

    A ``None`` position contributes the fixed budget to the numerator. With no
    successful run the estimate is undefined and ``None`` is returned.
    """

    if budget < 0:
        raise ValueError("budget must be non-negative")
    successes = sum(position is not None and position <= budget for position in hit_positions)
    if successes == 0:
        return None
    total = sum(min(position, budget) if position is not None else budget for position in hit_positions)
    return total / successes


@dataclass(frozen=True)
class Aggregate:
    """Descriptive statistics for one predeclared group."""

    count: int
    mean: float | None
    standard_deviation: float | None
    median: float | None
    minimum: float | None
    maximum: float | None

    def as_dict(self) -> dict[str, float | int | None]:
        """Return a serializable mapping."""

        return {
            "count": self.count,
            "mean": self.mean,
            "standard_deviation": self.standard_deviation,
            "median": self.median,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }


def aggregate_values(values: Iterable[float | int | None]) -> Aggregate:
    """Compute descriptive statistics after dropping explicit missing values."""

    observed = [float(value) for value in values if value is not None]
    return Aggregate(
        count=len(observed),
        mean=mean(observed) if observed else None,
        standard_deviation=stdev(observed) if len(observed) > 1 else None,
        median=median(observed) if observed else None,
        minimum=min(observed) if observed else None,
        maximum=max(observed) if observed else None,
    )
