# Benchmark Metrics

This page documents the implemented metrics subsystem. It uses three evidence labels throughout:

* **Repository implementation evidence** means behavior present in the repository code or tests named here.
* **Literature evidence** means a claim supported by the cited papers.
* **Proposed benchmark-specific design** means a benchmark reporting protocol described here, not a completed production feature.

## Contribution Scope

This work focuses on the metrics subsystem.
## Metrics Overview

**Implemented. Repository implementation evidence.** The metrics subsystem is centered on `Metric`, `MetricResult`, and `MetricSpec`. The abstract metric API lives in `src/leaderboard/metrics/base.py`. Concrete metric classes live in `src/leaderboard/metrics/distance_metrics.py` and `src/leaderboard/metrics/ranking_metrics.py`. The registry in `src/leaderboard/metrics/registry.py` exposes `METRIC_KEYS`, `METRIC_SPECS`, and `METRICS`.

**Implemented. Repository implementation evidence.** The canonical metric keys are exactly:

* `mse`
* `mae`
* `mse_normalized`
* `r2`
* `spearman`
* `kendall_tau`
* `precision_at_k`

The input alias `normalized_mse` is accepted and maps to `mse_normalized`. It is not a separate canonical output key.

**Implemented. Repository implementation evidence.** `src/leaderboard/metrics/scorer.py` contains `Scorer.score`, which computes metric values for one run. `src/leaderboard/metrics/evaluator.py` contains `compute_all_metrics`, a wrapper for evaluating all registered metrics. `src/leaderboard/metrics/utils.py` contains `prepare_metric_inputs` and `_prepare_interaction_values`, which align inputs before metric computation.

**Implemented. Repository implementation evidence.** Tests in `tests/leaderboard/test_metrics.py` and `tests/leaderboard/test_ranking_metric.py` describe expected metric behavior, including `test_distance_metrics_parametrized_edge_values`, `test_r2_returns_nan_for_constant_ground_truth`, and `test_precision_at_k_uses_absolute_top_k_overlap`. Pairwise label-direction behavior is covered in `tests/leaderboard/test_pairwise_dataset.py` by `test_mse_lower_score_wins` and `test_spearman_higher_score_wins`.

## Metrics Package Structure

**Implemented. Repository implementation evidence.** The metrics package is split by contract, result transport, concrete metric families, registry metadata, input preparation, orchestration, and compatibility wrappers. The files below are the permitted metrics modules.

