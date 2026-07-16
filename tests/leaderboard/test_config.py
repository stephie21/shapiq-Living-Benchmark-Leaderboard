"""Unified Test Suite for Configuration Manager.

This file replaces all previous redundant test files and directly tests the behaviors
defined in models.py and loader.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from leaderboard.config_manager.loader import load_and_validate_config

# Import the core configuration models
from leaderboard.config_manager.models import GroundTruthConfig, MVPRunConfig


@pytest.fixture
def base_config_data() -> dict:
    """Fixture providing a standard, fully valid configuration dictionary.
    Uses a small local_xai classification game to pass ExactComputer guards.
    """
    return {
        "game": "AdultCensus",
        "game_family": "local_xai",
        "index": "SV",
        "max_order": 1,
        "n_players": 14,
        "game_seed": 42,
        "approximators": ["PermutationSamplingSV", "KernelSHAP"],
        "budgets": [100, 500],
        "seeds": [0, 1, 2],
        "ground_truth": {"strategy": "compute", "method": "ExactComputer"},
        "game_params": {"model_name": "decision_tree", "imputer": "marginal"},
    }


def test_valid_config_initialization(base_config_data: dict) -> None:
    """Test that a completely valid configuration parses successfully."""
    config = MVPRunConfig(**base_config_data)
    assert config.game == "AdultCensus"
    assert config.index == "SV"
    assert config.n_players == 14
    assert config.game_family == "local_xai"


def test_soum_game_bypasses_constraints_and_purges_params(base_config_data: dict) -> None:
    """Test that the SOUM game bypasses ExactComputer limits and purges ML parameters."""
    base_config_data["game"] = "SOUM"
    base_config_data["n_players"] = 25
    base_config_data["ground_truth"]["method"] = "ExactComputer"
    base_config_data["game_params"] = {
        "model_name": "decision_tree",
        "imputer": "marginal",
        "n_basis_games": 10,
    }

    config = MVPRunConfig(**base_config_data)

    # 1. Verify n_players is forcefully overridden to the hardcoded value (10) for SOUM
    assert config.n_players == 10

    # 2. Verify SOUM successfully purges irrelevant ML parameters
    assert "model_name" not in config.game_params
    assert "imputer" not in config.game_params

    # 3. Verify SOUM-specific mathematical parameters are retained
    assert config.game_params.get("n_basis_games") == 10


def test_unsupported_enum_parameters_raise_error(base_config_data: dict) -> None:
    """Test that invalid imputers or models correctly trigger the whitelist validation."""
    # Test an unsupported imputer
    base_config_data["game_params"]["imputer"] = "magic_imputer"
    # Match string must be uppercase because format_config_error uses .upper()
    with pytest.raises(ValidationError, match="INVALID INPUT AT PARAMETER 'IMPUTER'"):
        MVPRunConfig(**base_config_data)

    # Test an unsupported model_name
    base_config_data["game_params"] = {"model_name": "magic_model"}
    # Match string must be uppercase because format_config_error uses .upper()
    with pytest.raises(ValidationError, match="INVALID INPUT AT PARAMETER 'MODEL_NAME'"):
        MVPRunConfig(**base_config_data)


def test_loader_successfully_parses_valid_yaml(tmp_path: Path, base_config_data: dict) -> None:
    """Test that the loader correctly parses and validates a valid YAML file."""
    # Create a temporary valid yaml file using pytest's tmp_path fixture
    yaml_file = tmp_path / "valid_config.yaml"
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(base_config_data, f)

    config = load_and_validate_config(yaml_file)

    # Verify the file is read and instantiated as MVPRunConfig correctly
    assert config is not None
    assert config.game == "AdultCensus"
    assert config.n_players == 14


def test_loader_exits_on_invalid_yaml(tmp_path: Path, base_config_data: dict) -> None:
    """Test that the loader intercepts Pydantic errors and triggers a sys.exit(1)."""
    # Intentionally cause a critical error: use an unsupported game name
    base_config_data["game"] = "BogusGameName"

    yaml_file = tmp_path / "invalid_config.yaml"
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(base_config_data, f)

    # By design in loader.py, config errors are caught and trigger sys.exit(1)
    with pytest.raises(SystemExit) as excinfo:
        load_and_validate_config(yaml_file)

    # Ensure the exit code is 1
    assert excinfo.value.code == 1


def test_game_family_validation_rejects_mismatch(base_config_data: dict) -> None:
    """Test that configuring a local game as global_xai raises an error."""
    base_config_data["game"] = "Mushroom"  # Mushroom is purely local_xai
    base_config_data["game_family"] = "global_xai"

    with pytest.raises(ValidationError, match="not available as a global_xai game"):
        MVPRunConfig(**base_config_data)


def test_budget_filtering_and_fallback(base_config_data: dict) -> None:
    """Test that out-of-bounds budgets are stripped and a fallback is generated if empty."""
    # For AdultCensus (n=14), valid range is 15 <= budget < 16384
    base_config_data["budgets"] = [10, 100, 20000]

    config = MVPRunConfig(**base_config_data)
    # 10 and 20000 should be stripped out
    assert config.budgets == [100]

    # Test complete fallback when ALL are invalid
    base_config_data["budgets"] = [10, 20000]
    config2 = MVPRunConfig(**base_config_data)
    # Should fallback to (n_players + 1) * 2 = (14 + 1) * 2 = 30
    assert config2.budgets == [30]


def test_approximator_filtering_and_incompatibility(base_config_data: dict) -> None:
    """Test that invalid or index-incompatible approximators are filtered out."""
    base_config_data["index"] = "SII"
    base_config_data["max_order"] = 2
    # 'PermutationSamplingSV' is SV-only, so it should be stripped for SII
    # 'KernelSHAP' is SV-only, should be stripped
    # 'PermutationSamplingSII' is SII compatible
    # 'BogusName' is completely invalid
    base_config_data["approximators"] = [
        "PermutationSamplingSV",
        "PermutationSamplingSII",
        "BogusName",
        "KernelSHAP",
    ]

    config = MVPRunConfig(**base_config_data)
    # Only the SII-compatible one should survive
    assert config.approximators == ["PermutationSamplingSII"]


def test_max_order_validation(base_config_data: dict) -> None:
    """Test that index and max_order enforce structural rules."""
    # SV must have order 1
    base_config_data["index"] = "SV"
    base_config_data["max_order"] = 2
    with pytest.raises(ValidationError, match="When computing SV, max_order must be 1"):
        MVPRunConfig(**base_config_data)

    # Interaction indices must have order >= 2
    base_config_data["index"] = "SII"
    base_config_data["max_order"] = 1
    with pytest.raises(ValidationError, match="max_order must be at least 2"):
        MVPRunConfig(**base_config_data)


def test_game_params_purging_for_global_games(base_config_data: dict) -> None:
    """Test that global_xai dynamically purges local_xai-specific parameters."""
    base_config_data["game_family"] = "global_xai"
    base_config_data["game_params"] = {
        "imputer": "marginal",  # Should be purged
        "x": 0,  # Should be purged
        "class_to_explain": 1,  # Should be purged
        "model_name": "decision_tree",  # Should remain
    }

    config = MVPRunConfig(**base_config_data)
    assert "imputer" not in config.game_params
    assert "x" not in config.game_params
    assert "class_to_explain" not in config.game_params
    assert config.game_params["model_name"] == "decision_tree"


def test_game_params_loss_function_task_mismatch(base_config_data: dict) -> None:
    """Test that regression games reject classification losses and vice versa."""
    # Must be global_xai to prevent 'loss_function' from being purged by local_xai checks
    base_config_data["game_family"] = "global_xai"

    # Test Regression Game with Classification Loss
    base_config_data["game"] = "CaliforniaHousing"  # Regression
    base_config_data["n_players"] = 8
    base_config_data["game_params"] = {"loss_function": "accuracy_score"}

    with pytest.raises(ValidationError, match="TASK MISMATCH"):
        MVPRunConfig(**base_config_data)

    # Test Classification Game with Regression Loss
    base_config_data["game"] = "AdultCensus"  # Classification
    base_config_data["n_players"] = 14
    base_config_data["game_params"] = {"loss_function": "mean_squared_error"}

    with pytest.raises(ValidationError, match="TASK MISMATCH"):
        MVPRunConfig(**base_config_data)


def test_visual_game_constraints(base_config_data: dict) -> None:
    """Test that visual games enforce exact computer and valid patch constraints."""
    base_config_data["game"] = "ImageClassifier"
    base_config_data["game_params"] = {
        "model_name": "vit_9_patches",
        "x_explain_path": "/dummy/path",
    }
    # Test mismatching n_players (vit_9_patches requires n=9)
    base_config_data["n_players"] = 14
    with pytest.raises(ValidationError, match="requires n_players=9"):
        MVPRunConfig(**base_config_data)

    # Test invalid Ground Truth method
    base_config_data["n_players"] = 9
    base_config_data["ground_truth"]["method"] = "TreeExplainer"
    with pytest.raises(ValidationError, match="TreeExplainer' is not applicable"):
        MVPRunConfig(**base_config_data)


def test_large_game_exact_computer_freeze_guard(base_config_data: dict) -> None:
    """Test that exact computer is blocked for large games to prevent freezes."""
    base_config_data["game"] = "Splice"
    base_config_data["n_players"] = 60  # > 14

    with pytest.raises(ValidationError, match="COMBINATORIAL RUNTIME EXPLOSION IMMINENT"):
        MVPRunConfig(**base_config_data)


def test_global_xai_tree_explainer_blocked(base_config_data: dict) -> None:
    """Test that global explanations cannot be evaluated via TreeExplainer."""
    base_config_data["game_family"] = "global_xai"
    base_config_data["ground_truth"]["method"] = "TreeExplainer"

    with pytest.raises(ValidationError, match="You MUST use 'ExactComputer'"):
        MVPRunConfig(**base_config_data)


def test_shapiq_upstream_bug_guard_for_high_order_indices(base_config_data: dict) -> None:
    """Test that STII/FSII/FBII with TreeExplainer intercepts upstream bugs."""
    base_config_data["index"] = "STII"
    base_config_data["max_order"] = 2
    base_config_data["ground_truth"]["method"] = "TreeExplainer"

    with pytest.raises(ValidationError, match="SHAPIQ UPSTREAM BUG DETECTED"):
        MVPRunConfig(**base_config_data)
