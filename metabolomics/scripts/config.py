"""Configuration loader for the metabolomics pipeline.

Loads config.json and provides typed access to all settings.
This is the SINGLE SOURCE OF TRUTH for all pipeline parameters.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.pipeline.types import (
    Config,
    decode_config,
    require_dict,
)


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from config.json.

    Args:
        config_path: Path to config.json. Defaults to project root.

    Returns:
        Validated Config TypedDict.

    Raises:
        FileNotFoundError: If config.json doesn't exist.
        TypeError: If config.json has invalid types.
        KeyError: If config.json is missing required keys.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        raw = json.load(f)

    # Validate it's a dict
    raw_dict = require_dict(raw, "config")

    # Decode and validate all fields
    return decode_config(raw_dict)


def get_sample_columns(config: Config, tissue: str, treatment: str) -> list[str]:
    """Get sample column names for a tissue/treatment combination.

    Args:
        config: Loaded config.
        tissue: "leaf" or "root" (case insensitive).
        treatment: "drought", "ambient", or "watered" (case insensitive).

    Returns:
        List of column names.

    Raises:
        KeyError: If tissue or treatment is unknown.
    """
    tissue_lower = tissue.lower()
    treatment_lower = treatment.lower()

    if tissue_lower == "leaf":
        samples = config["samples"]["leaf"]
    elif tissue_lower == "root":
        samples = config["samples"]["root"]
    else:
        raise KeyError(f"Unknown tissue: {tissue}")

    if treatment_lower == "drought":
        return samples["drought"]
    elif treatment_lower == "ambient":
        return samples["ambient"]
    elif treatment_lower == "watered":
        return samples["watered"]
    else:
        raise KeyError(f"Unknown treatment: {treatment}")


def get_blank_columns(config: Config, tissue: str) -> list[str]:
    """Get blank column names for a tissue.

    Args:
        config: Loaded config.
        tissue: "leaf" or "root" (case insensitive).

    Returns:
        List of blank column names.

    Raises:
        KeyError: If tissue is unknown.
    """
    tissue_lower = tissue.lower()

    if tissue_lower == "leaf":
        return config["blanks"]["leaf"]
    elif tissue_lower == "root":
        return config["blanks"]["root"]
    else:
        raise KeyError(f"Unknown tissue: {tissue}")


def get_all_sample_columns(config: Config) -> list[str]:
    """Get all sample column names across all tissues and treatments.

    Args:
        config: Loaded config.

    Returns:
        List of all sample column names.
    """
    cols: list[str] = []
    for tissue in ["leaf", "root"]:
        for treatment in ["drought", "ambient", "watered"]:
            cols.extend(get_sample_columns(config, tissue, treatment))
    return cols


def get_threshold(config: Config, section: str, key: str) -> float:
    """Get a threshold value from config.

    Args:
        config: Loaded config.
        section: Threshold section ("blank_filter", "cumulative_filter", "detection").
        key: Key within the section.

    Returns:
        The threshold value as float.

    Raises:
        KeyError: If section or key doesn't exist.
    """
    thresholds = config["thresholds"]
    if section == "blank_filter":
        if key == "fold_change":
            return thresholds["blank_filter"]["fold_change"]
        elif key == "p_value":
            return thresholds["blank_filter"]["p_value"]
        else:
            raise KeyError(f"Unknown blank_filter key: {key}")
    elif section == "cumulative_filter":
        if key == "threshold":
            return thresholds["cumulative_filter"]["threshold"]
        else:
            raise KeyError(f"Unknown cumulative_filter key: {key}")
    elif section == "detection":
        if key == "min_value":
            return thresholds["detection"]["min_value"]
        else:
            raise KeyError(f"Unknown detection key: {key}")
    else:
        raise KeyError(f"Unknown threshold section: {section}")
