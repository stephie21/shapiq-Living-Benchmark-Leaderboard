from dataclasses import dataclass

from .base import Metric
from .distance_metrics import MAEMetric, MSEMetric, NormalizedMSEMetric, R2Metric
from .ranking_metrics import KendallTauMetric, PrecisionAtKMetric, SpearmanMetric


@dataclass(frozen=True)
class MetricSpec:
    """Metadata and implementation for one benchmark metric."""

    name: str
    function: Metric
    higher_is_better: bool
    category: str
    description: str


METRIC_SPECS = {
    "mse": MetricSpec(
        name="mse",
        function=MSEMetric(),
        higher_is_better=False,
        category="error",
        description="Mean squared error between reference and estimated values.",
    ),
    "mae": MetricSpec(
        name="mae",
        function=MAEMetric(),
        higher_is_better=False,
        category="error",
        description="Mean absolute error between reference and estimated values.",
    ),
    "mse_normalized": MetricSpec(
        name="mse_normalized",
        function=NormalizedMSEMetric(),
        higher_is_better=False,
        category="error",
        description="Mean squared error normalized by the reference variance.",
    ),
    "r2": MetricSpec(
        name="r2",
        function=R2Metric(),
        higher_is_better=True,
        category="faithfulness",
        description="R-squared reconstruction faithfulness score.",
    ),
    "spearman": MetricSpec(
        name="spearman",
        function=SpearmanMetric(),
        higher_is_better=True,
        category="rank_correlation",
        description="Spearman rank correlation between reference and estimated values.",
    ),
    "kendall_tau": MetricSpec(
        name="kendall_tau",
        function=KendallTauMetric(),
        higher_is_better=True,
        category="rank_correlation",
        description="Kendall tau rank correlation between reference and estimated values.",
    ),
    "precision_at_k": MetricSpec(
        name="precision_at_k",
        function=PrecisionAtKMetric(),
        higher_is_better=True,
        category="top_k",
        description="Overlap between the top-k absolute reference and estimated values.",
    ),
}

# Canonical keys are the names stored in run_record["metrics"].
METRIC_KEYS = tuple(METRIC_SPECS.keys())
METRIC_ALIASES = {
    "normalized_mse": "mse_normalized",
}

# METRICS keeps the previous public lookup style while MetricSpec stores metadata.
METRICS = {name: spec.function for name, spec in METRIC_SPECS.items()}
METRICS.update({alias: METRICS[name] for alias, name in METRIC_ALIASES.items()})
