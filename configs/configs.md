# shapiq Benchmark Configurations

This directory contains all configuration files required to run the `shapiq` benchmark experiments. The configuration
system relies on strict Pydantic typing and an intelligent "Silent Purge" mechanism to ensure runtime safety, parameter
consistency, and automatic cross-validation of experimental setups.

---

## 📊 Benchmark Run Plan & Progress Status

Below is the active execution tracker detailing the configurations, feature dimensions (`n`), target indices, and
specific computational budgets assigned for our ongoing benchmark evaluations.

| Game Name               | Players (`n`) | Game Family    | Target Index                                               | Evaluation Budgets          | Random Seeds |
|:------------------------|:-------------:|:---------------|:-----------------------------------------------------------|:----------------------------|:-------------|
| **CaliforniaHousing**   |       8       | Local XAI      | `SII` (3), `k-SII` (3), `STII` (3), `FBII` (4), `FSII` (4) | 250                         | 10           |
| **BikeSharing**         |      12       | Local XAI      | `SV`, `k-SII`, `SII`, `STII`, `FBII`, `FSII`               | 250, 500, 1000              | 30           |
| **AdultCensus**         |      14       | **Global XAI** | `SV`, `k-SII`, `SII`, `STII`                               | 250, 500, 1000, 5000, 10000 | 10           |
| **Mushroom**            |      22       | Local XAI      | `SV`, `SII`, `k-SII`                                       | 250, 500, 1000, 5000, 10000 | 6            |
| **Soybean**             |      35       | Local XAI      | `SV`, `SII`, `k-SII`                                       | 250, 500, 1000, 5000, 10000 | 8            |
| **Splice**              |      60       | Local XAI      | `SV`, `SII`, `k-SII`                                       | 250, 500, 1000, 5000, 10000 | 10           |
| **TaiwaneseBankruptcy** |      94       | Local XAI      | `SV`, `SII`, `k-SII`                                       | 250, 500, 1000, 5000, 10000 | 10           |
| **Arrhythmia**          |      279      | Local XAI      | `SV`                                                       | 1000, 5000, 10000           | 5*           |
| **Arrhythmia**          |      279      | Local XAI      | `SII` (fallback `k-SII`)                                   | 500, 1000, 5000             | 10**         |
| **ImageClassifier**     |       9       | Local XAI      | `SV`                                                       | 250, 500                    | 3            |
| **ImageClassifier**     |       9       | Local XAI      | `k-SII` (fallback `SII`, `STII`)                           | 100, 200, 400               | 4***         |

### ⚠️ Special Execution Notes & Hardware Stress Tests

1. **Arrhythmia Extreme Dimensionality (`n=279`)**:
    * Due to the massive feature space, this dataset requires execution on a secondary high-performance workstation.
    * *\*Note on `SV`*: The `kADDSHAP` approximator has only completed 10 runs strictly at a budget of 1000.
    * *\*\*Note on `SII`*: The `KernelSHAPIQ` and `InconsistentKernelSHAPIQ` approximators have only completed 1 run at
      a budget of 1000 due to severe computational overhead.
2. **ImageClassifier (Computer Vision via Deep Learning)**:
    * This black-box task evaluates image patches/superpixels and is completed strictly via `ExactComputer`. Expect
      significant CPU/RAM spikes during initialization as Hugging Face ViT/ResNet weights are downloaded and heavy
      matrix multiplications are executed.
    * *\*\*\*Scale Updates*: A new pipeline execution featuring budgets of 250 and 500 across `n=14` players is
      currently scheduled.
    * *Optimization Strategy*: For `n=9` players (resulting in exactly 512 total coalitions), utilizing just 2 discrete
      budgets (250, 500) combined with 3 random seeds is mathematically optimal. A budget of 500 guarantees near-perfect
      algorithmic convergence for this dimension. Furthermore, restricting the evaluated indices strictly to `SV` and
      `k-SII` successfully bypasses redundant high-order evaluations, heavily mitigating thermal throttling while still
      capturing both primary main effects and critical interaction effects.

---

## 🚀 Quick Start Execution Workflow

Starting a new benchmark run requires zero hard-coding. Follow this standard workflow:

### Step 1: Select a Base Template

