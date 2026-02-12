"""Tests for the pipeline loader module."""

from __future__ import annotations

from pathlib import Path

from scripts.pipeline.loader import load_data, load_formulas
from scripts.pipeline.types import PipelineState


def test_load_data_creates_state() -> None:
    """Test load_data creates a populated PipelineState."""
    state = load_data()

    assert state.config is not None
    assert state.df_raw is not None
    assert state.df_raw.height > 0
    assert "Compound" in state.df_raw.columns
    assert "load" in state.completed_stages


def test_load_data_with_existing_state() -> None:
    """Test load_data works with an existing PipelineState."""
    existing_state = PipelineState()
    state = load_data(state=existing_state)

    assert state is existing_state
    assert state.config is not None
    assert state.df_raw is not None


def test_load_data_records_stage_result() -> None:
    """Test load_data records a stage result."""
    state = load_data()

    assert len(state.stage_results) == 1
    result = state.stage_results[0]
    assert result.stage_name == "load"
    assert result.success is True
    assert state.df_raw is not None
    assert result.output_count == state.df_raw.height


def test_load_formulas_missing_file() -> None:
    """Test load_formulas returns empty dict for missing file."""
    result = load_formulas(Path("/nonexistent/path/formulas.xlsx"))
    assert result == {}


def test_load_data_uses_config_values() -> None:
    """Test load_data reads data using config values."""
    state = load_data()

    assert state.config is not None
    # Verify config was used correctly
    assert state.config["input"]["file"] == "Emily_Data_Pruned_Labeled.xlsx"
    assert state.config["input"]["sheet"] == "Normalized"


def test_load_data_formula_lookup_populated() -> None:
    """Test load_data populates formula_lookup from formula file."""
    state = load_data()

    # The project has a formula file with formulas
    assert len(state.formula_lookup) > 0
    # Formula lookup should map compound names to formulas
    for compound, formula in list(state.formula_lookup.items())[:5]:
        assert isinstance(compound, str)
        assert isinstance(formula, str)
