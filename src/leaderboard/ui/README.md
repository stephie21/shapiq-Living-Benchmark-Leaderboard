# shapiq Approximator Leaderboard — UI Documentation

A Gradio-based web interface for comparing Shapley value approximators across games, budgets, and interaction indices.

---

## Overview

The leaderboard evaluates approximators on benchmark games using two complementary statistical methods:

- **ELO ratings** — pairwise win/loss comparisons between approximators, stabilized via bootstrap resampling and confidence intervals
- **Critical Difference (CD) analysis** — Demšar (2006) rank-based test that identifies which performance differences are statistically significant

Data is loaded from a MongoDB backend (or a local JSONL file) and aggregated into per-(approximator, game, budget) statistics before the UI starts.

---

## Tabs

### ELO Leaderboard

The main ranking view. Approximators are compared pairwise within each *budget bucket* and scored using the ELO system.

**Filters:** (apply before or after navigating buckets):

- **Metric** — restrict scoring to one metric (e.g. MSE or Spearman); default: all metrics combined
- **Index** — interaction index (e.g. `SV`); default: SV if present, otherwise first available index
- **Game** — restrict to one benchmark game; default: all games
- **Bootstrap Samples** — number of bootstrap samples for CI estimation (0 = disabled)
- **Permutations** — number of ELO permutations per bootstrap sample
- **Approximators** — checkbox group to include/exclude individual approximators;  
*Deselect all* / *Reset* buttons for convenience

**Controls:**

- **🔍 Open in Detailed Data Tab** — transfers the current approximator/budget/metric/index/game selection to the Detailed Data tab
- **Apply & Recompute** — re-runs ELO scoring with the current filter and approximator selection

**Budget buckets** (navigable via ◀ / ▶ buttons):

| Label | Budget (coalition evaluations) |
|---|---|
| Low | 250 |
| Low-Medium | 500 |
| Medium *(default)* | 1 000 |
| Medium-High | 5 000 |
| High | 10 000 |

**Outputs:**

- Ranked table with ELO score, match count, wins, losses, and ties
- Bar chart of ELO scores with 95 % bootstrap confidence intervals (shown when all games are selected; hidden for single-game view)
- CD diagram (switchable via the sub-tab) showing which pairs of approximators are
*not* significantly different (connected by a bar); uses the same metric and index
filters as the ELO computation
- Info line summarizing the active configuration and any relevant warnings

**Side-by-side overview:**  
(below the navigation panel): all five budget buckets rendered simultaneously for a quick cross-budget comparison.

> ⚠️ ELO and CD rankings may diverge when aggregating over multiple indices or games — this is flagged in the info line.

> ⚠️ Confidence intervals are not meaningful when only one comparable group exists (e.g. a single game is selected) — this is flagged in the info line.

---

### Metrics across Budgets

Line plots of aggregated metric values over the full budget range, one sub-tab per available metric (e.g. MSE, Spearman).

Each plot shows mean ± 1 std (shaded band) on a **log scale** for the selected game. Every approximator gets a consistent colour and line style across all views.

**Filters:**

- **Game** dropdown — select the benchmark game to display
- **Approximators** checkbox group — toggle individual approximators;  
*Deselect all* / *Reset* buttons for convenience

**Controls:**

- **🔍 Open in Detailed Data Tab** — jump to the raw data view pre-filtered to the current game and approximator selection

---

### Compare Approximators

Side-by-side comparison of up to 5 approximators, each shown in a separate column with an independent game selection.

Use **+ Add Approximator** / **- Remove Approximator** to control the number of active columns. All columns share the same y-axis scale per metric, making visual comparison straightforward.

**Controls:**

- **🔍 Open in Detailed Data Tab** — jump to the raw data view pre-filtered to the current game and approximator selection

---

### Detailed Data

Raw record browser with full filter control. Useful for inspecting individual runs, verifying seeds, or exporting specific slices of data.

**Filters:**

| Filter | Description |
|---|---|
| Game | Benchmark game name |
| Approximator | Approximator name |
| Budget | Number of coalition evaluations |
| Index | Interaction index (e.g. `SV`) |
| Max Order | Maximum interaction order |
| N Players | Number of players in the game |
| Ground Truth Method | Method used to compute ground truth values |
| Approx Seed | Random seed of the approximator run |
| Metrics | Restrict which metric columns are shown |

All filters are multi-select; leaving a filter empty means *no restriction*. Click **Search** to apply, **Reset filters** to clear all selections.

The result count is shown above the table (e.g. `128 runs found`).

---

### 📖 Help

Displays this documentation.

---

## Methodology

For details on the ELO and Critical Difference scoring methods, see the
[Scoring README](../scoring/README.md).
