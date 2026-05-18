import copy
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from shapiq.interaction_values import InteractionValues


def is_interaction_values(value) -> bool:
    """Return whether a value looks like a shapiq InteractionValues object."""
    return hasattr(value, "interaction_lookup") and hasattr(value, "values")


def remove_empty_value_if_needed(value):
    """Return a copy where the empty interaction value is set to zero.

    The empty interaction represents the baseline. It should not influence the
    benchmark metrics, so InteractionValues inputs are copied and adjusted before
    conversion to arrays. Non-InteractionValues inputs are returned unchanged.
    """
    if not is_interaction_values(value):
        return value

    try:
        new_value = copy.deepcopy(value)
        empty_index = new_value.interaction_lookup[()]
        new_value.values[empty_index] = 0
        return new_value
    except KeyError:
        return value


def as_metric_array(value) -> np.ndarray:
    """Convert arrays or InteractionValues-like objects into float arrays."""
    value = remove_empty_value_if_needed(value)

    if is_interaction_values(value):
        return np.asarray(value.values, dtype=float)

    return np.asarray(value, dtype=float)


def prepare_metric_inputs(ground_truth, estimated) -> tuple[np.ndarray, np.ndarray]:
    """Convert and validate the two arrays passed to metric implementations."""
    ground_truth_array = as_metric_array(ground_truth)
    estimated_array = as_metric_array(estimated)

    if ground_truth_array.shape != estimated_array.shape:
        raise ValueError(
            "Metric inputs must have the same shape. "
            f"Got ground_truth shape {ground_truth_array.shape} and "
            f"estimated shape {estimated_array.shape}."
        )

    return ground_truth_array, estimated_array
