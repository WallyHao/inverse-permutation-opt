import csv
import json
import tempfile
import unittest
from pathlib import Path

from tsp_perm_ea_bench.analysis.metrics import ert, first_hit, gap_ratio
from tsp_perm_ea_bench.analysis.summarize import summarize_experiment
from tsp_perm_ea_bench.core.config import ExperimentSpec
from tsp_perm_ea_bench.runner.batch import BatchRunner


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class AnalysisMetricTests(unittest.TestCase):
    def test_gap_keeps_negative_best_known_values(self) -> None:
        self.assertEqual(gap_ratio(95, 100), -0.05)

    def test_first_hit_and_ert_preserve_right_censoring(self) -> None:
        checkpoints = [(0, 130), (4, 110), (8, 100)]
        self.assertEqual(first_hit(checkpoints, reference_value=100, target_gap=0.0), 8)
        self.assertEqual(ert([8, None, 4], budget=10), 22 / 2)
        self.assertIsNone(ert([None, None], budget=10))


class BatchAndAnalysisTests(unittest.TestCase):
    def test_batch_runner_is_resumable_and_analysis_is_rebuildable(self) -> None:
        spec = ExperimentSpec.from_file(
            REPOSITORY_ROOT / "configs" / "development-smoke.json"
        )
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary) / "results"
            runner = BatchRunner(
                spec,
                repository_root=REPOSITORY_ROOT,
                output_root=output_root,
            )
            first = runner.run()
            second = runner.run()
            self.assertEqual(len(first), 8)
            self.assertTrue(all(item["status"] == "success" for item in first))
            self.assertEqual(
                [item["attempt_id"] for item in first],
                [item["attempt_id"] for item in second],
            )

            experiment_directory = output_root / spec.experiment_id
            experiment_json = json.loads(
                (experiment_directory / "experiment.json").read_text()
            )
            self.assertEqual(experiment_json["experiment_id"], spec.experiment_id)
            analysis_directory = summarize_experiment(experiment_directory)
            with (analysis_directory / "final_summary.csv").open(newline="") as handle:
                final_rows = list(csv.DictReader(handle))
            self.assertEqual(len(final_rows), 8)
            self.assertTrue((analysis_directory / "convergence.svg").is_file())


if __name__ == "__main__":
    unittest.main()
