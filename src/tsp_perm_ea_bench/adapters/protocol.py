"""Protocol for connecting an external algorithm to the run contract."""

from __future__ import annotations

from typing import Any, Protocol

from ..algorithms.steady_state import RunResult
from ..observers.events import Observer
from ..problems.tsp import TSPProblem


class AlgorithmAdapter(Protocol):
    """An adapter must expose the same problem, seed, and observer boundary."""

    def run(
        self,
        problem: TSPProblem,
        *,
        config: dict[str, Any],
        master_seed: int,
        instance_id: str,
        repeat: int,
        observer: Observer,
    ) -> RunResult:
        """Execute one run without bypassing the shared result protocol."""
