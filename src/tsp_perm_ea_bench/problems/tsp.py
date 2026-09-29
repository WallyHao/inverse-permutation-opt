"""Symmetric TSP representation and the supported TSPLIB parser."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Iterable, Mapping, Sequence


class ProblemFormatError(ValueError):
    """Raised when an instance violates the supported TSP protocol."""


class ReferenceStatus(StrEnum):
    """Status of the reference objective associated with an instance."""

    PROVEN_OPTIMUM = "proven_optimum"
    BEST_KNOWN = "best_known"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TSPProblem:
    """A symmetric TSP with internal city identifiers ``0..n-1``."""

    name: str
    node_ids: tuple[int, ...]
    distances: tuple[tuple[int, ...], ...]
    original_to_internal: Mapping[int, int]
    reference_value: int | None = None
    reference_status: str = ReferenceStatus.UNKNOWN
    reference_tour: tuple[int, ...] | None = None
    edge_weight_type: str = "EXPLICIT"

    def __post_init__(self) -> None:
        n = len(self.node_ids)
        if n < 3:
            raise ProblemFormatError("a TSP instance requires at least three cities")
        if len(set(self.node_ids)) != n:
            raise ProblemFormatError("node identifiers must be unique")
        if len(self.distances) != n or any(len(row) != n for row in self.distances):
            raise ProblemFormatError("distance matrix must be square")
        for i in range(n):
            if self.distances[i][i] != 0:
                raise ProblemFormatError("distance matrix diagonal must be zero")
            for j in range(n):
                weight = self.distances[i][j]
                if not isinstance(weight, int) or weight < 0:
                    raise ProblemFormatError("distances must be non-negative integers")
                if weight != self.distances[j][i]:
                    raise ProblemFormatError("distance matrix must be symmetric")
        if set(self.original_to_internal) != set(self.node_ids):
            raise ProblemFormatError("the original city mapping is incomplete")
        if set(self.original_to_internal.values()) != set(range(n)):
            raise ProblemFormatError("the internal city mapping is not a permutation")
        if self.reference_status not in {status.value for status in ReferenceStatus}:
            raise ProblemFormatError(
                f"unsupported reference status: {self.reference_status}"
            )
        if self.reference_tour is not None:
            self.validate_tour(self.reference_tour)

    @property
    def n(self) -> int:
        """Return the number of cities."""

        return len(self.node_ids)

    @classmethod
    def from_matrix(
        cls,
        name: str,
        distances: Sequence[Sequence[int]],
        *,
        node_ids: Sequence[int] | None = None,
        reference_value: int | None = None,
        reference_status: str = ReferenceStatus.UNKNOWN,
        reference_tour: Sequence[int] | None = None,
    ) -> "TSPProblem":
        """Construct a problem from an already validated integer matrix."""

        n = len(distances)
        ids = tuple(range(1, n + 1) if node_ids is None else node_ids)
        if len(ids) != n:
            raise ProblemFormatError("node_ids must match the matrix dimension")
        mapping = {node_id: index for index, node_id in enumerate(ids)}
        return cls(
            name=name,
            node_ids=ids,
            distances=tuple(tuple(row) for row in distances),
            original_to_internal=mapping,
            reference_value=reference_value,
            reference_status=reference_status,
            reference_tour=None if reference_tour is None else tuple(reference_tour),
        )

    @classmethod
    def from_coordinates(
        cls,
        name: str,
        coordinates: Mapping[int, tuple[float, float]],
        *,
        reference_value: int | None = None,
        reference_status: str = ReferenceStatus.UNKNOWN,
        reference_tour: Sequence[int] | None = None,
    ) -> "TSPProblem":
        """Construct an EUC_2D problem using TSPLIB nearest-integer rounding."""

        node_ids = tuple(coordinates)
        matrix = []
        for source in node_ids:
            row = []
            for target in node_ids:
                x1, y1 = coordinates[source]
                x2, y2 = coordinates[target]
                row.append(tsplib_euc_2d_distance(x1, y1, x2, y2))
            matrix.append(row)
        return cls(
            name=name,
            node_ids=node_ids,
            distances=tuple(tuple(row) for row in matrix),
            original_to_internal={node_id: index for index, node_id in enumerate(node_ids)},
            reference_value=reference_value,
            reference_status=reference_status,
            reference_tour=None if reference_tour is None else tuple(reference_tour),
            edge_weight_type="EUC_2D",
        )

    def validate_tour(self, tour: Sequence[int]) -> None:
        """Raise if ``tour`` is not a permutation of internal city identifiers."""

        if len(tour) != self.n:
            raise ValueError(f"tour must contain exactly {self.n} cities")
        if set(tour) != set(range(self.n)):
            raise ValueError("tour must be a permutation of internal city identifiers")

    def evaluate(self, tour: Sequence[int]) -> int:
        """Return the exact length of the closed tour."""

        self.validate_tour(tour)
        return sum(
            self.distances[tour[index]][tour[(index + 1) % self.n]]
            for index in range(self.n)
        )

    def to_original_tour(self, tour: Sequence[int]) -> tuple[int, ...]:
        """Convert an internal tour to the identifiers in the source file."""

        self.validate_tour(tour)
        return tuple(self.node_ids[city] for city in tour)

    def to_internal_tour(self, tour: Sequence[int]) -> tuple[int, ...]:
        """Convert a source-file tour to internal identifiers."""

        internal = tuple(self.original_to_internal.get(city, -1) for city in tour)
        self.validate_tour(internal)
        return internal


def tsplib_euc_2d_distance(
    x1: float, y1: float, x2: float, y2: float
) -> int:
    """Compute TSPLIB's ``EUC_2D`` nearest-integer distance."""

    distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    return math.floor(distance + 0.5)


