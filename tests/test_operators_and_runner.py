import json
import random
import tempfile
import unittest
from pathlib import Path

from tsp_perm_ea_bench.algorithms.steady_state import (
    SteadyStateConfig,
    run_steady_state_ga,
)
from tsp_perm_ea_bench.observers.events import MemoryObserver
from tsp_perm_ea_bench.observers.logger import RunLogger
from tsp_perm_ea_bench.operators.crossover import crossover
from tsp_perm_ea_bench.operators.mutation import move_mutation
from tsp_perm_ea_bench.problems.tsp import TSPProblem


class OperatorTests(unittest.TestCase):
    def test_all_first_matrix_crossovers_return_legal_children(self) -> None:
        first = (0, 1, 2, 3, 4, 5)
        second = (5, 3, 1, 4, 0, 2)
        for name in ("ox", "pmx", "erx", "sax"):
            first_before, second_before = first, second
            result = crossover(name, first, second, rng=random.Random(11))
            self.assertEqual(sorted(result.child), list(range(6)))
            self.assertEqual(first, first_before)
            self.assertEqual(second, second_before)

    def test_move_mutation_preserves_the_permutation(self) -> None:
        result = move_mutation(
            (0, 1, 2, 3, 4), probability=1.0, rng=random.Random(17)
        )
        self.assertTrue(result.applied)
        self.assertEqual(sorted(result.tour), [0, 1, 2, 3, 4])
        self.assertNotEqual(result.tour, (0, 1, 2, 3, 4))


class RunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = TSPProblem.from_matrix(
            "six-city-fixture",
            (
                (0, 4, 7, 3, 8, 5),
                (4, 0, 2, 6, 5, 7),
                (7, 2, 0, 4, 3, 6),
                (3, 6, 4, 0, 5, 2),
                (8, 5, 3, 5, 0, 4),
                (5, 7, 6, 2, 4, 0),
            ),
        )
        self.config = SteadyStateConfig(
            population_size=6,
            offspring_budget=8,
            mutation_probability=0.05,
            crossover="ox",
        )

    def test_repeated_run_has_the_same_logical_result_and_events(self) -> None:
        first_observer = MemoryObserver()
        second_observer = MemoryObserver()
        first = run_steady_state_ga(
            self.problem,
            self.config,
            master_seed=1000,
            instance_id="six-city",
            repeat=0,
            observer=first_observer,
        )
        second = run_steady_state_ga(
            self.problem,
            self.config,
            master_seed=1000,
            instance_id="six-city",
            repeat=0,
            observer=second_observer,
        )

        self.assertEqual(first, second)
        self.assertEqual(first_observer.events, second_observer.events)
        self.assertEqual(first.counters["initial_evaluations"], 6)
        self.assertEqual(first.counters["offspring_evaluations"], 8)
        self.assertEqual(first.counters["total_evaluations"], 14)
        self.assertEqual(first.termination_reason, "budget_exhausted")

    def test_logger_writes_complete_run_artifacts(self) -> None:
        observer = MemoryObserver()
        result = run_steady_state_ga(
            self.problem,
            self.config,
            master_seed=1000,
            instance_id="six-city",
            repeat=0,
            observer=observer,
        )
        with tempfile.TemporaryDirectory() as temporary:
            run_directory = Path(temporary) / result.run_id
            logger = RunLogger(run_directory)
            for event in observer.events:
                logger.on_event(event)
            logger.write(
                result=result,
                manifest={"run_id": result.run_id, "schema_version": "test"},
                best_tour={"length": result.best_value},
            )
            self.assertTrue((run_directory / "complete.json").is_file())
            summary = json.loads((run_directory / "summary.json").read_text())
            self.assertEqual(summary["run_id"], result.run_id)
            self.assertEqual(
                json.loads((run_directory / "complete.json").read_text())["run_id"],
                result.run_id,
            )


if __name__ == "__main__":
    unittest.main()
