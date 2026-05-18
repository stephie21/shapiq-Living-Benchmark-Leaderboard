"""Base interface for benchmark metrics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .result import MetricResult


class Metric(ABC):
    """Abstract base class for scalar benchmark metrics."""

    name = "base"
    higher_is_better = False

    @abstractmethod
    def compute(self, ground_truth: object, estimated: object, **params: object) -> MetricResult:
        """Compute the metric value for aligned reference and estimated values."""
        raise NotImplementedError