| File | Component type | Main responsibility | Why separate? | Imports | Used by |
| --- | --- | --- | --- | --- | --- |
| `__init__.py` | package API | Exports exactly `METRICS`, `METRIC_KEYS`, `METRIC_ALIASES`, `METRIC_SPECS`, and `Scorer` through `__all__`. `Metric`, `MetricResult`, concrete metric classes, and `compute_all_metrics` are not package-level exports. | Keeps the public package surface small while still exposing lookup metadata and the scorer. | `registry.METRICS`, `registry.METRIC_KEYS`, `registry.METRIC_ALIASES`, `registry.METRIC_SPECS`, `scorer.Scorer` | External imports and tests such as `test_public_api_exports_required_metrics` |
| `base.py` | abstract contract | Defines `Metric`, an ABC with class attributes `name = "base"` and `higher_is_better = False`. Its exact abstract method is `compute(self, ground_truth, estimated) -> MetricResult`, with two inputs only. | Gives every metric the same minimal compute contract without formula logic, input alignment, registry logic, or error policy. | `abc.ABC`, `abc.abstractmethod`, `MetricResult` | `distance_metrics.py`, `ranking_metrics.py` |
| `result.py` | result transport | Defines mutable `@dataclass` `MetricResult` with exactly `metric_name`, `value`, and `higher_is_better`. It carries values only and does no validation. | Lets metrics return a shared shape while `Scorer` can read `.value` and return a plain canonical dictionary. | `dataclasses.dataclass` | Concrete metrics and `Scorer.score` |
| `distance_metrics.py` | concrete distance metrics | Defines `MSEMetric`, `MAEMetric`, `NormalizedMSEMetric`, and `R2Metric`. MSE subtracts arrays and uses `np.mean(difference**2)`. MAE subtracts arrays and uses `np.mean(np.abs(...))`. Normalized MSE uses `np.var` and falls back to MSE when variance is zero. R2 converts with `np.array`, checks shapes explicitly, then uses squared sums, the mean, and `np.isclose` on the denominator. | Keeps value-distance formulas separate from rank or top-k semantics. These classes instantiate `MetricResult` and don't align common inputs. | `numpy`, `Metric`, `MetricResult` | `registry.py`, direct tests in `test_metrics.py` |
| `ranking_metrics.py` | concrete ranking metrics | Defines `SpearmanMetric`, `KendallTauMetric`, and `PrecisionAtKMetric`. Spearman and Kendall call SciPy `spearmanr` and `kendalltau` and map a NaN correlation to `0`. Precision@k compares absolute top-k membership, supports arrays and the original `InteractionValues` path, requires `k > 0`, checks shapes, and uses `_top_k_array_indices` and `_top_k_interaction_keys`. | Keeps ordering and membership metrics separate from numeric-distance metrics. `PrecisionAtKMetric` is the only concrete class with a narrower extra parameter, `k=10`. | `numpy`, `scipy.stats.kendalltau`, `scipy.stats.spearmanr`, `shapiq.InteractionValues`, `Metric`, `MetricResult` | `registry.py`, direct tests in `test_metrics.py` and `test_ranking_metric.py` |
| `registry.py` | registry module | Defines frozen dataclass `MetricSpec` with exactly `name`, `function`, `higher_is_better`, `category`, and `description`. Defines canonical ordered `METRIC_KEYS`, accepted external-to-canonical `METRIC_ALIASES`, canonical-to-spec `METRIC_SPECS`, and `METRICS`, which contains canonical executable objects plus alias keys. | Centralizes lookup, selection, canonical output order, alias handling, and direction reuse without conditional chains. | Concrete metric classes from `distance_metrics.py` and `ranking_metrics.py`, `dataclass` | `Scorer`, package API, pairwise code that reads metric direction, tests such as `test_registry_specs_match_public_metric_instances` |
| `utils.py` | input preparation functions | Defines `remove_empty_value_if_needed`, `prepare_metric_inputs`, `_prepare_interaction_values`, and `_values_for_interactions`. `remove_empty_value_if_needed` returns arrays unchanged. For `InteractionValues` with the `()` key, it deep copies and sets `interactions[()] = 0`. `prepare_metric_inputs` only special-cases when both inputs are `InteractionValues`; otherwise it calls `np.asarray(..., dtype=float)`, checks shape equality, and raises `ValueError` on mismatch. `_prepare_interaction_values` uses the sorted union of nonempty lookup keys ordered by `(len(key), key)`, and `_values_for_interactions` uses `0` for missing keys. | Isolates array coercion and the benchmark assumption for aligning two interaction-value objects. | `copy.deepcopy`, `numpy`, `shapiq.InteractionValues` | `Scorer.score`, direct tests such as `test_interaction_values_ignore_empty_key_and_align_union` |
| `scorer.py` | orchestration class | Defines `Scorer(metric_names=None, metric_params=None, fail_fast=False)`. Persistent attrs are `metric_names`, `metric_params`, and `fail_fast`. `_normalize_metric_names` expands `None` to all `METRIC_KEYS`, applies aliases, raises `KeyError` for unknown names, and de-dupes while preserving order. `_normalize_metric_params` applies aliases and raises `KeyError` for unknown metric names, but doesn't statically validate nested parameter dictionaries or target metric compatibility. `score` prepares shared inputs first, initializes empty results, iterates canonical `METRIC_KEYS`, returns `None` for unselected metrics, uses specs and params for selected metrics, keeps the original `InteractionValues` branch for Precision@k, catches all exceptions unless `fail_fast=True`, stores `float(value)`, and returns all canonical keys. | Keeps runtime control flow and failure policy out of formulas and metadata. It contains no metric formula. | `InteractionValues`, `METRIC_ALIASES`, `METRIC_KEYS`, `METRIC_SPECS`, `prepare_metric_inputs` | Callers that need configurable scoring, `evaluator.py`, tests such as `test_scorer_isolates_mocked_metric_failure` |
| `evaluator.py` | thin wrapper | Defines only `compute_all_metrics(ground_truth, estimated) -> Scorer().score(...)`. | Preserves convenience and compatibility for all-default scoring. New configurable selection should use `Scorer`; the wrapper always uses all defaults. | `Scorer` | Tests cover wrapper behavior. No repository caller beyond tests is claimed here. |

Concrete metric classes and `MetricSpec` duplicate name and direction values. Runtime discovery and direction lookup use registry specs, while metric instances carry result metadata in their returned `MetricResult`. The registry is authoritative for lookup and selection. The test `test_registry_specs_match_public_metric_instances` enforces consistency between public instances and specs.

## Architectural Rationale

**Implemented. Repository implementation evidence.** The architecture separates computation, transport, metadata, preparation, and runtime control flow.

