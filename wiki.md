# shapiq Living Benchmark Leaderboard Wiki

Our leaderboard is also available on HuggingFace Spaces! Check it out: [Leaderboard](https://huggingface.co/spaces/JJ248/shapiq-leaderboard)

## Purpose of the leaderboard

The Living Benchmark Leaderboard primarily serves as a support tool for users of SHAPIQ. Its goal is to help users identify suitable approximators for a selected benchmark context. Users can filter the available benchmark data by game, interaction index, budget, and metric. Internally, these variables are used to define comparable groups within which approximators can be evaluated against one another.

The approximators are ranked primarily using the implemented Elo system. In addition, an alternative ranking based on Critical Difference Plots is available.

While the Elo system provides a compact relative rating that accounts for the strength of the compared opponents, Critical Difference Plots can better illustrate which approximators differ meaningfully across comparable benchmark groups.

The leaderboard was developed with a strong focus on extensibility. New approximators, games, metrics, scorers, and even new storage options should integrate well into the existing architecture.

## Overview of the components

The `configs` folder is the central storage location for benchmark configurations. These configurations are loaded and validated by the Config Manager. The Config Manager acts as a validation layer between user-defined YAML files and the execution pipeline. It checks the configuration, removes incompatible parameters where possible, and prevents invalid or unsupported benchmark setups from reaching the Runner.

The actual approximation is performed by the Runner using the parameters defined in the configuration. The Runner generates raw run records that are then stored through the Storage component.

The Storage component provides a unified interface for storing and loading benchmark records. The currently supported storage backends are MongoDB, local JSONL files, and Hugging Face Datasets. This allows the same runner and UI logic to work with different persistence options.

The stored benchmark data is connected to the user interface. Data can be loaded into the UI, although usually only a user-selected subset of the available data is used for ranking and visualization.

The approximators are ranked on the basis of the selected run records with the help of a Scorer. Both the Runner and the Scorer use a range of available metrics for their calculations. The Metrics package defines the canonical metric keys, aliases, metric direction metadata, and metric computation logic used throughout the benchmark pipeline.

The PDL package contains functionality for pairwise difference learning and metric sensitivity analysis. It can be used to investigate under which benchmark contexts one approximator tends to outperform another.

## Deployment

The leaderboard can be deployed locally or on Hugging Face Spaces. The UI is built with Gradio and uses `app.py` as the project-root entry point for deployment. Before deployment, the storage backend must be configured, because the UI loads leaderboard data from the selected storage system.

For local development and testing, local JSONL storage is sufficient. For collaborative benchmark population, MongoDB is recommended. For stable public leaderboard snapshots, Hugging Face Datasets can be used as a versioned data backend.

## Package documentation

For more detailed information about the individual components, see the package-specific documentation:

- [Config Manager](https://github.com/stephie21/shapiq-Living-Benchmark-Leaderboard/blob/main/src/leaderboard/config_manager/README.md)
- [Runner](https://github.com/stephie21/shapiq-Living-Benchmark-Leaderboard/blob/main/src/leaderboard/runner/README.md)
- [Metrics](https://github.com/stephie21/shapiq-Living-Benchmark-Leaderboard/blob/main/src/leaderboard/metrics/README.md)
- [Storage](https://github.com/stephie21/shapiq-Living-Benchmark-Leaderboard/blob/main/src/leaderboard/storage/README.md)
- [Scoring](https://github.com/stephie21/shapiq-Living-Benchmark-Leaderboard/blob/main/src/leaderboard/scoring/README.md)
- [UI](https://github.com/stephie21/shapiq-Living-Benchmark-Leaderboard/tree/main/src/leaderboard/ui/README.md)
- [PDL](https://github.com/stephie21/shapiq-Living-Benchmark-Leaderboard/blob/main/src/leaderboard/pdl/README.md)
- [Deployment](https://github.com/stephie21/shapiq-Living-Benchmark-Leaderboard/blob/main/src/leaderboard/deployment.md)
