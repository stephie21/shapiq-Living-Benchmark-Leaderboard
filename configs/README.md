# shapiq Benchmark Configurations

This directory contains all configuration files required to run the `shapiq` benchmark experiments. The configuration
system relies on strict Pydantic typing and an intelligent "Silent Purge" mechanism to ensure runtime safety, parameter
consistency, and automatic cross-validation of experimental setups.

---

## 📊 Benchmark Run Plan & Progress Status

Below is the active execution tracker detailing the configurations, feature dimensions ($n$), target indices, and
specific computational budgets assigned for our ongoing benchmark evaluations.

| Game Name               | Players ($n$) | Game Family    | Target Index                                               | Evaluation Budgets          | Random Seeds |
|:------------------------|:-------------:|:---------------|:-----------------------------------------------------------|:----------------------------|:-------------|
| **CaliforniaHousing**   |       8       | Local XAI      | `SII` (3), `k-SII` (3), `STII` (3), `FBII` (4), `FSII` (4) | 250                         | 10           |
| **BikeSharing**         |      12       | Local XAI      | `SV`, `k-SII`, `SII`, `STII`, `FBII`, `FSII`               | 250, 500, 1000              | 30           |
| **AdultCensus**         |      14       | **Global XAI** | `SV`, `k-SII`, `SII`, `STII`                               | 250, 500, 1000, 5000, 10000 | 10           |
| **Mushroom**            |      22       | Local XAI      | `SV`, `SII`, `k-SII`                                       | 250, 500, 1000, 5000, 10000 | 6            |
| **Soybean**             |      35       | Local XAI      | `SV`, `SII`, `k-SII`                                       | 250, 500, 1000, 5000, 10000 | 8            |
| **Splice**              |      60       | Local XAI      | `SV`, `SII`, `k-SII`                                       | 250, 500, 1000, 5000, 10000 | 10           |
| **TaiwaneseBankruptcy** |      94       | Local XAI      | `SV`, `SII`, `k-SII`                                       | 250, 500, 1000, 5000, 10000 | 10           |
| **Arrhythmia**          |      279      | Local XAI      | `SV`                                                       | 1000, 5000, 10000           | 5            |
| **Arrhythmia**          |      279      | Local XAI      | `SII`                                                      | 500, 1000, 5000             | 10           |
| **ImageClassifier**     |       9       | Local XAI      | `SV`                                                       | 250, 500                    | 3            |
| **ImageClassifier**     |       9       | Local XAI      | `k-SII`                                                    | 100, 200, 400               | 4            |

### Special Execution Notes & Hardware Stress Tests

1. **Arrhythmia Extreme Dimensionality ($n=279$)**:
    * Due to the massive feature space, this dataset requires execution on a secondary high-performance workstation.
    * *\*Note on `SV`*: The `kADDSHAP` approximator has only completed 10 runs strictly at a budget of 1000.
    * *\*\*Note on `SII`*: The `KernelSHAPIQ` and `InconsistentKernelSHAPIQ` approximators have only completed 1 run at
      a budget of 1000 due to severe computational overhead.
2. **ImageClassifier (Computer Vision via Deep Learning)**:
    * This black-box task evaluates image patches/superpixels and is completed strictly via `ExactComputer`. Expect
      significant CPU/RAM spikes during initialization as Hugging Face ViT/ResNet weights are downloaded and heavy
      matrix multiplications are executed.
    * *\*\*\*Scale Updates*: A new pipeline execution featuring budgets of 250 and 500 across $n=14$ players is
      currently scheduled.
    * *Optimization Strategy*: For $n=9$ players (resulting in exactly 512 total coalitions), utilizing just 2 discrete
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

Clone your chosen template to create your active run file. The runner defaults to looking for **default_run.yaml**.
Alternatively, you can copy or reference ready-to-use configuration files from existing game directories. For example,
you can use the predefined YAML files located inside the Soybean n = 35 folder, such as SV_Soybean n = 35.yaml,
SII_Soybean n = 35.yaml, or k-SII_Soybean n = 35.yaml. You can clone these files via the command line, or simply open
them in your IDE and manually copy and paste the YAML content directly into your default_run.yaml.

<img width="443" height="410" alt="Screenshot 2026-07-17 at 13 41 10" src="https://github.com/user-attachments/assets/f1f1d477-d203-423c-977d-7f8f55ba4199" />

```bash
cp configs/template_tabular.yaml configs/default_run.yaml

```

### Step 3: Execute the Sweep

Modify `default_run.yaml` according to your experimental parameters then start the runner script:

```bash
python src/leaderboard/runner/runner_with_config.py

```

Note:

* The system employs a two-tier validation process. Severe structural errors (such as completely missing mandatory
  fields like budgets) will immediately intercept the execution and display a formatted red boundary box (💥 CRITICAL
  CONFIGURATION ERROR) detailing how to fix the issue.
* However, recoverable logic issues, such as unachievable budgets (
  e.g., exceeding $2^n$) or unsupported approximators—are handled by the "Silent Purge" mechanism. The system will
  automatically filter these invalid entries out and continue executing the remaining valid configurations.

### Configuration Flow Diagram

```text
+-------------------+       +-------------------------+       +-------------------------+
|                   |       |                         |       |                         |
| default_run.yaml  | ----> | config_manager/loader   | ----> |   Runner Execution      |
| (User Input)      |       | (Pydantic Validation)   |       |   (shapiq pipeline)     |
|                   |       |                         |       |                         |
+-------------------+       +-------------------------+       +-------------------------+
                                        |
                                        |  - Validates boundaries (e.g., budgets < 2^n)
                                        |  - Enforces shapiq algorithmic compatibility
                                        V  - Auto-purges irrelevant parameters
```

---

## Parameter Dictionary & `shapiq` Mapping

Every parameter defined in the YAML configuration files maps directly to the underlying `shapiq` library's evaluation
functions.

### 1. Base Game & Interaction Index Constraints

* **`game`** *(String)*: The exact string identifier of the dataset (e.g., `"AdultCensus"`, `"ImageClassifier"`,
  `"SOUM"`).
* **`game_family`** *(String)*: Determines the scope of the explanation target.
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

This nested dictionary controls the machine learning backend. *(Note: The system automatically purges parameters that do not belong to the active `game_family`)*.

**Universal Parameters:**

* **`model_name`** *(String)*: The machine learning algorithm acting as the black box. Visual games support `"vit_9_patches"` or `"resnet_18"`. Tabular games support:
  * `"decision_tree"`: **(Highly Recommended)** Extremely fast. Best for debugging and large games ($n > 14$).
  * `"random_forest"`: Very slow. Every coalition requires traversing all trees. May cause overheating when paired with sampling approximators.
  * `"gradient_boosting"`: Extremely slow. Use strictly for realistic baseline benchmarking on small games.
* **`normalize`** *(Boolean)*: Centers the baseline game values to 0 for the empty feature set. Set to `true` for standard ML tasks.
* **`verbose`** *(Boolean)*: Toggles internal game-level debugging logs.


**Local XAI Exclusive Parameters:** *(Ignored safely if family is global_xai)*

* **`imputer`** *(String)*: Determines how missing features (out-of-coalition features) are simulated. Supports
  `"marginal"` or `"conditional"`.
* **`x`** *(Integer)*: The row index of the specific instance in the dataset to be explained.
* **`class_to_explain`** *(Integer)*: The index of the target class probability. *Note: If the game is identified as a
  Regression task (e.g., `BikeSharing`), this parameter is automatically purged by the system to prevent downstream
  TypeErrors*.

**Global XAI Exclusive Parameters:** *(Ignored safely if family is local_xai)*

* **`loss_function`** *(String)*: The metric used to evaluate performance drops when features are masked.
* *Strict Cross-Validation*: Classification games (e.g., `AdultCensus`) MUST use `"accuracy_score"` or
  `"cross_entropy"`. Regression games MUST use `"mean_absolute_error"` or `"mean_squared_error"`. Mismatches trigger
  immediate execution halts.


* **`n_samples_eval`** *(Integer)*: Number of background rows sampled per coalition to shuffle missing features.
* **`n_samples_empty`** *(Integer)*: The background sample size used strictly to calculate the baseline empty-set loss
  value.

**Visual Game Exclusive Parameters:**

* **`x_explain_path`** *(String)*: The relative or absolute file path (`src/shapiq_games/benchmark/imagenet_examples`)
  to
  the target image. This parameter is mandatory
  for the `ImageClassifier` game.
