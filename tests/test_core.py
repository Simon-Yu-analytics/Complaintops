import unittest

from complaintops.classifier import MultinomialNB, classification_metrics
from complaintops.forecast import moving_average_forecast
from complaintops.optimize import staffing_plan


class ClassifierTests(unittest.TestCase):
    def test_learns_product_language(self):
        model = MultinomialNB().fit(
            ["incorrect credit report account", "card charged duplicate purchase", "credit bureau dispute", "card annual fee"],
            ["Credit reporting", "Credit card", "Credit reporting", "Credit card"],
        )
        self.assertEqual(model.predict("credit bureau account dispute"), "Credit reporting")

    def test_metrics_are_bounded(self):
        metrics = classification_metrics(["a", "a", "b"], ["a", "b", "b"])
        self.assertGreaterEqual(metrics["macro_f1"], 0)
        self.assertLessEqual(metrics["accuracy"], 1)


class ForecastTests(unittest.TestCase):
    def test_moving_average_horizon(self):
        self.assertEqual(moving_average_forecast([10, 12, 14, 16], horizon=2), [13, 14])


class OptimizerTests(unittest.TestCase):
    def test_capacity_covers_buffered_peak(self):
        plan = staffing_plan({"Cards": [40, 60, 50]}, cases_per_agent_week=45, service_level_buffer=1.1)
        team = plan["teams"][0]
        self.assertGreaterEqual(team["weekly_capacity"], 60 * 1.1)


if __name__ == "__main__":
    unittest.main()

