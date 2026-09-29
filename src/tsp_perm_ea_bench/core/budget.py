"""Authoritative objective-evaluation accounting for one run."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from ..problems.tsp import TSPProblem


class EvaluationPhase(StrEnum):
    """The run phase that owns an objective evaluation."""

    INITIALIZATION = "initialization"
    OFFSPRING = "offspring"
    LOCAL_SEARCH = "local_search"
    AUDIT = "audit"


class TerminationReason(StrEnum):
    """Reasons understood by the platform runner."""

    BUDGET_EXHAUSTED = "budget_exhausted"
    OPTIMUM_REACHED = "optimum_reached"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"


class BudgetExceeded(RuntimeError):
    """Raised when a run requests an evaluation after its budget is spent."""


@dataclass
class EvaluationCounters:
    """Logical and physical objective-evaluation counters."""

    initial_evaluations: int = 0
    offspring_evaluations: int = 0
    local_search_evaluations: int = 0
    total_evaluations: int = 0
    full_objective_calls: int = 0
    delta_calls: int = 0
    audit_objective_calls: int = 0
    iterations: int = 0

    def validate(self) -> None:
        """Raise if the accounting identity is violated."""

        expected = (
            self.initial_evaluations
            + self.offspring_evaluations
            + self.local_search_evaluations
        )
        if self.total_evaluations != expected:
            raise AssertionError(
                "total_evaluations must equal the sum of logical phase counters"
            )


@dataclass(frozen=True)
class EvaluationResult:
    """The result of one accepted objective request."""

    value: int | float
    phase: EvaluationPhase
    logical_evaluation: int
    best_value: int | float
    reached_proven_optimum: bool


class EvaluationContext:
    """Evaluate tours while enforcing the declared offspring budget.

    Initialization evaluations are counted separately. The default first
    version deliberately does not cache objective values: duplicate tours
    still consume one logical evaluation, as required by the protocol.
    """

    def __init__(
        self,
        problem: "TSPProblem",
        *,
        offspring_budget: int,
        stop_at_proven_optimum: bool = True,
    ) -> None:
        if offspring_budget < 0:
            raise ValueError("offspring_budget must be non-negative")
        self.problem = problem
        self.offspring_budget = offspring_budget
        self.stop_at_proven_optimum = stop_at_proven_optimum
        self.counters = EvaluationCounters()
        self.best_value: int | float | None = None
        self.best_tour: tuple[int, ...] | None = None
        self.termination_reason: TerminationReason | None = None
        self._event_sequence = 0

    @property
    def offspring_budget_remaining(self) -> int:
        """Return the number of offspring evaluations still available."""

        return self.offspring_budget - self.counters.offspring_evaluations

    @property
    def exhausted(self) -> bool:
        """Return whether the offspring evaluation budget is spent."""

        return self.offspring_budget_remaining == 0

    def evaluate(
        self,
        tour: Sequence[int],
        *,
        phase: EvaluationPhase,
        use_delta: bool = False,
    ) -> EvaluationResult:
        """Evaluate one legal tour and update the authoritative counters."""

        if phase is EvaluationPhase.OFFSPRING and self.exhausted:
            self.termination_reason = TerminationReason.BUDGET_EXHAUSTED
            raise BudgetExceeded("the offspring evaluation budget is exhausted")
        if (
            self.termination_reason is TerminationReason.OPTIMUM_REACHED
            and phase is not EvaluationPhase.INITIALIZATION
        ):
            raise BudgetExceeded("the run already reached its proven optimum")

        value = self.problem.evaluate(tour)
        tour_tuple = tuple(tour)
        self._record_counter(phase, use_delta=use_delta)
        if self.best_value is None or value < self.best_value:
            self.best_value = value
            self.best_tour = tour_tuple

        reached_optimum = (
            self.stop_at_proven_optimum
            and self.problem.reference_status == "proven_optimum"
            and self.problem.reference_value is not None
            and value == self.problem.reference_value
        )
        if reached_optimum and phase is not EvaluationPhase.INITIALIZATION:
            self.termination_reason = TerminationReason.OPTIMUM_REACHED

        self.counters.validate()
        return EvaluationResult(
            value=value,
            phase=phase,
            logical_evaluation=self.counters.total_evaluations,
            best_value=self.best_value,
            reached_proven_optimum=reached_optimum,
        )

    def finish_if_budget_exhausted(self) -> None:
        """Mark normal budget completion once no offspring budget remains."""

        if self.exhausted and self.termination_reason is None:
            self.termination_reason = TerminationReason.BUDGET_EXHAUSTED

    def next_event_sequence(self) -> int:
        """Return the next monotonically increasing observer sequence number."""

        self._event_sequence += 1
        return self._event_sequence

    def _record_counter(self, phase: EvaluationPhase, *, use_delta: bool) -> None:
        if phase is EvaluationPhase.INITIALIZATION:
            self.counters.initial_evaluations += 1
        elif phase is EvaluationPhase.OFFSPRING:
            self.counters.offspring_evaluations += 1
        elif phase is EvaluationPhase.LOCAL_SEARCH:
            self.counters.local_search_evaluations += 1
        elif phase is EvaluationPhase.AUDIT:
            self.counters.audit_objective_calls += 1
        else:
            raise ValueError(f"unsupported evaluation phase: {phase}")

        if phase is not EvaluationPhase.AUDIT:
            self.counters.total_evaluations += 1
        if use_delta:
            self.counters.delta_calls += 1
        else:
            self.counters.full_objective_calls += 1
