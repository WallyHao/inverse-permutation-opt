"""Persistent CSV and JSON artifacts for one completed run."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .events import Event


class RunLogger:
    """Collect events and write a run directory with an atomic completion marker."""

    def __init__(self, output_directory: str | Path, *, detailed_events: bool = False) -> None:
        self.output_directory = Path(output_directory)
        self.detailed_events = detailed_events
        self.events: list[Event] = []

    def on_event(self, event: Event) -> None:
        self.events.append(event)

    def write(self, *, result: Any, manifest: dict[str, Any], best_tour: dict[str, Any]) -> None:
        """Write all run artifacts and create ``complete.json`` last."""

        self.output_directory.mkdir(parents=True, exist_ok=True)
        self._write_json("manifest.json", manifest)
        self._write_csv(
            "improvements.csv",
            [event for event in self.events if event.event_type == "improvement"],
        )
        self._write_csv(
            "checkpoints.csv",
            [event for event in self.events if event.event_type == "checkpoint"],
        )
        self._write_operator_summary()
        if self.detailed_events:
            self._write_csv(
                "events.csv",
                [event for event in self.events if event.event_type == "offspring"],
            )
        self._write_json("summary.json", _jsonable(result))
        self._write_json("best_tour.json", best_tour)
        self._write_json(
            "complete.json",
            {"schema_version": "completion-v1", "run_id": result.run_id},
        )

    def _write_json(self, filename: str, value: Any) -> None:
        _atomic_write(
            self.output_directory / filename,
            json.dumps(_jsonable(value), indent=2, sort_keys=True) + "\n",
        )

    def _write_csv(self, filename: str, events: list[Event]) -> None:
        rows: list[dict[str, Any]] = []
        for event in events:
            row = {
                "event_type": event.event_type,
                "sequence": event.sequence,
                "phase": event.phase,
                "iteration": event.iteration,
                "initial_evaluations": event.initial_evaluations,
                "offspring_evaluations": event.offspring_evaluations,
                "local_search_evaluations": event.local_search_evaluations,
                "total_evaluations": event.total_evaluations,
            }
            row.update(event.payload)
            rows.append(row)
        fieldnames = sorted({key for row in rows for key in row})
        if not fieldnames:
            fieldnames = ["event_type", "sequence"]
        lines: list[str] = []
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="", dir=self.output_directory, delete=False
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            temporary = Path(handle.name)
        os.replace(temporary, self.output_directory / filename)

    def _write_operator_summary(self) -> None:
        """Write mechanism aggregates without requiring per-offspring storage."""

        grouped: dict[tuple[str, str], list[Event]] = {}
        for event in self.events:
            if event.event_type != "offspring":
                continue
            key = (str(event.payload.get("crossover")), str(event.payload.get("delegate") or ""))
            grouped.setdefault(key, []).append(event)
        rows: list[dict[str, Any]] = []
        for (crossover_name, delegate), events in sorted(grouped.items()):
            distances = [
                event.payload["parent_edge_distance"]
                for event in events
                if event.payload.get("parent_edge_distance") is not None
            ]
            edge_values = [float(event.payload["edge_retention"]) for event in events]
            position_values = [
                float(event.payload["position_retention"]) for event in events
            ]
            mutation_count = sum(
                bool(event.payload.get("mutation_applied")) for event in events
            )
            rows.append(
                {
                    "crossover": crossover_name,
                    "delegate": delegate,
                    "calls": len(events),
                    "mean_parent_edge_distance": _mean(distances),
                    "mean_edge_retention": _mean(edge_values),
                    "mean_position_retention": _mean(position_values),
                    "mutation_count": mutation_count,
                    "mutation_rate": mutation_count / len(events),
                }
            )
        fieldnames = [
            "crossover",
            "delegate",
            "calls",
            "mean_parent_edge_distance",
            "mean_edge_retention",
            "mean_position_retention",
            "mutation_count",
            "mutation_rate",
        ]
        temporary: Path
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="", dir=self.output_directory, delete=False
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            temporary = Path(handle.name)
        os.replace(temporary, self.output_directory / "operator_summary.csv")


def _atomic_write(path: Path, content: str) -> None:
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        from dataclasses import asdict

        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)