| Concern | Component | What it owns | What it avoids |
| --- | --- | --- | --- |
| Abstract metric contract | `Metric` in `base.py` | A two-input `compute` method and default class metadata | Formula code, alignment, registry lookup, and failure policy |
| Result transport | `MetricResult` in `result.py` | `metric_name`, `value`, and `higher_is_better` | Validation and canonical dictionary shaping |
| Numeric distance computation | `distance_metrics.py` | MSE, MAE, normalized MSE, and R2 calculations | Ranking semantics and shared input preparation |
| Ranking and top-k computation | `ranking_metrics.py` | Spearman, Kendall Tau, and Precision@k calculations | Numeric distance semantics and global orchestration |
| Lookup and metadata | `registry.py` | Canonical keys, aliases, specs, executable objects, output order, and direction lookup | Formula execution and input preparation |
| Input preparation | `utils.py` | Array coercion, shape checks, and two-`InteractionValues` union alignment | Metric selection and failure handling |
| Runtime orchestration | `Scorer` in `scorer.py` | Metric selection, parameter dispatch, failure policy, Precision@k raw-object branch, and canonical dict output | Formula implementation |
| Compatibility wrapper | `compute_all_metrics` in `evaluator.py` | All-default scoring through `Scorer().score(...)` | Configurable metric selection |

This split has practical advantages. Adding a metric puts formula code in the distance or ranking module that matches its semantics. The registry gives callers one canonical output order and accepted aliases. `Scorer` can provide configurable selection, alias normalization, and fail-fast behavior without every metric duplicating that control flow. `MetricResult` stays as a small handoff object, so callers receive a plain dictionary rather than metric class instances.

The verified costs are also explicit. Instance and spec direction/name values are duplicated and must stay consistent. Adding a metric requires multiple synchronized changes. Precision@k's original-`InteractionValues` path weakens the pure array abstraction. Aliases and canonical keys can drift. Nested metric-parameter dictionaries aren't statically checked for compatibility with their target metric. Mapping correlation NaN values to `0` loses undefinedness. When both inputs are `InteractionValues`, the alignment uses a sorted union and fills missing keys with zero, which is a benchmark assumption rather than proof that the two explanations are semantically compatible.

```mermaid
flowchart TD
    Caller[Caller] --> Evaluator[evaluator.py<br/>compute_all_metrics]
    Caller --> Scorer[scorer.py<br/>Scorer]
    Evaluator --> Scorer
    Scorer --> Registry[registry.py<br/>METRIC_KEYS, METRIC_ALIASES, METRIC_SPECS]
    Scorer --> Utils[utils.py<br/>prepare_metric_inputs]
    Registry --> Distance[distance_metrics.py<br/>distance metrics]
    Registry --> Ranking[ranking_metrics.py<br/>ranking metrics]
    Distance --> Base[base.py<br/>Metric]
    Distance --> Result[result.py<br/>MetricResult]
    Ranking --> Base
    Ranking --> Result
```

## Metric Class and Runtime Structure

**Implemented. Repository implementation evidence.** The class relationships are intentionally small. `Metric` is an ABC, not a Protocol. It doesn't accept base `**params`; concrete classes may narrow their own compute signatures, and only `PrecisionAtKMetric` exposes `k=10`.

```mermaid
classDiagram
    class Metric {
        <<abstract>>
        +name = "base"
        +higher_is_better = False
        +compute(ground_truth, estimated) MetricResult
    }
    class MetricResult {
        <<dataclass>>
        +metric_name
        +value
        +higher_is_better
    }
    class MetricSpec {
        <<dataclass>>
        +name
        +function
        +higher_is_better
        +category
        +description
    }
    class RegistryModule {
        <<module>>
        +METRIC_KEYS
        +METRIC_ALIASES
        +METRIC_SPECS
        +METRICS
    }
    class Scorer {
        +Scorer(metric_names=None, metric_params=None, fail_fast=False)
        +score(ground_truth, estimated) dict
        +_normalize_metric_names(metric_names) tuple
        +_normalize_metric_params(metric_params) dict
    }
    class MSEMetric
    class MAEMetric
    class NormalizedMSEMetric
    class R2Metric
    class SpearmanMetric
    class KendallTauMetric
    class PrecisionAtKMetric {
        +compute(ground_truth, estimated, k=10) MetricResult
    }

    Metric <|-- MSEMetric
    Metric <|-- MAEMetric
    Metric <|-- NormalizedMSEMetric
    Metric <|-- R2Metric
    Metric <|-- SpearmanMetric
    Metric <|-- KendallTauMetric
    Metric <|-- PrecisionAtKMetric
    MSEMetric ..> MetricResult : creates
    MAEMetric ..> MetricResult : creates
    NormalizedMSEMetric ..> MetricResult : creates
    R2Metric ..> MetricResult : creates
    SpearmanMetric ..> MetricResult : creates
    KendallTauMetric ..> MetricResult : creates
    PrecisionAtKMetric ..> MetricResult : creates
    RegistryModule ..> MetricSpec : defines specs
    RegistryModule ..> MSEMetric : stores executable
    RegistryModule ..> MAEMetric : stores executable
    RegistryModule ..> NormalizedMSEMetric : stores executable
    RegistryModule ..> R2Metric : stores executable
    RegistryModule ..> SpearmanMetric : stores executable
    RegistryModule ..> KendallTauMetric : stores executable
    RegistryModule ..> PrecisionAtKMetric : stores executable
    Scorer ..> RegistryModule : reads keys aliases specs metrics
    Scorer ..> Metric : invokes compute
    Scorer ..> MetricResult : reads value
```