The repository provides ready-to-use templates tailored to specific data modalities:

* `template_tabular.yaml`: Used for tabular machine learning datasets (e.g., `AdultCensus`, `BikeSharing`) and synthetic
  unanimity mathematical games (`SOUM`).
* `template_visual.yaml`: Exclusively formatted for computer vision and deep learning tasks (e.g., `ImageClassifier` via
  ViT or ResNet).

### Step 2: Clone the Configuration

Clone your chosen template to create your active run file. The runner defaults to looking for `default_run.yaml`.

```bash
cp configs/template_tabular.yaml configs/default_run.yaml

```

### Step 3: Execute the Sweep

Modify `default_run.yaml` according to your experimental parameters. Pass it to the runner script:

```bash
python src/leaderboard/runner/runner_with_config_demo.py configs/default_run.yaml

```

*Note: If your configuration contains illegal values, mismatched algorithmic combinations, or unachievable budgets, the
system will immediately intercept the execution and display a formatted red boundary
box (`💥 CRITICAL CONFIGURATION ERROR`) detailing exactly how to fix the issue.*

---

## 🗂️ Exhaustive Parameter Dictionary

Every parameter defined in the YAML configuration files maps directly to the underlying `shapiq` library's evaluation
functions.

### 1. Base Game & Interaction Index Constraints

* **`game`** *(String)*: The exact string identifier of the dataset (e.g., `"AdultCensus"`, `"ImageClassifier"`,
  `"SOUM"`).
* **`game_family`** *(String)*: The scope of the explanation target.
* `local_xai`: Explains a localized model prediction for a single specific data instance.
* `global_xai`: Explains dataset-wide feature impacts by evaluating the overall model loss function.


* **`index`** *(String)*: The specific game-theoretic interaction index to compute.
* *Supported Whitelist*: `"SV"`, `"SII"`, `"k-SII"`, `"STII"`, `"FSII"`, `"FBII"`.


* **`max_order`** *(Integer)*: The maximum degree/order of the feature interactions.
* *Validation Rule*: If `index` is set to `"SV"`, `max_order` is mathematically restricted and MUST equal `1`. If an
  interaction index (like `"SII"`) is selected, `max_order` MUST be `>= 2`.


* **`n_players`** *(Integer)*: The dimension of the game (number of features). For tabular games, this is auto-inferred.
  For visual games, you must align this with the specific model architecture (e.g., `9` for `"vit_9_patches"`).

### 2. Black-Box Engine Control (`game_params`)

This nested dictionary controls the machine learning backend.

**Universal Parameters:**

* **`model_name`** *(String)*: The machine learning algorithm acting as the black box. Tabular games support
  `"decision_tree"` (highly recommended for performance), `"random_forest"`, or `"gradient_boosting"`. Visual games
  support `"vit_9_patches"` or `"resnet_18"`.
* **`normalize`** *(Boolean)*: Centers the baseline game values to 0 for the empty feature set. Set to `true` for
  standard ML tasks.
* **`verbose`** *(Boolean)*: Toggles internal game-level debugging logs.

**Local XAI Exclusive Parameters:** *(Ignored safely if family is global_xai)*

* **`imputer`** *(String)*: Determines how missing features (out-of-coalition features) are simulated. Supports
  `"marginal"` or `"conditional"`.
* **`x`** *(Integer)*: The row index of the specific instance in the dataset to be explained.
* **`class_to_explain`** *(Integer)*: The index of the target class probability. *Note: If the game is identified as a
  Regression task (e.g., `BikeSharing`), this parameter is automatically purged by the system to prevent downstream
  TypeErrors.*

**Global XAI Exclusive Parameters:** *(Ignored safely if family is local_xai)*

* **`loss_function`** *(String)*: The metric used to evaluate performance drops when features are masked.
* *Strict Cross-Validation*: Classification games (e.g., `AdultCensus`) MUST use `"accuracy_score"` or
  `"cross_entropy"`. Regression games MUST use `"mean_absolute_error"` or `"mean_squared_error"`. Mismatches trigger
  immediate execution halts.


* **`n_samples_eval`** *(Integer)*: Number of background rows sampled per coalition to shuffle missing features.
* **`n_samples_empty`** *(Integer)*: The background sample size used strictly to calculate the baseline empty-set loss
  value.

