import numpy as np

from .base import Metric
from .result import MetricResult


class MSEMetric(Metric):
    """Mean squared error between reference and estimated values."""

    name = "mse"
    higher_is_better = False

    def compute(self, ground_truth, estimated, **params) -> MetricResult:
        """Compute ``mean((ground_truth - estimated) ** 2)``."""
        difference = ground_truth - estimated

        return MetricResult(
            metric_name=self.name,
            value=float(np.mean(difference ** 2)),
            higher_is_better=self.higher_is_better,
        )


class MAEMetric(Metric):
    """Mean absolute error between reference and estimated values."""

    name = "mae"
    higher_is_better = False

    def compute(self, ground_truth, estimated, **params) -> MetricResult:
        """Compute ``mean(abs(ground_truth - estimated))``."""
        difference = ground_truth - estimated

        return MetricResult(
            metric_name=self.name,
            value=float(np.mean(np.abs(difference))),
            higher_is_better=self.higher_is_better,
        )


class NormalizedMSEMetric(Metric):
    """Mean squared error normalized by the reference variance."""

    name = "mse_normalized"
    higher_is_better = False

    def compute(self, ground_truth, estimated, **params) -> MetricResult:
        """Compute normalized MSE, falling back to MSE for zero variance."""
        difference = ground_truth - estimated
        mse = np.mean(difference ** 2)
        variance = np.var(ground_truth)

        if variance == 0:
            value = float(mse)
        else:
            value = float(mse / variance)

        return MetricResult(
            metric_name=self.name,
            value=value,
            higher_is_better=self.higher_is_better,
        )


class R2Metric(Metric):
    """R-squared reconstruction faithfulness metric."""

    name = "r2"
    higher_is_better = True

    def compute(self, ground_truth, estimated, **params) -> MetricResult:
        """Compute ``1 - residual_sum_of_squares / total_sum_of_squares``."""
        residual_sum_of_squares = np.sum((estimated - ground_truth) ** 2)
        total_sum_of_squares = np.sum((ground_truth - np.mean(ground_truth)) ** 2)

        if total_sum_of_squares == 0:
            value = float(np.nan)
        else:
            value = float(1 - residual_sum_of_squares / total_sum_of_squares)

        return MetricResult(
            metric_name=self.name,
            value=value,
            higher_is_better=self.higher_is_better,
        )
