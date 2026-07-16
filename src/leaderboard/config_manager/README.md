# Config Manager Module

The `config_manager` serves as the primary **defensive firewall** for the shapiq Leaderboard runner. It is responsible
for loading, parsing, and rigorously validating user configurations from YAML files.

By leveraging **Pydantic** for strict type modeling and employing a custom UI-friendly exception handler, this module
ensures a "Fail Fast" approach. It shields the deep execution pipelines from runtime crashes and replaces messy Pydantic
tracebacks with clean, actionable terminal UI boundaries (💥).

## 🏗️ Architecture & Data Flow

```text
  [YAML Template]  
         |
         v
  +--------------+       (Validation Layer - models.py)
  |  loader.py   | -----> 1. Type Casting & Schema Validation
  +--------------+        2. Silent Purge (Cross-family param isolation)
         |                3. Anti-Freeze Guard (Dimension limits)
  (If Invalid)            4. Algorithmic Cross-Validation
         |                        |
         v                        | (If Valid)
  +-----------------------+       v
  | config_exceptions.py  |   [MVPRunConfig] --> Passed to Game Factory
  | (Terminal UI Output)  |
  +-----------------------+

```

## 📁 Directory Structure & Responsibilities

| File                          | Core Responsibility                                                                                                                                                                                |
|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `__init__.py`                 | Public API surface. Exposes models (`MVPRunConfig`) and exceptions.                                                                                                                                |
| `models.py`                   | **Business Logic Layer**. Contains the Pydantic models. Executes cross-field dependency checks, parameter purging, and bounds interception.                                                        |
| `constants.py`                | **Single Source of Truth**. Stores all registries (Global/Local), hardcoded feature counts (`GAME_PLAYER_COUNTS`), and algorithmic whitelists.                                                     |
| `config_exceptions.py`        | **UI & Error Handling**. Defines granular error classes (e.g., `BudgetRangeError`). Contains the `format_config_error` template that renders the distinct red boundary boxes (💥) in the terminal. |
| `loader.py`                   | **Entry Point**. Reads YAML files and intercepts raw Pydantic `ValidationError` to strip traceback noise before rendering the UI exceptions.                                                       |
| `check_game_player_counts.py` | **Dev Tool**. Dynamically loads tabular datasets from `shapiq_games` to verify their actual $n$ dimensions against `constants.py`.                                                                 |

---

## 🧠 Core Validation Mechanisms

The module implements advanced defensive programming paradigms inside `models.py`:

### 1. Parameter Silent Purge

To provide a frictionless "universal template" experience, `validate_game_params` dynamically cleans the input
dictionary:

* If `game_family == "global_xai"`, the system quietly removes local-only parameters (`imputer`, `x`,
  `class_to_explain`).
* If the task is inside `REGRESSION_GAMES`, `class_to_explain` is purged.
* **Why?** Users don't need to manually delete unused lines in their YAML when switching modes. The Runner always
  receives a perfectly sanitized dictionary.

### 2. Anti-Freeze Guards

Benchmark evaluation can trigger combinatorial explosions. The config manager acts as a circuit breaker:

* **Dimension Guard**: Blocks `ExactComputer` for games where $n > 14$ to prevent memory/CPU exhaustion (
  evaluating $2^{15}$ permutations takes too long).
* **Upstream Bug Mitigation**: Intercepts `TreeExplainer` requests for `STII`, `FSII`, and `FBII` indices, as
  `shapiq v0.x` contains known matrix broadcasting bugs for these combinations.

### 3. Intelligent Cross-Validation

* **Loss Function Integrity**: Dynamically assesses if a dataset belongs to `REGRESSION_GAMES`. If a user assigns a
  classification loss (e.g., `accuracy_score`) to a regression task, it halts execution instantly.
* **Visual Dimension Alignment**: Enforces structural mapping (e.g., `"vit_9_patches"` strictly requires `n_players=9`).

## 💡 Developer Guidelines

* **Adding New Errors**: To add new constraints, always raise your exceptions wrapped in the `format_config_error`
  template from `config_exceptions.py` to maintain terminal UI consistency.
* **Modifying Supported Lists**: 90% of structural updates (adding datasets, algorithms, or imputers) only require
  modifying the sets and dicts inside `constants.py`. The Pydantic validators will dynamically adapt to the new
  whitelists.

## 🛠️ Extending the Benchmark Ecosystem

The benchmark architecture is highly decoupled. If you need to test new datasets or algorithms beyond the standard
templates, you do not need to modify the complex validation logic in the configuration models. You only need to update
the central registries.

### Registering a New Game (Dataset)

To introduce a new dataset to the leaderboard ecosystem:

1. **Ensure DataLoader Exists**: Verify that your data processing function is fully implemented and exposed in the
   `shapiq_games.datasets` module.
2. **Update the Single Source of Truth**: Open `src/leaderboard/config_manager/constants.py`.
3. **Bind to Registry**: Add the game class to the `LOCAL_GAME_REGISTRY` or `GLOBAL_GAME_REGISTRY` dictionary.
4. **Define Dimensionality (CRITICAL)**: You MUST hardcode the exact feature dimension size (e.g., `"MyNewDataset": 45`)
   inside the `GAME_PLAYER_COUNTS` dictionary. The system relies on this value to perform budget boundary validations
   and Out-Of-Memory guards.
5. **Task Classification**: If your new dataset is a Regression task (predicting continuous values rather than classes),
   you MUST append its string name to the `REGRESSION_GAMES` set to activate the loss-function cross-validation locks.

