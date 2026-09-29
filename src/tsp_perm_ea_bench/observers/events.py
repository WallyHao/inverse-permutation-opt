"""Immutable events emitted by the algorithm execution framework."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ..core.budget import EvaluationContext


class Observer(Protocol):
    """Protocol implemented by observers that consume run events."""

    def on_event(self, event: "Event") -> None:
        """Consume one event without changing algorithm state."""


@dataclass(frozen=True)
class Event:
    """A serializable event with a complete budget snapshot."""

    event_type: str
    sequence: int
    phase: str
    iteration: int
    initial_evaluations: int
    offspring_evaluations: int
    local_search_evaluations: int
    total_evaluations: int
    payload: dict[str, Any]

    @classmethod
    def from_context(
        cls,
        event_type: str,
        context: EvaluationContext,
        *,
        iteration: int,
        payload: dict[str, Any],
    ) -> "Event":
        counters = context.counters
        return cls(
            event_type=event_type,
            sequence=context.next_event_sequence(),
            phase=event_type,
            iteration=iteration,
            initial_evaluations=counters.initial_evaluations,
            offspring_evaluations=counters.offspring_evaluations,
            local_search_evaluations=counters.local_search_evaluations,
            total_evaluations=counters.total_evaluations,
            payload=payload,
        )


class MemoryObserver:
    """Collect events for tests and in-process analysis."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def on_event(self, event: Event) -> None:
        self.events.append(event)