def load_tsplib(
    path: str | Path,
    *,
    reference_value: int | None = None,
    reference_status: str = ReferenceStatus.UNKNOWN,
    reference_tour: Sequence[int] | None = None,
) -> TSPProblem:
    """Load a supported ``TYPE: TSP`` and ``EDGE_WEIGHT_TYPE: EUC_2D`` file."""

    source = Path(path)
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ProblemFormatError(f"cannot read TSPLIB instance {source}: {error}") from error

    headers: dict[str, str] = {}
    coordinates: dict[int, tuple[float, float]] = {}
    section: str | None = None
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        upper = line.upper()
        if upper == "EOF":
            break
        if upper.endswith("_SECTION"):
            section = upper
            continue
        if section == "NODE_COORD_SECTION":
            fields = line.split()
            if len(fields) != 3:
                raise ProblemFormatError(f"invalid coordinate row: {line}")
            try:
                node_id = int(fields[0])
                x, y = float(fields[1]), float(fields[2])
            except ValueError as error:
                raise ProblemFormatError(f"invalid coordinate row: {line}") from error
            if node_id in coordinates:
                raise ProblemFormatError(f"duplicate node identifier: {node_id}")
            if not math.isfinite(x) or not math.isfinite(y):
                raise ProblemFormatError(f"non-finite coordinate row: {line}")
            coordinates[node_id] = (x, y)
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().upper()] = value.strip()

    if headers.get("TYPE", "").upper() != "TSP":
        raise ProblemFormatError("only TYPE: TSP is supported")
    if headers.get("EDGE_WEIGHT_TYPE", "").upper() != "EUC_2D":
        raise ProblemFormatError("only EDGE_WEIGHT_TYPE: EUC_2D is supported")
    try:
        dimension = int(headers["DIMENSION"])
    except (KeyError, ValueError) as error:
        raise ProblemFormatError("DIMENSION must be an integer") from error
    if dimension != len(coordinates):
        raise ProblemFormatError(
            f"DIMENSION={dimension} but parsed {len(coordinates)} coordinate rows"
        )

    return TSPProblem.from_coordinates(
        headers.get("NAME", source.stem),
        coordinates,
        reference_value=reference_value,
        reference_status=reference_status,
        reference_tour=reference_tour,
    )
