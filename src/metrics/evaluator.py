from .scorer import Scorer


def compute_all_metrics(ground_truth, estimated):
    """Compatibility wrapper that scores all registered metrics for one run."""
    return Scorer().score(ground_truth, estimated)
