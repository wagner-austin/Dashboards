"""Tests for the pipeline cumulative_filter module."""

from __future__ import annotations

import polars as pl
import pytest

from scripts.pipeline.blank_filter import filter_blanks
from scripts.pipeline.cumulative_filter import (
    _filter_cumulative_single_sample,
    filter_cumulative,
)
from scripts.pipeline.loader import load_data
from scripts.pipeline.types import PipelineState


@pytest.fixture
def blank_filtered_state() -> PipelineState:
    """Load and blank-filter data for testing."""
    state = load_data()
    return filter_blanks(state)


def test_filter_cumulative_requires_df_blank_filtered() -> None:
    """Test filter_cumulative raises if df_blank_filtered is None."""
    state = PipelineState()
    with pytest.raises(ValueError, match="df_blank_filtered is None"):
        filter_cumulative(state)


def test_filter_cumulative_requires_config() -> None:
    """Test filter_cumulative raises if config is None."""
    state = PipelineState()
    state.df_blank_filtered = pl.DataFrame({"Compound": ["A", "B"]})
    with pytest.raises(ValueError, match="config is None"):
        filter_cumulative(state)


def test_filter_cumulative_creates_df_80(blank_filtered_state: PipelineState) -> None:
    """Test filter_cumulative creates df_80."""
    state = filter_cumulative(blank_filtered_state)

    assert state.df_80 is not None
    assert state.df_blank_filtered is not None
    assert state.df_80.height > 0
    assert state.df_80.height <= state.df_blank_filtered.height


def test_filter_cumulative_populates_kept_80(blank_filtered_state: PipelineState) -> None:
    """Test filter_cumulative populates kept_80 set."""
    state = filter_cumulative(blank_filtered_state)

    assert len(state.kept_80) > 0
    assert state.df_80 is not None
    # All kept compounds should be in the filtered df
    filtered_compounds = set(state.df_80["Compound"].to_list())
    assert state.kept_80 == filtered_compounds


def test_filter_cumulative_populates_sample_data_80(
    blank_filtered_state: PipelineState,
) -> None:
    """Test filter_cumulative populates sample_data_80."""
    state = filter_cumulative(blank_filtered_state)

    assert len(state.sample_data_80) > 0
    # Each entry should be (col_name, tissue, count, pct)
    for entry in state.sample_data_80:
        assert len(entry) == 4
        col, tissue, count, pct = entry
        assert isinstance(col, str)
        assert tissue in ["Leaf", "Root"]
        assert isinstance(count, int)
        assert isinstance(pct, float)


def test_filter_cumulative_records_stage_result(
    blank_filtered_state: PipelineState,
) -> None:
    """Test filter_cumulative records a stage result."""
    state = filter_cumulative(blank_filtered_state)

    # Should have load + blank_filter + cumulative_filter results
    result = state.stage_results[-1]
    assert result.stage_name == "cumulative_filter"
    assert result.success is True
    assert "cumulative_filter" in state.completed_stages


def test_filter_cumulative_single_sample_basic() -> None:
    """Test single sample cumulative filter basic functionality."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C", "D"],
            "Sample": [100.0, 50.0, 30.0, 20.0],
        }
    )

    kept, count, smallest_pct = _filter_cumulative_single_sample(df, "Sample", 0.80)

    # Total = 200, need 160 for 80%
    # A=100 (50%), A+B=150 (75%), A+B+C=180 (90%) -> need A, B, C
    assert len(kept) == 3
    assert "A" in kept
    assert "B" in kept
    assert "C" in kept
    assert "D" not in kept
    assert count == 3


def test_filter_cumulative_single_sample_empty_column() -> None:
    """Test single sample filter with all nulls."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B"],
            "Sample": [None, None],
        }
    )

    kept, count, smallest_pct = _filter_cumulative_single_sample(df, "Sample", 0.80)

    assert len(kept) == 0
    assert count == 0
    assert smallest_pct == 0.0


def test_filter_cumulative_single_sample_zero_total() -> None:
    """Test single sample filter when total is zero."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B"],
            "Sample": [0.0, 0.0],
        }
    )

    # Note: drop_nulls doesn't drop zeros, but zeros are filtered in loop
    kept, count, smallest_pct = _filter_cumulative_single_sample(df, "Sample", 0.80)

    # Behavior depends on implementation - zeros should be dropped
    assert smallest_pct == 0.0


def test_filter_cumulative_single_sample_single_peak() -> None:
    """Test single sample filter with just one peak."""
    df = pl.DataFrame(
        {
            "Compound": ["A"],
            "Sample": [100.0],
        }
    )

    kept, count, smallest_pct = _filter_cumulative_single_sample(df, "Sample", 0.80)

    # Single peak, it's 100% of signal, so it passes any threshold
    assert len(kept) == 1
    assert "A" in kept
    assert count == 1


def test_filter_cumulative_single_sample_100_threshold() -> None:
    """Test single sample filter with 100% threshold keeps all."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C"],
            "Sample": [100.0, 50.0, 10.0],
        }
    )

    kept, count, smallest_pct = _filter_cumulative_single_sample(df, "Sample", 1.0)

    assert len(kept) == 3
    assert count == 3


def test_filter_cumulative_single_sample_very_low_threshold() -> None:
    """Test single sample filter with very low threshold."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C"],
            "Sample": [900.0, 50.0, 50.0],  # A is 90% of total
        }
    )

    kept, count, smallest_pct = _filter_cumulative_single_sample(df, "Sample", 0.50)

    # Only need 50%, A alone is 90%
    assert len(kept) == 1
    assert "A" in kept
