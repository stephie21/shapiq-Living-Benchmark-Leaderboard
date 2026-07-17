## Scoring README

### Purpose of the scorer

The purpose of a leaderboard scorer is to compute a ranking of approximators based on their performance on a selected benchmark context. The project defines an abstract `LeaderboardScorer` interface and allows different concrete scoring implementations. The primary implementation currently used is the `EloScorer`, which is based on the Elo rating system. This implementation will be covered in more detail.

The input to a scorer are run records from the database. They contain benchmark results of the approximators across games, indices, budgets, seeds and metrics. After the scorer processes these records, it returns a `ScoringResult`.

The `ScoringResult` describes which scorer was used, which benchmark context was evaluated, and how the approximators were ranked. Its main output is a list of leaderboard rows, where each approximator is assigned a score and ranked accordingly. In addition, the result contains metadata that documents how the score was computed.

### The Elo rating system

The Elo rating system is a rating method for players in repeated pairwise contests, which was originally designed for chess.

Each competitor has a numerical rating. Before a match, the rating difference is used to estimate the expected result. A competitor with a higher rating is expected to win more often than a competitor with a lower rating.

After the match, both ratings are updated. If the result matches the expectation, the rating change is small. If the result is surprising, for example if a lower-rated competitor beats a higher-rated competitor, the rating change is larger.

The size of the rating update is controlled by the so-called `k_factor`. A high `k_factor` makes ratings react quickly to new results. A low `k_factor` makes ratings more stable.

The Elo system should be understood as a relative rating system that takes the strength of each opponent into account. However, the margin of victory in a match does not affect the rating update.

### How the EloScorer works

The `EloScorer` is the primary scoring implementation used in the leaderboard. It compares approximators through pairwise matches within benchmark groups. A comparable group consists of run records that share the same benchmark context, such as game, index, maximum interaction order, budget, and ground truth method. Comparable groups are formed during scoring based on the configured group keys.

Within each comparable group, the scorer first aggregates repeated runs over approximation seeds and then constructs pairwise matches for the selected metrics. All approximators start with the same initial Elo rating (Default: 1000). Each pairwise match updates the ratings of the two involved approximators. The update depends on the match outcome and on the expected win probability, which is derived from the current rating difference between both approximators. A win against a stronger opponent leads to a larger Elo gain, while a win against a weaker opponent leads to a smaller gain. On the other hand, losing against a weaker opponent is penalized more strongly than losing against a stronger opponent.

Since Elo ratings are updated sequentially, the order of pairwise matches can influence the final outcome. This is a known disadvantage of the Elo system. To obtain more stable rankings, the scorer can compute Elo ratings multiple times using different permutations of the match order. The final score is then based on the mean rating across these permutations.