## 🛠️ Extending the Benchmark Ecosystem

The benchmark architecture is built on two distinct layers: the underlying game definitions (`shapiq_games`) and the
leaderboard configuration layer (`config_manager`).

To add a completely new dataset or a new approximator, you must follow the complete end-to-end integration pipeline
below.

### 📚 Part 1: Adding a New Game (Dataset)

Adding a new tabular game (e.g.`TaiwaneseBankruptcy`) requires a 3-phase process: writing the data loader, creating the
benchmark wrapper, and finally registering it in the configuration manager.

#### Phase 1: Implement the Dataset Loader (`src/shapiq_games/datasets`)

1. **Add Raw Data**: Place your raw dataset file (e.g., `taiwanese_bankruptcy.csv`) into the data directory:
   `src/shapiq_games/datasets/data/`.
2. **Create Loader Function**: Open `src/shapiq_games/datasets/_all.py` and write the data extraction and imputation
   logic.

```python
def load_taiwanese_bankruptcy() -> tuple[pd.DataFrame, pd.Series]:
    """Load the Taiwanese Bankruptcy dataset from local CSV file."""
    data = _try_load("taiwanese_bankruptcy.csv")
    target_col = "Bankrupt" if "Bankrupt" in data.columns else data.columns[-1]

    X = data.drop(columns=[target_col])
    y = data[target_col]

    X = X.apply(pd.to_numeric, errors="coerce")
    X = _impute(X)
    X = _encode_categorical(X)
    y = pd.Series(LabelEncoder().fit_transform(y.astype(str)), name="target")
    return X, y

```

3. **Expose the Loader**: Open `src/shapiq_games/datasets/__init__.py`.

* Add `load_taiwanese_bankruptcy` to the `from ._all import (...)` block.
* Add `"load_taiwanese_bankruptcy"` to the `__all__` list.

#### Phase 2: Integrate into the Benchmark Engine (`src/shapiq_games/benchmark`)

4. **Update Setup Logic**: Open `src/shapiq_games/benchmark/setup.py`.

* Import your new loader at the top of the file.
* Append `"taiwanese_bankruptcy"` to the `AVAILABLE_DATASETS` list.
* Inside the `__init__` method, add the routing logic:

```python
elif dataset_name == "taiwanese_bankruptcy":
x_data, y_data = load_taiwanese_bankruptcy()
self.feature_names: list = list(x_data.columns)
self.dataset_type = "classification"

```

* *Remember to update the fallback `else:` error message string to include your new dataset name so users see it in the
  terminal.*


5. **Create the Game Class**: Open `src/shapiq_games/benchmark/local_xai/benchmark_tabular.py` and create the
   configuration wrapper:

```python
class TaiwaneseBankruptcy(LocalExplanation):
    """The TaiwaneseBankruptcy dataset as a LocalExplanation game."""

    def __init__(
            self, *, class_to_explain: int | None = None, x: np.ndarray | int | None = None,
            model_name: str = "decision_tree", imputer: str = "marginal", normalize: bool = True,
            verbose: bool = False, random_state: int | None = 42,
    ) -> None:
        _init_classification_game(
            self, dataset_name="taiwanese_bankruptcy", class_to_explain=class_to_explain,
            x=x, model_name=model_name, imputer=imputer, normalize=normalize,
            verbose=verbose, random_state=random_state,
        )

```

6. **Expose the Game Class**: Open `src/shapiq_games/benchmark/local_xai/__init__.py`.

* Import `TaiwaneseBankruptcy` from `.benchmark_tabular`.
* Append `"TaiwaneseBankruptcy"` to the `__all__` list.

#### Phase 3: Register in the Config Manager (`src/leaderboard/config_manager`)

Now that the game exists in the underlying library, you must whitelist it for the Runner's YAML parser.

7. **Bind to Registry**: Open `src/leaderboard/config_manager/constants.py`. Import the game and map it inside the
   `LOCAL_GAME_REGISTRY` (and `GLOBAL_GAME_REGISTRY` if applicable).
8. **Define Dimensionality (CRITICAL)**: You MUST hardcode the exact feature dimension size inside the
   `GAME_PLAYER_COUNTS` dictionary:

```python
GAME_PLAYER_COUNTS = {
    # ... other games
    "TaiwaneseBankruptcy": 94,
}

```

*Note: The Pydantic validators rely strictly on this integer to perform budget boundary checks ($n+1 \le B < 2^n$) and
Out-Of-Memory (OOM) guards.*

9. **Task Classification**: If your new dataset is a Regression task, you MUST append its string name to the
   `REGRESSION_GAMES` set to activate the loss-function cross-validation locks.

---

### 🧮 Part 2: Adding a New Approximator (Algorithm)

To add a new sampling or proxy algorithm to the benchmark comparison:

1. **Verify Upstream Integration**: Ensure that your custom algorithm class is properly implemented, inherits from
   `shapiq.approximator.Approximator`, and is registered in the appropriate index capability lists inside the core
   `shapiq` package (e.g., `SV_APPROXIMATORS` or `SII_APPROXIMATORS`).
2. **Update the Whitelist**: Open `src/leaderboard/config_manager/constants.py`.
3. **Append Name**: Add the precise, case-sensitive class name of your algorithm to the `ALL_SUPPORTED_APPROXIMATORS`
   list.

Once registered in the `constants.py` file, the Pydantic validator will immediately recognize it as a legitimate input,
allowing you to invoke it directly via the `approximators` list in your `default_run.yaml` files.
