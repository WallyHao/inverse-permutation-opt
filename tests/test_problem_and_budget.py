import unittest
from pathlib import Path

from tsp_perm_ea_bench.core.budget import (
    BudgetExceeded,
    EvaluationContext,
    EvaluationPhase,
    TerminationReason,
)
from tsp_perm_ea_bench.problems.metrics import (
    edge_distance,
    edge_set,
    exact_population_edge_distance,
)
from tsp_perm_ea_bench.problems.tsp import (
    ProblemFormatError,
    ReferenceStatus,
    TSPProblem,
    load_tsplib,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = REPOSITORY_ROOT / "benchmarks" / "instances"


class TSPProblemTests(unittest.TestCase):
    def test_closed_tour_and_rotation_have_same_length(self) -> None:
        problem = load_tsplib(
            BENCHMARK_ROOT / "square.tsp",
            reference_value=4,
            reference_status=ReferenceStatus.PROVEN_OPTIMUM,
            reference_tour=(0, 1, 2, 3),
        )

        self.assertEqual(problem.evaluate((0, 1, 2, 3)), 4)
        self.assertEqual(problem.evaluate((1, 2, 3, 0)), 4)
        self.assertEqual(problem.to_original_tour((0, 2, 1, 3)), (1, 3, 2, 4))

    def test_invalid_tours_are_rejected_without_repair(self) -> None:
        problem = load_tsplib(BENCHMARK_ROOT / "triangle.tsp")

        with self.assertRaises(ValueError):
            problem.evaluate((0, 1))
        with self.assertRaises(ValueError):
            problem.evaluate((0, 0, 1))
        with self.assertRaises(ValueError):
            problem.evaluate((0, 1, 4))

    def test_tsplib_rounding_is_nearest_integer(self) -> None:
        problem = load_tsplib(BENCHMARK_ROOT / "rounding-boundary.tsp")

        self.assertEqual(problem.distances[0][1], 2)
        self.assertEqual(problem.distances[0][2], 3)
        self.assertEqual(problem.distances[1][2], 3)

    def test_unsupported_format_is_rejected(self) -> None:
        with self.assertRaises(ProblemFormatError):
            TSPProblem.from_matrix("bad", ((0, 1), (1, 0)))


class MetricTests(unittest.TestCase):
    def test_closed_edges_include_the_last_to_first_edge(self) -> None:
        self.assertEqual(edge_set((0, 1, 2, 3)), {(0, 1), (1, 2), (2, 3), (0, 3)})

    def test_rotations_and_reversals_share_edges(self) -> None:
        tour = (0, 1, 2, 3)
        self.assertEqual(edge_distance(tour, (2, 3, 0, 1)), 0.0)
        self.assertEqual(edge_distance(tour, (0, 3, 2, 1)), 0.0)

    def test_population_formula_matches_pairwise_definition(self) -> None:
        population = [(0, 1, 2), (1, 2, 0), (0, 2, 1)]
        pairwise = sum(
            edge_distance(population[index], population[jndex])
            for index in range(len(population))
            for jndex in range(index + 1, len(population))
        ) / 3
        self.assertEqual(exact_population_edge_distance(population), pairwise)


class EvaluationContextTests(unittest.TestCase):
    def test_counters_separate_initialization_and_offspring_budget(self) -> None:
        problem = TSPProblem.from_matrix(
            "triangle",
            ((0, 1, 1), (1, 0, 1), (1, 1, 0)),
        )
        context = EvaluationContext(problem, offspring_budget=2)

        context.evaluate((0, 1, 2), phase=EvaluationPhase.INITIALIZATION)
        context.evaluate((0, 2, 1), phase=EvaluationPhase.OFFSPRING)
        context.evaluate((1, 0, 2), phase=EvaluationPhase.OFFSPRING)

        self.assertEqual(context.counters.initial_evaluations, 1)
        self.assertEqual(context.counters.offspring_evaluations, 2)
        self.assertEqual(context.counters.total_evaluations, 3)
        context.finish_if_budget_exhausted()
        self.assertEqual(context.termination_reason, TerminationReason.BUDGET_EXHAUSTED)
        with self.assertRaises(BudgetExceeded):
            context.evaluate((0, 1, 2), phase=EvaluationPhase.OFFSPRING)

    def test_proven_optimum_stops_after_the_successful_evaluation(self) -> None:
        problem = TSPProblem.from_matrix(
            "triangle",
            ((0, 1, 1), (1, 0, 1), (1, 1, 0)),
            reference_value=3,
            reference_status=ReferenceStatus.PROVEN_OPTIMUM,
        )
        context = EvaluationContext(problem, offspring_budget=3)

        result = context.evaluate((0, 1, 2), phase=EvaluationPhase.OFFSPRING)

        self.assertTrue(result.reached_proven_optimum)
        self.assertEqual(context.termination_reason, TerminationReason.OPTIMUM_REACHED)
        self.assertEqual(context.counters.total_evaluations, 1)


if __name__ == "__main__":
    unittest.main()
