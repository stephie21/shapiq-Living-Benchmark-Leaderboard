## Runner README

### Purpose of the runner

The purpose of the runner is to execute benchmark experiments for selected games, approximators, interaction indices, budgets, and random seeds. It connects to the configuration component and produces run records that can later be stored.

A benchmark run follows the general workflow:

1. Create the configured game instance.
2. Resolve the configured approximator class.
3. Compute the ground truth interaction values.
4. Run the approximator for one or more approximation seeds.
5. Align the approximated values with the ground truth.
6. Compute evaluation metrics.
7. Build standardized raw run records.
8. Store the raw records in the configured storage backend.

The main output of the runner is a list of raw run records. Each raw record represents one approximation seed and contains benchmark metadata, metric values, runtime information, hardware information, and failure status.

### Running a single benchmark

The central function for running one benchmark setup is `run_benchmark`. It receives an already constructed game, one approximator class, one interaction index, one budget, and a list of approximation seeds.

For each seed, the runner executes the approximator and creates one raw run record. After all seeds have been processed, the raw records are aggregated into one representative result.

**Run benchmark example:**

~~~python
benchmark_result = run_benchmark(
    game=game,
    game_name="SOUM",
    game_params=game_params,
    max_order=2,
    approx_seeds=list(range(30)),
    budget=100,
    index="SII",
    approximator_class=ProxySHAP,
)

raw_records = benchmark_result["raw_results"]
aggregated_record = benchmark_result["aggregated_result"]
~~~

The raw records are the most important output for the leaderboard pipeline. They preserve the individual seed-level results and are therefore suitable for later aggregation, scoring, debugging, and statistical analysis.

### Running a sweep on configs

For larger experiments, the runner can execute a config-driven benchmark sweep. The YAML config defines the benchmark context, including the game, interaction index, maximum order, approximators, budgets, seeds, and ground truth method.

The sweep expands the validated config into concrete benchmark setups. Currently, the main sweep dimensions are approximators and budgets. Seeds are not expanded into separate top-level configs; instead, all configured seeds are passed to `run_benchmark` and executed within each approximator-budget setup.

In practice, this means that a config with three approximators, two budgets, and five seeds creates six benchmark setups and produces thirty raw run records.

To run a sweep, first prepare a YAML config and then pass it to the runner:

~~~bash
python -m leaderboard.runner.runner_with_config configs/default_run.yaml
~~~

If no config path is provided, the runner uses the default config path defined in the script.

### Package structure

The runner package is organized around benchmark orchestration, config expansion, game and approximator construction, experiment execution, record creation, and storage integration.

| File | Classification | Description |
|---|---|---|
| `__init__.py` | Package marker | Marks the runner directory as a Python package. |
| `benchmark_runner.py` | Main benchmark orchestration | Provides `run_benchmark`, which computes ground truth, runs experiments over seeds, aggregates the results, and returns raw and aggregated benchmark records. |
| `runner_with_config.py` | Config-based sweep entry point | Loads and validates a YAML config, expands it into concrete run configurations, creates games and approximators, runs benchmarks, and stores raw results. |
| `config_loader.py` | Simple config expansion | Loads YAML configs and expands singular or plural approximator/budget fields into concrete run configurations. |
| `game_factory.py` | Game construction | Creates game instances from run and base configuration data. It handles local XAI games, global XAI games, SOUM, default parameters, and selected path resolution. |
| `approximator_registry.py` | Approximator lookup | Maps approximator names from the config to concrete `shapiq` approximator classes. |
| `approximator_runner.py` | Approximation execution | Instantiates one approximator and runs it on a game with a given budget and seed. |
| `ground_truth_computer.py` | Ground truth computation | Computes exact interaction values with `ExactComputer` or `TreeExplainer`, depending on the configured method. |
| `experiment_runner.py` | Seed-level experiment execution | Runs one or more approximation seeds, aligns approximated values with ground truth, computes metrics, and creates raw run records. |
| `record_builder.py` | Run record creation | Creates standardized benchmark records containing metadata, metrics, runtime, hardware information, and failure status. |
| `aggregator.py` | Result aggregation | Aggregates multiple successful raw run records into one representative record by averaging metrics and runtime values. |
| `runner_storage_adapter.py` | Storage adapter | Provides helper functions for storing raw run records in a database or appending them to a local JSONL file. |
| `environment_info.py` | Runtime metadata | Collects hardware and Python runtime information for inclusion in run records. |
| `custom_types.py` | Shared type aliases | Defines runner-specific type aliases such as supported interaction indices and metric function types. |
| `runner_exceptions.py` | Runner error types | Defines custom exceptions for missing metrics, failed aggregation, interaction-key mismatches, and unknown games. |
| `runner_demo.py` | Manual single-run demo | Runs a hard-coded local SOUM benchmark example and stores the raw results. |
