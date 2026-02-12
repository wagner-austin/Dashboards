"""Tests for config loading."""

from __future__ import annotations

import pytest

from scripts.config import (
    get_all_sample_columns,
    get_blank_columns,
    get_sample_columns,
    get_threshold,
    load_config,
)
from scripts.pipeline.types import Config


@pytest.fixture
def config() -> Config:
    """Load the real config.json."""
    return load_config()


def test_load_config_exists() -> None:
    """Test that config.json exists and loads."""
    config = load_config()
    assert config is not None
    assert "input" in config
    assert "output" in config
    assert "samples" in config
    assert "blanks" in config
    assert "thresholds" in config


def test_load_config_thresholds(config: Config) -> None:
    """Test that thresholds are present."""
    assert "blank_filter" in config["thresholds"]
    assert "cumulative_filter" in config["thresholds"]

    # Blank filter thresholds
    bf = config["thresholds"]["blank_filter"]
    assert "fold_change" in bf
    assert "p_value" in bf
    assert "fdr_correction" in bf

    # Cumulative filter threshold
    cf = config["thresholds"]["cumulative_filter"]
    assert "threshold" in cf


def test_get_threshold_blank_filter(config: Config) -> None:
    """Test getting blank filter threshold."""
    fold_change = get_threshold(config, "blank_filter", "fold_change")
    assert fold_change == 20.0

    p_value = get_threshold(config, "blank_filter", "p_value")
    assert p_value == 0.05


def test_get_threshold_cumulative(config: Config) -> None:
    """Test getting cumulative filter threshold."""
    threshold = get_threshold(config, "cumulative_filter", "threshold")
    assert threshold == 0.80


def test_get_sample_columns(config: Config) -> None:
    """Test getting sample column names."""
    leaf_drought = get_sample_columns(config, "leaf", "drought")
    assert len(leaf_drought) == 4
    assert "BL - Drought" in leaf_drought

    root_ambient = get_sample_columns(config, "root", "ambient")
    assert len(root_ambient) == 4
    assert "HR - Ambient" in root_ambient


def test_get_blank_columns(config: Config) -> None:
    """Test getting blank column names."""
    leaf_blanks = get_blank_columns(config, "leaf")
    assert len(leaf_blanks) == 2
    assert "Blk1" in leaf_blanks

    root_blanks = get_blank_columns(config, "root")
    assert len(root_blanks) == 4
    assert "250220_ebtruong_blank1" in root_blanks


def test_get_all_sample_columns(config: Config) -> None:
    """Test getting all sample column names."""
    all_cols = get_all_sample_columns(config)
    # 4 drought + 4 ambient + 4 watered for leaf = 12
    # 4 drought + 4 ambient + 3 watered for root = 11
    # Total = 23
    assert len(all_cols) == 23


def test_get_threshold_invalid_section(config: Config) -> None:
    """Test that invalid section raises KeyError."""
    with pytest.raises(KeyError, match="Unknown threshold section"):
        get_threshold(config, "invalid_section", "param")


def test_get_threshold_invalid_key(config: Config) -> None:
    """Test that invalid key raises KeyError."""
    with pytest.raises(KeyError, match="Unknown blank_filter key"):
        get_threshold(config, "blank_filter", "invalid_key")


def test_get_threshold_detection(config: Config) -> None:
    """Test getting detection threshold."""
    min_value = get_threshold(config, "detection", "min_value")
    assert min_value == 0.0


def test_get_threshold_invalid_cumulative_key(config: Config) -> None:
    """Test that invalid cumulative_filter key raises KeyError."""
    with pytest.raises(KeyError, match="Unknown cumulative_filter key"):
        get_threshold(config, "cumulative_filter", "invalid_key")


def test_get_threshold_invalid_detection_key(config: Config) -> None:
    """Test that invalid detection key raises KeyError."""
    with pytest.raises(KeyError, match="Unknown detection key"):
        get_threshold(config, "detection", "invalid_key")


def test_load_config_missing_file() -> None:
    """Test that missing config file raises FileNotFoundError."""
    from pathlib import Path

    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config(Path("/nonexistent/path/config.json"))


def test_get_sample_columns_invalid_tissue(config: Config) -> None:
    """Test that invalid tissue raises KeyError."""
    with pytest.raises(KeyError, match="Unknown tissue"):
        get_sample_columns(config, "invalid_tissue", "drought")


def test_get_sample_columns_invalid_treatment(config: Config) -> None:
    """Test that invalid treatment raises KeyError."""
    with pytest.raises(KeyError, match="Unknown treatment"):
        get_sample_columns(config, "leaf", "invalid_treatment")


def test_get_blank_columns_invalid_tissue(config: Config) -> None:
    """Test that invalid tissue raises KeyError."""
    with pytest.raises(KeyError, match="Unknown tissue"):
        get_blank_columns(config, "invalid_tissue")
