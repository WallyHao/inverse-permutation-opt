"""Versioned instance manifests and source-file integrity checks."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .tsp import ReferenceStatus, TSPProblem, load_tsplib


@dataclass(frozen=True)
class InstanceRecord:
    """One manifest entry with the metadata required for a reproducible load."""

    instance_id: str
    file: Path
    dimension: int
    edge_weight_type: str
    reference_status: str
    reference_value: int | None
    reference_tour: tuple[int, ...] | None
    source: str
    sha256: str | None = None


class InstanceRegistry:
    """Load, validate, and resolve instances from a JSON manifest."""

    def __init__(self, manifest_path: str | Path, records: dict[str, InstanceRecord]) -> None:
        self.manifest_path = Path(manifest_path)
        self.records = records

    @classmethod
    def from_manifest(cls, manifest_path: str | Path) -> "InstanceRegistry":
        path = Path(manifest_path)
        document = json.loads(path.read_text(encoding="utf-8"))
        if document.get("schema_version") != "benchmark-manifest-v1":
            raise ValueError("unsupported benchmark manifest schema")
        records: dict[str, InstanceRecord] = {}
        for entry in document.get("instances", []):
            instance_id = str(entry["instance_id"])
            if instance_id in records:
                raise ValueError(f"duplicate instance_id: {instance_id}")
            records[instance_id] = InstanceRecord(
                instance_id=instance_id,
                file=path.parent / entry["file"],
                dimension=int(entry["dimension"]),
                edge_weight_type=str(entry["edge_weight_type"]),
                reference_status=str(entry["reference_status"]),
                reference_value=entry.get("reference_value"),
                reference_tour=(
                    None
                    if entry.get("reference_tour") is None
                    else tuple(int(city) for city in entry["reference_tour"])
                ),
                source=str(entry.get("source", "")),
                sha256=entry.get("sha256"),
            )
        return cls(path, records)

    def get(self, instance_id: str) -> InstanceRecord:
        """Return a manifest record by stable identity."""

        try:
            return self.records[instance_id]
        except KeyError as error:
            raise KeyError(f"unknown instance_id: {instance_id}") from error

    def load(self, instance_id: str) -> TSPProblem:
        """Validate source identity and return the corresponding TSP problem."""

        record = self.get(instance_id)
        source_bytes = record.file.read_bytes()
        actual_sha256 = hashlib.sha256(source_bytes).hexdigest()
        if record.sha256 is not None and actual_sha256 != record.sha256:
            raise ValueError(
                f"SHA-256 mismatch for {instance_id}: expected {record.sha256}, "
                f"got {actual_sha256}"
            )
        problem = load_tsplib(
            record.file,
            reference_value=record.reference_value,
            reference_status=record.reference_status,
            reference_tour=None,
        )
        if problem.n != record.dimension:
            raise ValueError(
                f"dimension mismatch for {instance_id}: "
                f"manifest={record.dimension}, parsed={problem.n}"
            )
        if problem.edge_weight_type != record.edge_weight_type:
            raise ValueError(
                f"distance-type mismatch for {instance_id}: "
                f"manifest={record.edge_weight_type}, parsed={problem.edge_weight_type}"
            )
        if record.reference_tour is not None:
            internal_tour = problem.to_internal_tour(record.reference_tour)
            if record.reference_value is None:
                raise ValueError(f"reference tour has no value for {instance_id}")
            actual_value = problem.evaluate(internal_tour)
            if actual_value != record.reference_value:
                raise ValueError(
                    f"reference tour mismatch for {instance_id}: "
                    f"declared={record.reference_value}, computed={actual_value}"
                )
            problem = TSPProblem(
                name=problem.name,
                node_ids=problem.node_ids,
                distances=problem.distances,
                original_to_internal=problem.original_to_internal,
                reference_value=problem.reference_value,
                reference_status=problem.reference_status,
                reference_tour=internal_tour,
                edge_weight_type=problem.edge_weight_type,
            )
        return problem

    def validate_all(self) -> list[str]:
        """Validate every registered source and return the validated identities."""

        for instance_id in self.records:
            self.load(instance_id)
        return list(self.records)
