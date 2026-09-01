"""Meta-evaluation metrics for the automated judge cascade."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ReliabilityThresholds:
    alpha_min: float = 0.67
    human_alpha_fraction_min: float = 0.90
    icc_min: float = 0.85
    aggregate_mae_max: float = 5.0
    macro_f1_min: float = 0.85
    balanced_accuracy_min: float = 0.85
    full_hit_precision_min: float = 0.90
    critical_false_positive_max: float = 0.05
    invariance_min: float = 0.95
    deletion_sensitivity_min: float = 0.90
    coverage_min: float = 0.70
    accepted_agreement_min: float = 0.95


@dataclass(frozen=True)
class ReliabilityReport:
    krippendorff_alpha: float
    human_human_alpha: float
    alpha_fraction: float
    aggregate_icc: float
    aggregate_mae: float
    macro_f1: float
    balanced_accuracy: float
    full_hit_precision: float
    critical_false_positive_rate: float
    invariance: float
    deletion_sensitivity: float
    coverage: float
    accepted_agreement: float
    passed: bool
    failures: tuple[str, ...]


def krippendorff_alpha_ordinal(ratings: np.ndarray) -> float:
    """Krippendorff alpha for complete ordinal ratings (rows=items, cols=raters)."""
    ratings = np.asarray(ratings, dtype=float)
    if ratings.ndim != 2 or ratings.shape[1] < 2:
        raise ValueError("ratings must have at least two raters")
    categories = np.unique(ratings[~np.isnan(ratings)])
    if len(categories) <= 1:
        return 1.0
    scale = float(categories.max() - categories.min()) or 1.0
    observed: list[float] = []
    for row in ratings:
        values = row[~np.isnan(row)]
        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                observed.append(((values[i] - values[j]) / scale) ** 2)
    do = float(np.mean(observed)) if observed else 0.0
    pooled = ratings[~np.isnan(ratings)]
    expected = [
        ((pooled[i] - pooled[j]) / scale) ** 2
        for i in range(len(pooled))
        for j in range(i + 1, len(pooled))
    ]
    de = float(np.mean(expected)) if expected else 0.0
    return 1.0 if de == 0 else 1.0 - do / de


def icc_absolute_agreement(targets: np.ndarray, predictions: np.ndarray) -> float:
    """Two-rater ICC(A,1), suitable for aggregate human-vs-judge scores."""
    matrix = np.column_stack([targets, predictions]).astype(float)
    n, k = matrix.shape
    grand = matrix.mean()
    row_means = matrix.mean(axis=1)
    col_means = matrix.mean(axis=0)
    ms_rows = k * np.sum((row_means - grand) ** 2) / max(1, n - 1)
    ms_cols = n * np.sum((col_means - grand) ** 2) / max(1, k - 1)
    residual = matrix - row_means[:, None] - col_means[None, :] + grand
    ms_error = np.sum(residual**2) / max(1, (n - 1) * (k - 1))
    denominator = ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n
    return float((ms_rows - ms_error) / denominator) if denominator else 1.0


def _classification_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[float, float]:
    labels = np.unique(np.concatenate([y_true, y_pred]))
    f1s: list[float] = []
    recalls: list[float] = []
    for label in labels:
        true_positive = np.sum((y_true == label) & (y_pred == label))
        false_positive = np.sum((y_true != label) & (y_pred == label))
        false_negative = np.sum((y_true == label) & (y_pred != label))
        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0
        )
        f1s.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
        recalls.append(recall)
    return float(np.mean(f1s)), float(np.mean(recalls))


def evaluate_reliability(
    expert_labels: list[float],
    judge_labels: list[float | None],
    second_expert_labels: list[float],
    expert_aggregate_scores: list[float],
    judge_aggregate_scores: list[float],
    first_expert_labels: list[float] | None = None,
    critical_mask: list[bool] | None = None,
    invariance: float = 1.0,
    deletion_sensitivity: float = 1.0,
    thresholds: ReliabilityThresholds | None = None,
) -> ReliabilityReport:
    thresholds = thresholds or ReliabilityThresholds()
    if not (len(expert_labels) == len(judge_labels) == len(second_expert_labels)):
        raise ValueError("label arrays must have equal length")
    if first_expert_labels is not None and len(first_expert_labels) != len(expert_labels):
        raise ValueError("first expert labels must have equal length")
    accepted_mask = np.array([label is not None for label in judge_labels], dtype=bool)
    coverage = float(accepted_mask.mean()) if len(accepted_mask) else 0.0
    y_true = np.asarray(expert_labels, dtype=float)[accepted_mask]
    y_pred = np.asarray([label for label in judge_labels if label is not None], dtype=float)
    if not len(y_true):
        raise ValueError("at least one automated judgment must be accepted")
    alpha = krippendorff_alpha_ordinal(np.column_stack([y_true, y_pred]))
    human_alpha = krippendorff_alpha_ordinal(
        np.column_stack([first_expert_labels or expert_labels, second_expert_labels])
    )
    alpha_fraction = alpha / human_alpha if human_alpha > 0 else 1.0
    macro_f1, balanced_accuracy = _classification_metrics(y_true, y_pred)
    full_pred = y_pred == 1.0
    full_hit_precision = float(np.mean(y_true[full_pred] == 1.0)) if np.any(full_pred) else 1.0
    critical = np.asarray(critical_mask or [False] * len(expert_labels), dtype=bool)[accepted_mask]
    false_positive = (y_pred > y_true) & critical
    critical_denominator = np.sum(critical & (y_true < 1.0))
    critical_fpr = (
        float(np.sum(false_positive) / critical_denominator) if critical_denominator else 0.0
    )
    accepted_agreement = float(np.mean(y_true == y_pred))
    aggregate_icc = icc_absolute_agreement(
        np.asarray(expert_aggregate_scores), np.asarray(judge_aggregate_scores)
    )
    aggregate_mae = float(
        np.mean(np.abs(np.asarray(expert_aggregate_scores) - np.asarray(judge_aggregate_scores)))
    )
    checks = {
        "krippendorff_alpha": alpha >= thresholds.alpha_min,
        "human_alpha_fraction": alpha_fraction >= thresholds.human_alpha_fraction_min,
        "aggregate_icc": aggregate_icc >= thresholds.icc_min,
        "aggregate_mae": aggregate_mae <= thresholds.aggregate_mae_max,
        "macro_f1": macro_f1 >= thresholds.macro_f1_min,
        "balanced_accuracy": balanced_accuracy >= thresholds.balanced_accuracy_min,
        "full_hit_precision": full_hit_precision >= thresholds.full_hit_precision_min,
        "critical_false_positive_rate": critical_fpr <= thresholds.critical_false_positive_max,
        "invariance": invariance >= thresholds.invariance_min,
        "deletion_sensitivity": deletion_sensitivity >= thresholds.deletion_sensitivity_min,
        "coverage": coverage >= thresholds.coverage_min,
        "accepted_agreement": accepted_agreement >= thresholds.accepted_agreement_min,
    }
    failures = tuple(name for name, passed in checks.items() if not passed)
    return ReliabilityReport(
        krippendorff_alpha=alpha,
        human_human_alpha=human_alpha,
        alpha_fraction=alpha_fraction,
        aggregate_icc=aggregate_icc,
        aggregate_mae=aggregate_mae,
        macro_f1=macro_f1,
        balanced_accuracy=balanced_accuracy,
        full_hit_precision=full_hit_precision,
        critical_false_positive_rate=critical_fpr,
        invariance=invariance,
        deletion_sensitivity=deletion_sensitivity,
        coverage=coverage,
        accepted_agreement=accepted_agreement,
        passed=not failures,
        failures=failures,
    )