## Scoring Sequence

**Implemented. Repository implementation evidence.** `Scorer.score` returns a dictionary with every canonical key, in canonical order. The normal path prepares shared inputs once, then computes only selected metrics. Unselected metrics become `None`. With `fail_fast=False`, selected metric failures also become `None`. With `fail_fast=True`, the selected metric exception is re-raised.

```mermaid
sequenceDiagram
    participant Caller
    participant Scorer
    participant Utils as prepare_metric_inputs
    participant Registry as registry module
    participant Metric as concrete metric

    Caller->>Scorer: Scorer(metric_names=None, metric_params=None, fail_fast=False)
    Scorer->>Scorer: _normalize_metric_names(metric_names)
    Scorer->>Scorer: _normalize_metric_params(metric_params)
    Caller->>Scorer: score(ground_truth, estimated)
    Scorer->>Utils: prepare_metric_inputs(ground_truth, estimated)
    Utils-->>Scorer: prepared_ground_truth, prepared_estimated
    Scorer->>Scorer: initialize empty results
    loop metric_name in canonical METRIC_KEYS
        alt metric not selected
            Scorer->>Scorer: results[metric_name] = None
        else selected metric
            Scorer->>Registry: read METRIC_SPECS[metric_name] and params
            alt metric_name is precision_at_k and both originals are InteractionValues
                Scorer->>Metric: compute(original ground_truth, original estimated, **params)
            else normal compute path
                Scorer->>Metric: compute(prepared_ground_truth, prepared_estimated, **params)
            end
            alt compute succeeds
                Metric-->>Scorer: MetricResult(metric_name, value, higher_is_better)
                Scorer->>Scorer: results[metric_name] = float(value)
            else compute fails and fail_fast is false
                Scorer->>Scorer: results[metric_name] = None
            else compute fails and fail_fast is true
                Scorer--xCaller: re-raise exception
            end
        end
    end
    Scorer-->>Caller: canonical dict
```

## Array and InteractionValues Alignment

**Implemented. Repository implementation evidence.** `prepare_metric_inputs` coerces array-like values to floating point arrays and requires the ground truth and estimate arrays to have the same shape. This behavior applies after preparation for non-Precision@k metrics.

**Implemented. Repository implementation evidence.** `_prepare_interaction_values` aligns two `InteractionValues` objects over the sorted union of nonempty interaction keys, ordered by `(len(key), key)`. Missing keys are zero-filled. `remove_empty_value_if_needed` returns arrays unchanged; for an `InteractionValues` object with the `()` key, it deep copies the object and sets `interactions[()] = 0`.

**Implemented. Repository implementation evidence.** `Scorer.score` forwards the original `InteractionValues` objects only to `PrecisionAtKMetric`. It sends prepared arrays to the other metrics. This page doesn't claim behavior for mixed array and `InteractionValues` inputs beyond the code path above.

## End-to-End Metric Execution Example

**Implemented. Repository implementation evidence.** This example uses configurable scoring:

```python
scorer = Scorer(
    metric_names=["normalized_mse", "spearman"],
    metric_params={},
    fail_fast=False,
)
results = scorer.score(ground_truth, estimated)
```

The constructor maps the alias `normalized_mse` to canonical `mse_normalized`, keeps `spearman`, and de-dupes selected names while preserving order. During `score`, shared inputs are prepared first. For array-like inputs, both values are converted with `np.asarray(..., dtype=float)` and must have equal shape. The scorer then iterates all seven canonical keys: `mse`, `mae`, `mse_normalized`, `r2`, `spearman`, `kendall_tau`, and `precision_at_k`.

