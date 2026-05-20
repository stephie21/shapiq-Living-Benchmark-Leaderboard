"""Compatibility helpers for computing benchmark metrics."""

from __future__ import annotations

from .scorer import Scorer


def compute_all_metrics(ground_truth: object, estimated: object) -> dict[str, float | None]:
    """Compatibility wrapper that scores all registered metrics for one run."""
    return Scorer().score(ground_truth, estimated)
