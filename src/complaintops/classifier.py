from __future__ import annotations

import math
import re
from collections import Counter, defaultdict


TOKEN_PATTERN = re.compile(r"[a-z][a-z']+")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


class MultinomialNB:
    """Small, inspectable multinomial Naive Bayes baseline."""

    def __init__(self, alpha: float = 1.0) -> None:
        self.alpha = alpha
        self.class_counts: Counter[str] = Counter()
        self.token_counts: dict[str, Counter[str]] = defaultdict(Counter)
        self.total_tokens: Counter[str] = Counter()
        self.vocabulary: set[str] = set()

    def fit(self, texts: list[str], labels: list[str]) -> "MultinomialNB":
        if len(texts) != len(labels) or not texts:
            raise ValueError("texts and labels must be non-empty and aligned")
        self.class_counts.clear()
        self.token_counts.clear()
        self.total_tokens.clear()
        self.vocabulary.clear()
        for text, label in zip(texts, labels):
            tokens = tokenize(text)
            self.class_counts[label] += 1
            self.token_counts[label].update(tokens)
            self.total_tokens[label] += len(tokens)
            self.vocabulary.update(tokens)
        return self

    def predict_proba(self, text: str) -> dict[str, float]:
        if not self.class_counts:
            raise RuntimeError("Model must be fitted before prediction")
        total_docs = sum(self.class_counts.values())
        vocab_size = max(1, len(self.vocabulary))
        scores: dict[str, float] = {}
        for label, count in self.class_counts.items():
            score = math.log(count / total_docs)
            denominator = self.total_tokens[label] + self.alpha * vocab_size
            for token in tokenize(text):
                if token not in self.vocabulary:
                    continue
                numerator = self.token_counts[label][token] + self.alpha
                score += math.log(numerator / denominator)
            scores[label] = score
        peak = max(scores.values())
        exponentials = {label: math.exp(score - peak) for label, score in scores.items()}
        normalizer = sum(exponentials.values())
        return {label: value / normalizer for label, value in exponentials.items()}

    def predict(self, text: str) -> str:
        probabilities = self.predict_proba(text)
        return max(probabilities, key=probabilities.get)


def classification_metrics(actual: list[str], predicted: list[str]) -> dict[str, float]:
    if len(actual) != len(predicted) or not actual:
        raise ValueError("actual and predicted must be non-empty and aligned")
    labels = sorted(set(actual) | set(predicted))
    accuracy = sum(a == p for a, p in zip(actual, predicted)) / max(1, len(actual))
    f1_values = []
    for label in labels:
        tp = sum(a == label and p == label for a, p in zip(actual, predicted))
        fp = sum(a != label and p == label for a, p in zip(actual, predicted))
        fn = sum(a == label and p != label for a, p in zip(actual, predicted))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1_values.append(
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
    return {"accuracy": accuracy, "macro_f1": sum(f1_values) / max(1, len(f1_values))}


def selective_routing_metrics(
    actual: list[str],
    predicted: list[str],
    confidences: list[float],
    threshold: float = 0.75,
) -> dict[str, float | int]:
    """Evaluate an auto-route policy that sends low-confidence cases to review."""
    if len(actual) != len(predicted) or len(actual) != len(confidences) or not actual:
        raise ValueError("routing inputs must be non-empty and aligned")
    selected = [index for index, confidence in enumerate(confidences) if confidence >= threshold]
    correct = sum(actual[index] == predicted[index] for index in selected)
    coverage = len(selected) / len(actual)
    return {
        "threshold": threshold,
        "auto_routed": len(selected),
        "coverage": coverage,
        "review_rate": 1.0 - coverage,
        "accuracy": correct / len(selected) if selected else 0.0,
    }


def choose_confidence_threshold(
    actual: list[str],
    predicted: list[str],
    confidences: list[float],
    target_accuracy: float = 0.85,
    minimum_coverage: float = 0.50,
) -> dict[str, float | int]:
    """Choose maximum coverage meeting an accuracy target on calibration data."""
    candidates = sorted(set(confidences) | {0.0})
    evaluated = [
        selective_routing_metrics(actual, predicted, confidences, threshold)
        for threshold in candidates
    ]
    eligible = [
        metrics
        for metrics in evaluated
        if float(metrics["accuracy"]) >= target_accuracy
        and float(metrics["coverage"]) >= minimum_coverage
    ]
    if eligible:
        selected = max(eligible, key=lambda metrics: float(metrics["coverage"]))
    else:
        fallback = [
            metrics
            for metrics in evaluated
            if float(metrics["coverage"]) >= minimum_coverage
        ] or evaluated
        selected = max(
            fallback,
            key=lambda metrics: (float(metrics["accuracy"]), float(metrics["coverage"])),
        )
    return {
        **selected,
        "target_accuracy": target_accuracy,
        "minimum_coverage": minimum_coverage,
    }
