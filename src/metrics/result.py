"""Metric result data structures."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MetricResult:
    """Scalar result returned by a metric implementation."""

    metric_name: str
    value: float
    higher_is_better: bool
