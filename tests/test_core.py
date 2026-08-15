import csv
import tempfile
import unittest
from pathlib import Path

from complaintops import __version__
from complaintops.classifier import (
    MultinomialNB,
    choose_confidence_threshold,
    classification_metrics,
    selective_routing_metrics,
)
from complaintops.data import load_complaints
from complaintops.forecast import moving_average_forecast, select_method
from complaintops.optimize import staffing_plan
from complaintops.pipeline import temporal_split


class ClassifierTests(unittest.TestCase):
    def test_learns_product_language(self):
        model = MultinomialNB().fit(
            [
                "incorrect credit report account",
                "card charged duplicate purchase",
                "credit bureau dispute",
                "card annual fee",
            ],
            ["Credit reporting", "Credit card", "Credit reporting", "Credit card"],
        )
        self.assertEqual(model.predict("credit bureau account dispute"), "Credit reporting")

    def test_metrics_are_bounded(self):
        metrics = classification_metrics(["a", "a", "b"], ["a", "b", "b"])
        self.assertGreaterEqual(metrics["macro_f1"], 0)
        self.assertLessEqual(metrics["accuracy"], 1)

    def test_metrics_reject_misaligned_inputs(self):
        with self.assertRaises(ValueError):
            classification_metrics(["a"], ["a", "b"])

    def test_refit_replaces_previous_state(self):
        model = MultinomialNB().fit(["credit report"], ["Reporting"])
        model.fit(["mortgage escrow"], ["Mortgage"])
        self.assertEqual(set(model.class_counts), {"Mortgage"})
        self.assertEqual(model.predict("mortgage escrow"), "Mortgage")

    def test_low_confidence_cases_go_to_review(self):
        metrics = selective_routing_metrics(
            ["a", "b", "b"], ["a", "a", "b"], [0.95, 0.55, 0.85], threshold=0.75
        )
        self.assertEqual(metrics["auto_routed"], 2)
        self.assertAlmostEqual(metrics["accuracy"], 1.0)
        self.assertAlmostEqual(metrics["review_rate"], 1 / 3)

    def test_threshold_is_selected_on_accuracy_target(self):
        policy = choose_confidence_threshold(
            ["a", "b", "b", "a"],
            ["a", "a", "b", "a"],
            [0.95, 0.55, 0.85, 0.70],
            target_accuracy=0.9,
            minimum_coverage=0.5,
        )
        self.assertGreaterEqual(policy["accuracy"], 0.9)
        self.assertGreaterEqual(policy["coverage"], 0.5)


class ForecastTests(unittest.TestCase):
    def test_moving_average_horizon(self):
        self.assertEqual(moving_average_forecast([10, 12, 14, 16], horizon=2), [13, 14])

    def test_method_selection_finds_linear_trend(self):
        method, scores = select_method(list(range(10, 40)))
        self.assertEqual(method, "trend8")
        self.assertLess(scores[method], scores["naive"])


class OptimizerTests(unittest.TestCase):
    def test_capacity_covers_buffered_peak(self):
        plan = staffing_plan(
            {"Cards": [40, 60, 50]},
            cases_per_agent_week=45,
            service_level_buffer=1.1,
        )
        team = plan["teams"][0]
        self.assertGreaterEqual(team["weekly_capacity"], 60 * 1.1)

    def test_upper_interval_drives_capacity(self):
        plan = staffing_plan(
            {"Cards": [20, 22]},
            upper_forecast={"Cards": [28, 31]},
            cases_per_agent_week=24,
        )
        team = plan["teams"][0]
        self.assertEqual(team["planning_demand"], 31)
        self.assertGreaterEqual(team["weekly_capacity"], 31)
        self.assertEqual(plan["assumptions"]["forecast_interval_coverage"], 0.8)


class PipelineTests(unittest.TestCase):
    def test_temporal_split_has_no_date_overlap(self):
        rows = [
            {"complaint_id": str(index), "date_received": f"2025-01-{index:02d}"}
            for index in range(1, 11)
        ]
        train, test, cutoff = temporal_split(rows, test_fraction=0.3)
        self.assertTrue(all(row["date_received"] < cutoff for row in train))
        self.assertTrue(all(row["date_received"] >= cutoff for row in test))


class MetadataTests(unittest.TestCase):
    def test_package_version_matches_project_metadata(self):
        pyproject = (Path(__file__).parents[1] / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn(f'version = "{__version__}"', pyproject)


class DataTests(unittest.TestCase):
    def test_loader_rejects_missing_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=["complaint_id"])
                writer.writeheader()
                writer.writerow({"complaint_id": "1"})
            with self.assertRaises(ValueError):
                load_complaints(path)

    def test_loader_rejects_duplicate_ids(self):
        fields = [
            "complaint_id",
            "date_received",
            "product",
            "issue",
            "narrative",
            "state",
            "submitted_via",
        ]
        row = {
            "complaint_id": "C-1",
            "date_received": "2025-01-01",
            "product": "Credit card",
            "issue": "Fees",
            "narrative": "A duplicate fee appeared.",
            "state": "WA",
            "submitted_via": "Web",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicates.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows([row, row])
            with self.assertRaisesRegex(ValueError, "Duplicate complaint_id"):
                load_complaints(path)

    def test_loader_rejects_invalid_dates(self):
        fields = [
            "complaint_id",
            "date_received",
            "product",
            "issue",
            "narrative",
            "state",
            "submitted_via",
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid_date.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "complaint_id": "C-1",
                        "date_received": "2025-02-30",
                        "product": "Credit card",
                        "issue": "Fees",
                        "narrative": "A duplicate fee appeared.",
                        "state": "WA",
                        "submitted_via": "Web",
                    }
                )
            with self.assertRaisesRegex(ValueError, "Invalid date_received"):
                load_complaints(path)


if __name__ == "__main__":
    unittest.main()
