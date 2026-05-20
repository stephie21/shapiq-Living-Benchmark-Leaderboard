"""Ranking-based benchmark metric implementations."""

from __future__ import annotations

import numpy as np
from scipy.stats import kendalltau, spearmanr

from .base import Metric
from .result import MetricResult


class SpearmanMetric(Metric):
    """Spearman rank correlation between reference and estimated values."""

    name = "spearman"
    higher_is_better = True

    def compute(
        self,
        ground_truth: np.ndarray,
        estimated: np.ndarray,
        **_params: object,
    ) -> MetricResult:
        """Compute Spearman correlation and report undefined results as 0."""
        correlation, _ = spearmanr(ground_truth, estimated)

        if np.isnan(correlation):
            correlation = 0.0

        return MetricResult(
            metric_name=self.name,
            value=float(correlation),
            higher_is_better=self.higher_is_better,
        )


class KendallTauMetric(Metric):
    """Kendall tau rank correlation between reference and estimated values."""

    name = "kendall_tau"
    higher_is_better = True

    def compute(
        self,
        ground_truth: np.ndarray,
        estimated: np.ndarray,
        **_params: object,
    ) -> MetricResult:
        """Compute Kendall tau and report undefined results as 0."""
        correlation, _ = kendalltau(ground_truth, estimated)

        if np.isnan(correlation):
            correlation = 0.0

        return MetricResult(
            metric_name=self.name,
            value=float(correlation),
            higher_is_better=self.higher_is_better,
        )


class PrecisionAtKMetric(Metric):
    """Top-k overlap between strongest reference and estimated values."""

    name = "precision_at_k"
    higher_is_better = True

    def compute(
        self,
        ground_truth: np.ndarray,
        estimated: np.ndarray,
        **params: object,
    ) -> MetricResult:
        """Compute overlap of the top-k absolute values in both arrays."""
        k = int(params.get("k", 10))
        if k <= 0:
            msg = "precision_at_k requires k > 0."
            raise ValueError(msg)

        if ground_truth.size == 0:
            value = float(np.nan)
        else:
            k = min(k, ground_truth.size)
            truth_indices = set(np.argsort(np.abs(ground_truth))[-k:])
            estimated_indices = set(np.argsort(np.abs(estimated))[-k:])
            value = len(truth_indices & estimated_indices) / k

        return MetricResult(
            metric_name=self.name,
            value=float(value),
            higher_is_better=self.higher_is_better,
        )