* **`n_superpixel_resnet`** *(Integer)*: Configuration for ResNet-18 superpixel grouping (only active if model_name is "
  resnet_18").

### 3. Ground Truth Computation Strategies (`ground_truth`)

Dictates how the absolute true values are derived against which approximators are measured.

* **`strategy`**: Currently only support to `"compute"`.
* **`method`**: The backend computation engine.
* **ExactComputer**: Executes a brute-force calculation evaluating all $O(2^n)$ feature coalitions.
* `Anti-Freeze Guard`: The system will throw a Critical Error if you attempt to use this on tabular games where `n > 14`
  to prevent combinatorial explosion.
* **TreeExplainer**: Utilizes a highly optimized, polynomial-time tree traversal algorithm (fast for $n > 14$).
* `Upstream Bug Mitigation`: Due to known matrix initialization bugs in the upstream `shapiq v1.5.0` core, the
  configuration manager strictly blocks the use of `TreeExplainer` for high-order indices like `"STII"`, `"FSII"`, and
  `"FBII"`.

### 4. Execution Sweep Variables

These parameters accept lists and instruct the runner on how many iterations to sweep.

**`approximators`** *(List[String])*
The sampling or regression algorithms you wish to benchmark.

* **Validation Rule**: The system verifies that the algorithms requested are officially registered in `shapiq.approximator` AND that they mathematically support your chosen `index`. Incompatible algorithms are automatically purged from the run list.

**Supported Whitelists by Index:**

| Index Type | Supported Approximators |
| --- | --- |
| **SV** | `"OwenSamplingSV"`, `"StratifiedSamplingSV"`, `"SVARM"`, `"UnbiasedKernelSHAP"`, `"PermutationSamplingSV"`, `"KernelSHAP"`, `"kADDSHAP"`, `"ProxySPEX"`, `"ProxySHAP"` |
| **SII / k-SII** | `"PermutationSamplingSII"`, `"KernelSHAPIQ"`, `"InconsistentKernelSHAPIQ"`, `"SVARMIQ"`, `"SHAPIQ"`, `"ProxySPEX"`, `"ProxySHAP"` |
| **STII** | `"PermutationSamplingSTII"`, `"SVARMIQ"`, `"SHAPIQ"`, `"ProxySPEX"`, `"ProxySHAP"` |
| **FSII** | `"RegressionFSII"`, `"SVARMIQ"`, `"SHAPIQ"`, `"ProxySPEX"`, `"ProxySHAP"` |
| **FBII** | `"RegressionFBII"`, `"ProxySPEX"`, `"ProxySHAP"` |

* **⚠️ Critical Algorithmic Notes & Exceptions**: `"BV"` and `"CHII"` are currently not supported by the runner pipeline. `"SPEX"` has been replaced by `"ProxySPEX"` due to performance issues. `"SVARM"` and `"SVARMIQ"` will be automatically removed from the run when the player count ($n$) exceeds 20 due to performance issues. `"KernelSHAPIQ"` and `"InconsistentKernelSHAPIQ"` strictly require `SV`, `SII`, or `k-SII`. `"MSRBiased"` has been removed from the pipeline due to deprecation.

**`budgets`** *(List[Integer] e.g., `[250, 500, 1000, 5000,10000]`)*
The exact number of black-box model evaluations allowed per algorithm.

* **Validation Rule**: Budgets must strictly satisfy the boundary condition $n+1 \le \text{budget} < 2^n$. Out-of-bounds budgets are automatically removed to prevent algorithmic crashing.
* **Visual Game Warning**: For ImageClassifier games, the computational cost per sample is exceptionally high. It is strongly recommended to start with lower budgets (e.g., 250, 500).

**`seeds`** *(List[Integer] e.g., `[0, 1, 2, 3,...,29]`)*
Random seeds utilized to stabilize variance across stochastic sampling-based approximators.

---

## 🛠️ Extending the Benchmark Ecosystem

The benchmark architecture is highly decoupled. If you need to test new datasets or algorithms beyond the standard templates, you do not need to modify the complex validation logic in the configuration models. You only need to update the central registries located within the `config_manager`.

*(Refer to the [config_manager README](../src/leaderboard/config_manager/README.md) for complete integration steps)*

<img width="381" height="261" alt="Screenshot 2026-07-17 at 14 04 04" src="https://github.com/user-attachments/assets/893c9b37-7e8a-44cc-87e1-9f54d970b304" />

### Registering a New Game (Dataset)

To introduce a new dataset to the leaderboard ecosystem, whether it is already available in the `shapiq` dataset module or a custom one from the web:

1. **Follow the Config Manager Guide**: First, refer to the step-by-step code modification guide in the `config_manager/README.md` to properly set up the data loader, declare the feature dimensions ($n$), and define the task type.
2. **Expose the Game Name**: Open `src/leaderboard/config_manager/constants.py` and simply add your new game's string identifier to the designated game registry list.

### Registering a New Approximator (Algorithm)

To add a new sampling or proxy algorithm to the benchmark comparison:

1. **Verify Upstream Integration**: Ensure the algorithm class is fully implemented and integrated into the core `shapiq.approximator` package.
2. **Append Approximator Name**: Open `src/leaderboard/config_manager/constants.py` and add the precise, case-sensitive class name of your algorithm to the supported whitelist.

Once the name is added here, the central Pydantic validators will immediately recognize it as a legitimate input, allowing you to invoke it directly via the `approximators` list in your `default_run.yaml` files.