Only the selected specs and objects run. The scorer reads the `MetricSpec` and parameters for `mse_normalized`, invokes `NormalizedMSEMetric.compute`, receives a `MetricResult`, and stores `float(result.value)`. It repeats that path for `spearman` with `SpearmanMetric.compute`. The other canonical keys are present with `None` values because they weren't selected.

An illustrative final dictionary shape is:

```python
{
    "mse": None,
    "mae": None,
    "mse_normalized": "<computed>",
    "r2": None,
    "spearman": "<computed>",
    "kendall_tau": None,
    "precision_at_k": None,
}
```

The strings above stand in for computed floats. Real `Scorer.score` output stores floats or `None`.

## Component-Level API Reference

| Component | Type | Defined in | Purpose | Inputs | Outputs | Called by | Calls | Failure behavior | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Metric` | ABC | `base.py` | Defines the minimal metric contract and default class metadata. | `ground_truth`, `estimated` | `MetricResult` from subclasses | Concrete metric classes | None | Abstract method must be implemented by subclasses. | `test_registry_specs_match_public_metric_instances` |
| `MetricResult` | Mutable dataclass | `result.py` | Transports one metric result. | `metric_name`, `value`, `higher_is_better` | Object with the same fields | Concrete metrics, `Scorer.score` | None | No validation. | `test_distance_metrics_parametrized_edge_values`, `test_ranking_metrics_parametrized_ordering_and_constant_inputs` |
| `MetricSpec` | Frozen dataclass | `registry.py` | Stores registry metadata and executable function for one canonical metric. | `name`, `function`, `higher_is_better`, `category`, `description` | Spec object | `Scorer`, pairwise direction code | None | Dataclass construction errors if required fields are missing. | `test_registry_specs_match_public_metric_instances` |
| `MSEMetric` | Concrete metric | `distance_metrics.py` | Computes mean squared error. | Prepared arrays | `MetricResult` | `registry.py`, direct tests | NumPy subtraction and mean | NumPy errors can propagate to caller or be caught by `Scorer.score`. | `test_distance_metrics_parametrized_edge_values` |
| `MAEMetric` | Concrete metric | `distance_metrics.py` | Computes mean absolute error. | Prepared arrays | `MetricResult` | `registry.py`, direct tests | NumPy subtraction, absolute value, and mean | NumPy errors can propagate to caller or be caught by `Scorer.score`. | `test_distance_metrics_parametrized_edge_values` |
| `NormalizedMSEMetric` | Concrete metric | `distance_metrics.py` | Computes MSE normalized by ground-truth variance, with zero-variance fallback to MSE. | Prepared arrays | `MetricResult` | `registry.py`, direct tests | NumPy variance and mean | NumPy errors can propagate to caller or be caught by `Scorer.score`. | `test_distance_metrics_parametrized_edge_values` |
| `R2Metric` | Concrete metric | `distance_metrics.py` | Computes R2 faithfulness with explicit shape checking and constant-target handling. | Prepared arrays | `MetricResult` | `registry.py`, direct tests | NumPy arrays, means, squared sums, and `np.isclose` | Raises `ValueError` on shape mismatch; returns NaN for constant ground truth. | `test_r2_returns_nan_for_constant_ground_truth`, `test_r2_shape_mismatch_raises_clear_error` |
| `SpearmanMetric` | Concrete metric | `ranking_metrics.py` | Computes Spearman rank correlation and maps NaN correlation to `0`. | Prepared arrays | `MetricResult` | `registry.py`, direct tests | SciPy `spearmanr` | SciPy or input errors can propagate to caller or be caught by `Scorer.score`. | `test_ranking_metrics_parametrized_ordering_and_constant_inputs` |
| `KendallTauMetric` | Concrete metric | `ranking_metrics.py` | Computes Kendall Tau rank correlation and maps NaN correlation to `0`. | Prepared arrays | `MetricResult` | `registry.py`, direct tests | SciPy `kendalltau` | SciPy or input errors can propagate to caller or be caught by `Scorer.score`. | `test_ranking_metrics_parametrized_ordering_and_constant_inputs` |
| `PrecisionAtKMetric` | Concrete metric | `ranking_metrics.py` | Computes absolute top-k overlap for arrays or original `InteractionValues`. | Arrays or original `InteractionValues`, optional `k=10` | `MetricResult` | `registry.py`, `Scorer.score`, direct tests | `_top_k_array_indices`, `_top_k_interaction_keys` | Raises `ValueError` for `k <= 0` and shape mismatch; caps `k` at array size; empty arrays return `0`. | `test_precision_at_k_rejects_non_positive_k`, `test_precision_at_k_caps_k_at_array_size`, `test_precision_at_k_returns_zero_for_empty_arrays`, `test_precision_at_k_ignores_empty_interaction_values_key` |
| `prepare_metric_inputs` | Function | `utils.py` | Prepares shared inputs for scorer-controlled metric execution. | `ground_truth`, `estimated` | Two aligned arrays | `Scorer.score` | `_prepare_interaction_values` only when both inputs are `InteractionValues`; otherwise `np.asarray(..., dtype=float)` | Raises `ValueError` for shape mismatch in the array path. | `test_interaction_values_ignore_empty_key_and_align_union` |
| `_prepare_interaction_values` | Function | `utils.py` | Builds aligned arrays over the sorted union of nonempty interaction keys. | Two `InteractionValues` objects | Two arrays | `prepare_metric_inputs` | `_values_for_interactions` | Missing keys are filled with `0`; empty key is excluded. | `test_interaction_values_ignore_empty_key_and_align_union` |
| `Scorer` | Class | `scorer.py` | Stores normalized metric selection, parameter mapping, and failure policy. | `metric_names=None`, `metric_params=None`, `fail_fast=False` | Scorer instance | Callers and `compute_all_metrics` | `_normalize_metric_names`, `_normalize_metric_params` | Raises `KeyError` for unknown metric names or parameter keys. | `test_scorer_isolates_mocked_metric_failure` |
| `Scorer.score` | Method | `scorer.py` | Prepares inputs, dispatches selected metrics, handles failures, and returns canonical results. | `ground_truth`, `estimated` | Dict with all canonical metric keys and float or `None` values | Callers and `compute_all_metrics` | `prepare_metric_inputs`, registry specs, concrete metric compute methods | With `fail_fast=False`, selected metric exceptions become `None`; with `fail_fast=True`, exceptions are re-raised. | `test_scorer_isolates_mocked_metric_failure`, `test_public_api_exports_required_metrics` |
| `compute_all_metrics` | Function | `evaluator.py` | Convenience wrapper for all default metrics. | `ground_truth`, `estimated` | Result of `Scorer().score(...)` | Tests and any compatibility callers | `Scorer().score(...)` | Same behavior as default `Scorer.score`. | `test_public_api_exports_required_metrics` |

## Adding a Metric

**Repository implementation guidance.** Add a new metric based on what it measures. Use `distance_metrics.py` for numeric distance or faithfulness values. Use `ranking_metrics.py` for ordering or membership values. There is no generic extension module in the current package.

1. Subclass `Metric` in the appropriate module.
2. Set the constructor or class metadata to the metric name and direction used by its `MetricResult`.
3. Implement `compute(self, ground_truth, estimated) -> MetricResult` for the base contract. If the metric needs a narrower extra parameter, follow the current Precision@k pattern and make `Scorer` dispatch that parameter through `metric_params`.
4. Return `MetricResult(metric_name=..., value=..., higher_is_better=...)`. Don't put canonical dictionary logic inside the metric.
5. Import the class in `registry.py`.
6. Add a `MetricSpec` entry with `name`, executable `function`, `higher_is_better`, `category`, and `description`.
7. Manually add the canonical key to `METRIC_KEYS`; it doesn't auto-update from `METRIC_SPECS`.
8. Add an optional alias in `METRIC_ALIASES` if an external name should map to the canonical key.
9. Let `METRICS` derive executable objects from the canonical specs and alias keys.
10. Expand the package public API only if the project intentionally wants the new symbol exported. The existing package exports registry structures and `Scorer`, not concrete classes.
11. If the metric needs raw `InteractionValues` rather than prepared arrays, add an explicit `Scorer.score` special case like the current Precision@k branch.
12. Add tests for distance or ranking behavior, edge cases, `Scorer` dispatch, registry consistency, and public API expectations. Add pairwise direction tests only if pairwise behavior is touched.

Checklist for a new metric:

| Step | Required change | Why |
| --- | --- | --- |
| Choose module | `distance_metrics.py` or `ranking_metrics.py` | Keeps formula semantics grouped with existing metrics. |
| Implement class | Subclass `Metric`, set name/direction, return `MetricResult` | Satisfies the base contract and result transport. |
| Register spec | Import class and add a `MetricSpec` | Makes lookup and metadata available to `Scorer`. |
| Update keys | Add the canonical key to `METRIC_KEYS` manually | Controls output order and default scoring. |
| Add alias if needed | Update `METRIC_ALIASES` | Accepts external names without changing canonical output. |
| Handle parameters | Pass values through `metric_params` and update dispatch only when needed | Keeps formulas out of `Scorer` while allowing parameterized metrics. |
| Handle raw objects if needed | Add a targeted `Scorer.score` branch | Prepared arrays are the default path; raw `InteractionValues` require an explicit exception. |
| Test behavior | Cover the metric family, edge cases, `Scorer`, registry consistency, and package API | Prevents drift across formulas, metadata, aliases, and canonical outputs. |

## Metrics Architecture Limitations

**Implemented. Repository implementation evidence.** The current metrics architecture has known verified limits:

* Alignment for two `InteractionValues` inputs uses a sorted union and zero fill. It doesn't establish semantic compatibility between explanations.
* Mixed array and `InteractionValues` inputs aren't special-cased beyond the current `prepare_metric_inputs` behavior.
* Metric instance name/direction and registry spec name/direction are duplicated.
* Nested metric parameters aren't statically checked against the target metric signature.
* Precision@k has a special raw-`InteractionValues` path in `Scorer.score`, so not every metric receives only prepared arrays.
* Undefined Spearman or Kendall correlations are returned as `0`, which loses the distinction between undefined and zero correlation.
* Adding, removing, or renaming a metric requires synchronized registry changes across keys, specs, optional aliases, and tests.

## Canonical Metrics

### Mean Squared Error, `mse`

**Implemented. Repository implementation evidence.** `MSEMetric` computes mean squared error.

Formula:

```text
mse = mean((ground_truth - estimated)^2)
```

Intuition: MSE measures average squared deviation from the reference values. Lower is better, which is covered by `test_mse_lower_score_wins`.

Strengths: MSE is sensitive to large errors and is useful when large deviations should count more than small ones.

Weaknesses: Squaring makes the value scale-dependent and outlier-sensitive. A single large miss can dominate the score.

Edge cases: Exact agreement returns `0`. Inputs must align as arrays with the same shape after preparation, or as aligned `InteractionValues` arrays when both inputs are `InteractionValues`.

### Mean Absolute Error, `mae`

**Implemented. Repository implementation evidence.** `MAEMetric` computes mean absolute error.

Formula:

```text
mae = mean(abs(ground_truth - estimated))
```

Intuition: MAE measures the average absolute deviation from the reference values. Lower is better.

Strengths: MAE has the same units as the values being compared and weights errors linearly.

Weaknesses: MAE is still scale-dependent. It does not emphasize large errors as strongly as MSE.

Edge cases: Exact agreement returns `0`. Shape and alignment behavior follows `prepare_metric_inputs` and `_prepare_interaction_values`.

### Normalized Mean Squared Error, `mse_normalized`

**Implemented. Repository implementation evidence.** `NormalizedMSEMetric` computes MSE divided by the reference variance. The accepted input alias `normalized_mse` maps to the canonical key `mse_normalized`.

Formula:

```text
mse_normalized = mean((ground_truth - estimated)^2) / variance(ground_truth)
```

Intuition: normalized MSE compares squared error with the spread of the reference values. Lower is better.

Strengths: It reduces raw scale effects when reference variance is meaningful.

Weaknesses: It can be unstable when reference variance is very small. It also inherits MSE sensitivity to large deviations.

Edge cases: If the reference variance is zero, the implementation falls back to unnormalized MSE because no reference variance exists for normalization. This edge behavior is covered by distance metric tests such as `test_distance_metrics_parametrized_edge_values`.

### R2 Faithfulness, `r2`

**Implemented. Repository implementation evidence.** `R2Metric` computes a reconstruction quality score. It is a faithfulness or reconstruction metric, not a pure distance metric.

Formula:

```text
r2 = 1 - sum((ground_truth - estimated)^2) / sum((ground_truth - mean(ground_truth))^2)
```

Intuition: `1` means exact reconstruction. `0` matches the mean-reference baseline. Values below `0` are worse than that mean baseline. Higher is better.

Strengths: R2 gives a baseline-relative view of reconstruction quality, so it can show whether an estimate explains reference variation rather than only reporting absolute error.

Weaknesses: It depends on the variance of the supplied reference values. It can be negative, which is valid but can surprise readers who expect a bounded score.

Edge cases: A constant or near-zero denominator returns `NaN`, covered by `test_r2_returns_nan_for_constant_ground_truth`.

**Literature evidence and repository deviation.** ProxySPEX reports an R2-style faithfulness objective over all coalitions in Section 3.1, Eq. (2) [ProxySPEX]. The repository uses the same numerator and denominator algebra, but applies it to the supplied aligned arrays from `prepare_metric_inputs` or `_prepare_interaction_values`, not necessarily to every coalition. That is a domain-sampling deviation from the ProxySPEX equation, not a change in the algebra.

### Spearman Rank Correlation, `spearman`

**Implemented. Repository implementation evidence.** `SpearmanMetric` computes Spearman rank correlation through SciPy behavior and maps SciPy `NaN` to `0`. Higher is better, covered by `test_spearman_higher_score_wins`.

Formula:

```text
spearman = pearson_correlation(rank(ground_truth), rank(estimated))
```

Intuition: Spearman measures whether higher reference values tend to receive higher estimated ranks.

Strengths: It is insensitive to monotonic rescaling. It can be useful when ordering matters more than raw magnitude.

Weaknesses: It discards magnitude information. Ties can affect the computed correlation, and constant input can trigger SciPy `NaN` behavior.

Edge cases: When SciPy returns `NaN`, the implementation returns `0`.

### Kendall Tau Rank Correlation, `kendall_tau`

**Implemented. Repository implementation evidence.** `KendallTauMetric` computes Kendall Tau through SciPy behavior and maps SciPy `NaN` to `0`. Higher is better.

Formula:

```text
kendall_tau = (concordant_pairs - discordant_pairs) / pair_normalization
```

Intuition: Kendall Tau measures agreement in pairwise ordering between reference and estimated values.

Strengths: It directly reflects pairwise order consistency, which can be easier to interpret when ranking interactions.

Weaknesses: It does not measure magnitude error. Ties and small samples can limit resolution.

Edge cases: When SciPy returns `NaN`, the implementation returns `0`.

### Precision@k, `precision_at_k`

**Implemented. Repository implementation evidence.** `PrecisionAtKMetric` compares the overlap between the top-k reference and estimated interactions by absolute magnitude. `test_precision_at_k_uses_absolute_top_k_overlap` covers the magnitude-based behavior.

Formula:

```text
precision_at_k = count(top_k_abs(ground_truth) intersect top_k_abs(estimated)) / denominator
```

Intuition: Precision@k asks whether the estimate finds the same strongest interactions as the reference, ignoring sign and focusing on absolute magnitude.

Strengths: It is easy to interpret when the benchmark cares about recovering a short list of important interactions.

Weaknesses: It ignores the actual values once membership in the top-k set is decided. It is sensitive to ties around the cutoff.

Edge cases: The metric rejects `k <= 0`. For arrays, the denominator is capped by the array size and returns `0` for empty arrays. For `InteractionValues`, it excludes the empty key, builds top-k sets from nonempty interaction keys, and uses the size of the reference top-k nonempty-key set as the denominator. That denominator is capped by the available nonempty keys, and the empty nonempty-key case returns `0`.

## Metric Comparison Table

| Metric | Canonical key | Better direction | Main signal | Strength | Weakness | Edge cases |
| --- | --- | --- | --- | --- | --- | --- |
| Mean squared error | `mse` | Lower | Average squared value error | Highlights large errors | Scale-dependent and outlier-sensitive | Exact match is `0`; aligned arrays must match shape |
| Mean absolute error | `mae` | Lower | Average absolute value error | Linear and unit-preserving | Does not emphasize large errors like MSE | Exact match is `0`; same alignment rules as other array metrics |
| Normalized MSE | `mse_normalized` | Lower | Squared error relative to reference variance | Easier comparison across value scales | Unstable when reference variance is tiny | Zero reference variance falls back to MSE |
| R2 | `r2` | Higher | Baseline-relative reconstruction quality | Shows improvement over mean baseline | Not a pure distance metric; can be negative | Constant or near-zero denominator returns `NaN` |
| Spearman | `spearman` | Higher | Monotonic rank agreement | Ignores monotonic scaling | Drops magnitude information | SciPy `NaN` becomes `0`; ties matter |
| Kendall Tau | `kendall_tau` | Higher | Pairwise order agreement | Direct pairwise ranking interpretation | Drops magnitude information | SciPy `NaN` becomes `0`; ties and small samples matter |
| Precision@k | `precision_at_k` | Higher | Top-k absolute-magnitude overlap | Focuses on strongest interactions | Ignores value accuracy outside membership | Rejects `k <= 0`; array empty case returns `0` |

## Metric, Scorer, and Aggregator Roles

**Implemented. Repository implementation evidence.** These roles are distinct:

* `Metric` computes one metric value from one aligned reference and estimate pair.
* `Scorer.score` prepares inputs, invokes registered metrics, and writes per-run metric values under canonical keys.
* Aggregator consumes existing metric values from successful run records and averages them across records or seeds. It does not recompute metrics.


## References
* [ProxySPEX] Landon Butler, Abhineet Agarwal, Justin Kang, Yigit Efe Erginbas, Bin Yu, Kannan Ramchandran. “ProxySPEX: Inference-Efficient Interpretability via Sparse Feature Interactions in LLMs.” NeurIPS 2025, Section 3.1, Eq. (2), official supplied URL.