**Visual Game Exclusive Parameters:**

* **`x_explain_path`** *(String)*: The relative or absolute file path to the target image. This parameter is mandatory
  for the `ImageClassifier` game.

### 3. Ground Truth Computation Strategies (`ground_truth`)

Dictates how the absolute true values are derived against which approximators are measured.

* **`strategy`**: Currently defaults to `"compute"`.
* **`method`**: The backend computation engine.
* `"ExactComputer"`: Executes a brute-force calculation evaluating all 2^n feature coalitions.
* *Anti-Freeze Guard*: The system will throw a Critical Error if you attempt to use this on tabular games where `n > 14`
  to prevent memory starvation.


* `"TreeExplainer"`: Utilizes a highly optimized, polynomial-time tree traversal algorithm (fast for `n > 14`).
* *Upstream Bug Mitigation*: Due to known matrix initialization bugs in the upstream `shapiq v0.x` core, the
  configuration manager strictly blocks the use of `TreeExplainer` for high-order indices like `"STII"`, `"FSII"`, and
  `"FBII"`.

### 4. Execution Sweep Variables

These parameters accept lists and instruct the runner on how many iterations to sweep.

* **`approximators`** *(List[String])* : The sampling or regression algorithms you wish to benchmark (e.g.,
  `["OwenSamplingSV", "KernelSHAPIQ"]`).
* *Validation Rule*: The system verifies that the algorithms requested are officially registered in
  `shapiq.approximator` AND that they mathematically support your chosen `index`. Incompatible algorithms are
  automatically purged from the run list.


* **`budgets`** *(List[Integer])* : The exact number of black-box model evaluations allowed per algorithm.
* *Validation Rule*: Budgets must strictly satisfy the boundary condition: `n+1 <= budget < 2^n`. Out-of-bounds budgets
  are automatically removed to prevent algorithmic crashing.


* **`seeds`** *(List[Integer])* : Random seeds (e.g., `[0, 1, 2, 3]`) utilized to stabilize variance across stochastic
  sampling-based approximators.

---

## 🛠️ Extending the Benchmark Ecosystem

The benchmark architecture is highly decoupled. If you wish to benchmark novel datasets or custom approximators that are
not present in the default YAML templates, you do not need to modify the complex validation logic in the configuration
models. You only need to update the central registries.

### Registering a New Game (Dataset)

To introduce a new dataset to the leaderboard ecosystem:

1. **Ensure DataLoader Exists**: Verify that your data processing function is fully implemented and exposed in the
   `shapiq_games.datasets` module.
2. **Update the Single Source of Truth**: Open `src/leaderboard/config_manager/constants.py`.
3. **Bind to Registry**: Import your game class and map it inside either the `LOCAL_GAME_REGISTRY` or
   `GLOBAL_GAME_REGISTRY` dictionary.
4. **Define Dimensionality (CRITICAL)**: You MUST append the exact feature dimension size (e.g., `"MyNewDataset": 45`)
   to the `GAME_PLAYER_COUNTS` dictionary. The system relies on this hardcoded value to perform budget boundary
   validations and Out-Of-Memory guards.
5. **Task Classification**: If your new dataset is a Regression task (predicting continuous values rather than classes),
   you MUST add its string name to the `REGRESSION_GAMES` set to activate the loss-function cross-validation locks.

### Registering a New Approximator (Algorithm)

To add a new sampling or proxy algorithm to the benchmark comparison:

1. **Verify Upstream Integration**: Ensure that your custom algorithm class is properly implemented, inherits from
   `shapiq.approximator.Approximator`, and is correctly registered in the appropriate index capability lists inside the
   core `shapiq` package (e.g., `SV_APPROXIMATORS`).
2. **Update the Whitelist**: Open `src/leaderboard/config_manager/constants.py`.
3. **Append Name**: Add the precise, case-sensitive class name of your algorithm to the `ALL_SUPPORTED_APPROXIMATORS`
   list.

Once registered in the constants file, the Pydantic validator will immediately recognize it as a legitimate input,
allowing you to invoke it directly via the `approximators` list in your `default_run.yaml` files.