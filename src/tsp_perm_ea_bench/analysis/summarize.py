"""Rebuild tables and a lightweight convergence figure from run artifacts."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from .metrics import aggregate_values, ert, first_hit, gap_ratio


TARGET_GAPS = (0.1, 0.01, 0.001, 0.0)


def summarize_experiment(
    experiment_directory: str | Path,
    *,
    output_directory: str | Path | None = None,
) -> Path:
    """Create final, aggregate, target-hit, and SVG outputs for an experiment."""

    experiment = Path(experiment_directory)
    output = Path(output_directory) if output_directory else experiment / "analysis" / "analysis-v1"
    output.mkdir(parents=True, exist_ok=True)
    runs = _load_completed_runs(experiment)
    failures = _load_failures(experiment)
    final_rows = [_final_row(item) for item in runs]
    _write_csv(output / "final_summary.csv", final_rows)
    aggregate_rows = _aggregate_rows(final_rows)
    _write_csv(output / "aggregate_summary.csv", aggregate_rows)
    hit_rows = _hit_rows(runs)
    _write_csv(output / "hit_summary.csv", hit_rows)
    _write_csv(output / "failure_summary.csv", failures)
    _write_convergence_svg(output / "convergence.svg", runs)
    (output / "analysis_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "analysis-manifest-v1",
                "source_experiment": str(experiment),
                "completed_run_count": len(runs),
                "failed_attempt_count": len(failures),
                "targets": list(TARGET_GAPS),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return output


def _load_completed_runs(experiment: Path) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for summary_path in sorted(experiment.glob("runs/*/attempt-*/summary.json")):
        attempt = summary_path.parent
        if not (attempt / "complete.json").is_file():
            continue
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            manifest = json.loads((attempt / "manifest.json").read_text(encoding="utf-8"))
            with (attempt / "checkpoints.csv").open(newline="") as handle:
                checkpoints = list(csv.DictReader(handle))
            with (attempt / "improvements.csv").open(newline="") as handle:
                improvements = list(csv.DictReader(handle))
        except (OSError, json.JSONDecodeError, KeyError):
            continue
        runs.append(
            {
                "summary": summary,
                "manifest": manifest,
                "checkpoints": checkpoints,
                "improvements": improvements,
            }
        )
    return runs


def _load_failures(experiment: Path) -> list[dict[str, Any]]:
    """Return failed tasks without treating them as successful budget censures."""

    manifest_path = experiment / "task_manifest.json"
    if not manifest_path.is_file():
        return []
    task_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = []
    for task in task_manifest.get("tasks", []):
        if task.get("status") != "failed":
            continue
        run_root = experiment / "runs" / task["run_id"]
        errors = sorted(run_root.glob("attempt-*/error.json"))
        error = json.loads(errors[-1].read_text(encoding="utf-8")) if errors else {}
        rows.append(
            {
                "run_id": task["run_id"],
                "instance_id": task["instance_id"],
                "crossover": task["crossover"],
                "repeat": task["repeat"],
                "master_seed": task["master_seed"],
                "status": "failed",
                "error_type": error.get("error_type"),
                "message": error.get("message"),
            }
        )
    return rows


def _final_row(run: dict[str, Any]) -> dict[str, Any]:
    summary = run["summary"]
    manifest = run["manifest"]
    problem = manifest["problem"]
    config = manifest["config"]
    reference = problem.get("reference_value")
    best = summary.get("best_value")
    return {
        "run_id": summary["run_id"],
        "instance_id": summary["instance_id"],
        "crossover": config["crossover"],
        "repeat": summary["repeat"],
        "master_seed": summary["master_seed"],
        "termination_reason": summary["termination_reason"],
        "best_value": best,
        "reference_value": reference,
        "reference_status": problem.get("reference_status"),
        "gap_ratio": gap_ratio(best, reference),
        "gap_percent": _percent(gap_ratio(best, reference)),
        "offspring_evaluations": summary["counters"]["offspring_evaluations"],
        "total_evaluations": summary["counters"]["total_evaluations"],
        "wall_time": summary.get("wall_time"),
        "process_cpu_time": summary.get("process_cpu_time"),
    }


def _aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["instance_id"], row["crossover"])].append(row)
    result = []
    for (instance_id, crossover), group in sorted(groups.items()):
        aggregate = aggregate_values(row["gap_ratio"] for row in group)
        result.append(
            {
                "instance_id": instance_id,
                "crossover": crossover,
                **aggregate.as_dict(),
                "successful_runs": sum(
                    row["termination_reason"] != "failed" for row in group
                ),
            }
        )
    return result


def _hit_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in TARGET_GAPS:
        groups: dict[tuple[str, str], list[int | None]] = defaultdict(list)
        budgets: dict[tuple[str, str], int] = {}
        for run in runs:
            summary = run["summary"]
            manifest = run["manifest"]
            key = (summary["instance_id"], manifest["config"]["crossover"])
            reference = manifest["problem"].get("reference_value")
            checkpoints = [
                (int(row["offspring_evaluations"]), float(row["global_best"]))
                for row in run["checkpoints"]
                if row.get("global_best") not in {None, "", "None"}
            ]
            improvements = [
                (int(row["offspring_evaluations"]), float(row["best_value"]))
                for row in run["improvements"]
                if row.get("best_value") not in {None, "", "None"}
            ]
            groups[key].append(
                first_hit(
                    checkpoints + improvements,
                    reference_value=reference,
                    target_gap=target,
                )
            )
            budgets[key] = int(manifest["config"]["offspring_budget"])
        for (instance_id, crossover), positions in sorted(groups.items()):
            rows.append(
                {
                    "instance_id": instance_id,
                    "crossover": crossover,
                    "target_gap": target,
                    "run_count": len(positions),
                    "success_count": sum(position is not None for position in positions),
                    "success_rate": sum(position is not None for position in positions)
                    / len(positions),
                    "ert": ert(positions, budget=budgets[(instance_id, crossover)]),
                    "budget": budgets[(instance_id, crossover)],
                }
            )
    return rows


def _write_convergence_svg(path: Path, runs: list[dict[str, Any]]) -> None:
    """Draw median gap trajectories with only the Python standard library."""

    grouped: dict[tuple[str, str, int], list[float]] = defaultdict(list)
    for run in runs:
        summary = run["summary"]
        manifest = run["manifest"]
        reference = manifest["problem"].get("reference_value")
        if reference is None:
            continue
        key_prefix = (summary["instance_id"], manifest["config"]["crossover"])
        for row in run["checkpoints"]:
            if row.get("global_best") in {None, "", "None"}:
                continue
            value = gap_ratio(float(row["global_best"]), reference)
            if value is not None:
                grouped[(*key_prefix, int(row["offspring_evaluations"]))].append(value)
    points: dict[tuple[str, str], list[tuple[int, float]]] = defaultdict(list)
    for (instance_id, crossover, budget), values in sorted(grouped.items()):
        points[(instance_id, crossover)].append(
            (budget, aggregate_values(values).median or 0.0)
        )
    width, height = 900, 500
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="20" y="25" font-family="sans-serif" font-size="16">Median convergence gap by checkpoint</text>',
        '<line x1="70" y1="450" x2="870" y2="450" stroke="black"/>',
        '<line x1="70" y1="60" x2="70" y2="450" stroke="black"/>',
    ]
    colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]
    all_budgets = [budget for values in points.values() for budget, _ in values]
    max_budget = max(all_budgets, default=1)
    all_gaps = [gap for values in points.values() for _, gap in values]
    max_gap = max(max(all_gaps, default=1.0), 1e-12)
    for color_index, (label, values) in enumerate(sorted(points.items())):
        path_data = []
        for budget, gap in values:
            x = 70 + 800 * (math.log10(max(budget, 1)) / math.log10(max(max_budget, 10)))
            y = 450 - 390 * max(0.0, min(1.0, gap / max_gap))
            path_data.append(f"{x:.2f},{y:.2f}")
        color = colors[color_index % len(colors)]
        lines.append(f'<polyline points="{" ".join(path_data)}" fill="none" stroke="{color}"/>')
        lines.append(
            f'<text x="{90 + (color_index % 4) * 190}" y="{475 + (color_index // 4) * 16}" '
            f'font-family="sans-serif" font-size="11" fill="{color}">{label[0]} / {label[1]}</text>'
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _percent(value: float | None) -> float | None:
    return None if value is None else value * 100.0
