import unittest

from tsp_perm_ea_bench.algorithms.baselines import run_random_search
from tsp_perm_ea_bench.observers.events import MemoryObserver
from tsp_perm_ea_bench.problems.tsp import TSPProblem


class RandomSearchTests(unittest.TestCase):
    def test_random_search_uses_the_shared_budget_protocol(self) -> None:
        problem = TSPProblem.from_matrix(
            "baseline",
            (
                (0, 2, 3),
                (2, 0, 1),
                (3, 1, 0),
            ),
        )
        observer = MemoryObserver()
        result = run_random_search(
            problem,
            offspring_budget=5,
            master_seed=1000,
            instance_id="baseline",
            repeat=0,
            observer=observer,
        )

        self.assertEqual(result.counters["initial_evaluations"], 0)
        self.assertEqual(result.counters["offspring_evaluations"], 5)
        self.assertEqual(result.counters["total_evaluations"], 5)
        self.assertEqual(result.termination_reason, "budget_exhausted")


if __name__ == "__main__":
    unittest.main()