In addition, the scorer supports bootstrapping over comparable groups, inspired by the TabArena(https://github.com/autogluon/tabarena/tree/main) Elo rating system approach. For each bootstrap sample the comparable groups are sampled with replacement and the ratings recomputed. If match-order permutations are enabled, the scorer averages the permutation-based Elo ratings within each sample. The bootstrap score distribution is used to compute confidence intervals. These intervals show how stable the approximator rankings are under resampling of the available comparable groups.

The default configuration uses an initial Elo rating of 1 000, a K-factor of 16, and a tie tolerance of 0 (exact ties only). Bootstrap resampling defaults to 200 samples with 10 match-order permutations each, yielding 95 % confidence intervals.

### How to use the EloScorer

Construct the EloScorer by giving the benchmark context over which the approximators should be compared. The context can be restricted by metrics, games, indices, and budgets. If one of these filter arguments is set to `None`, the scorer uses all available values for that argument.
In addition you can decide on the number of order permutations to be calculated and the number of bootstrap samples to be taken. By default permutations and bootstrapping are disabled.
After completing the construction, call the `score` method with the run records as parameter to obtain the `ScoringResult`. It contains the ranked leaderboard rows, the evaluated context, and metadata about the scoring process.

**Usage example:**

```jsx
scorer = EloScorer(
    metric_names=["spearman"],
    game_names=None,
    indices=["SII"],
    budgets=[250, 500, 1000],
    n_permutations=50,
    n_bootstrap_samples=200,
    confidence_level=0.95,
)

result = scorer.score(raw_records)
```

### Critical Difference analysis

The `CriticalDifferenceScorer` ranks approximators per comparable group (same game, index, max order,
budget, and ground-truth method) and metric. Friedman's test checks
whether any ranking differences are globally significant. If significant, Nemenyi's
post-hoc test identifies which pairs differ — those that do *not* differ significantly
are connected by a bar in the CD diagram.

By default, seeds are aggregated within each comparable group before ranking, consistent
with the EloScorer. In the leaderboard UI, `approx_seed` is added as an additional group
key so that each seed is treated as an individual observation — this is why CD and ELO
rankings may diverge.

Reference: Demšar, J. (2006). Statistical comparisons of classifiers over multiple data
sets. *Journal of Machine Learning Research*, 7, 1–30.

### Addition of a new scorer

New scorers can be defined in the `leaderboard/scoring` package. A new scorer must fulfill the following requirements:

1. It must extend the abstract `LeaderboardScorer` class.
2. It must define a unique scorer name.
3. It must define whether higher final scores are considered better or worse.
4. It must implement the `score` method and return a `ScoringResult`.

The `score` method receives the run records as input and is responsible for computing the final leaderboard. The returned `ScoringResult` should contain the ranked leaderboard rows, the scoring context, and metadata describing the scoring process.

The main output of a scorer is a list of rows in the leaderboard (`LeaderboardRow`). The main data you need to construct these rows is a mapping from approximator names to their computed scores.
If the scorer computes intermediate results for comparable groups, these can be stored as group results (`group_results`) and optionally be provided in the output.
The `metadata` attribute can be used to store additional information about the scoring process. You can also use this information for debugging or visualization in the UI.

### Package structure

The scoring package is organized around a small set of core abstractions, concrete scorer implementations, shared utilities, and manual check scripts.

| File | Classification | Description |
|---|---|---|
| `__init__.py` | Package entry point | Exposes the most important public scoring interfaces, currently `LeaderboardScorer` and `ScoringResult`. |
| `base.py` | Core abstraction | Defines the abstract `LeaderboardScorer` base class. Every scorer must implement the `score(records)` method and return a `ScoringResult`. |
| `result.py` | Result data structures | Contains the dataclasses used to represent scoring output, including `LeaderboardRow`, group-level results, `ScoringContext`, and the final `ScoringResult`. |
| `scorer_utils.py` | Shared scorer utilities | Provides common helper functions for filtering valid records, grouping comparable benchmark records, extracting metric values, aggregating seeds, and building scoring contexts. |
| `elo_scorer.py` | Main scorer implementation | Implements the Elo-based leaderboard scorer. It builds pairwise matches between approximators, applies Elo updates, supports match-order permutations, and can compute bootstrap confidence intervals. |
| `cd_scorer.py` | Statistical comparison scorer | Implements Critical Difference analysis based on group-wise ranks, Friedman testing, and Nemenyi-style critical differences. It can also produce CD diagram visualizations. |
| `group_rank_scorer.py` | Simple baseline scorer | Implements a simpler group-wise ranking scorer. It ranks approximators inside comparable groups and aggregates these ranks into an average-rank leaderboard. |
| `display.py` | Terminal output helper | Formats a `ScoringResult` as a readable terminal table and provides a small print helper for manual inspection. |
| `check_elo_scorer.py` | Manual check script | Creates sample records and runs the `EloScorer` in several configurations for manual validation. |
| `check_cd_scorer.py` | Manual check script | Runs the Critical Difference scorer on historical records and saves a CD diagram for inspection. |
| `check_group_rank_scorer.py` | Manual check script | Runs the group-rank scorer on sample records and prints the resulting leaderboard. |
