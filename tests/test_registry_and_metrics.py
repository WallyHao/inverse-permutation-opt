import csv
import tempfile
import unittest
from pathlib import Path

from tsp_perm_ea_bench.observers.events import MemoryObserver
from tsp_perm_ea_bench.observers.logger import RunLogger
from tsp_perm_ea_bench.problems.metrics import (
    edge_retention,
    position_retention,
)
from tsp_perm_ea_bench.problems.registry import InstanceRegistry


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class RegistryTests(unittest.TestCase):
    def test_development_manifest_validates_all_sources_and_reference_tours(self) -> None:
        registry = InstanceRegistry.from_manifest(
            REPOSITORY_ROOT / "benchmarks" / "manifest.json"
        )

        self.assertEqual(
            registry.validate_all(), ["triangle", "square", "rounding-boundary"]
        )
        self.assertEqual(registry.load("square").reference_tour, (0, 1, 2, 3))


class StructureMetricTests(unittest.TestCase):
    def test_child_metrics_include_parent_one_or_parent_two_structure(self) -> None:
        first = (0, 1, 2, 3)
        second = (0, 3, 2, 1)
        child = (0, 1, 3, 2)

        self.assertEqual(edge_retention(child, first, second), 0.5)
        self.assertEqual(position_retention(child, first, second), 0.5)


class OperatorSummaryTests(unittest.TestCase):
    def test_default_logger_writes_aggregated_operator_summary(self) -> None:
        from tsp_perm_ea_bench.algorithms.steady_state import (
            SteadyStateConfig,
            run_steady_state_ga,
        )
        from tsp_perm_ea_bench.problems.tsp import TSPProblem

        problem = TSPProblem.from_matrix(
            "four-city",
            ((0, 1, 2, 3), (1, 0, 4, 2), (2, 4, 0, 1), (3, 2, 1, 0)),
        )
        observer = MemoryObserver()
        result = run_steady_state_ga(
            problem,
            SteadyStateConfig(population_size=4, offspring_budget=3),
            master_seed=5,
            instance_id="four-city",
            repeat=0,
            observer=observer,
        )
        with tempfile.TemporaryDirectory() as temporary:
            logger = RunLogger(Path(temporary))
            for event in observer.events:
                logger.on_event(event)
            logger.write(result=result, manifest={}, best_tour={})
            with (Path(temporary) / "operator_summary.csv").open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["calls"], "3")
            self.assertFalse((Path(temporary) / "events.csv").exists())


if __name__ == "__main__":
    unittest.main()
