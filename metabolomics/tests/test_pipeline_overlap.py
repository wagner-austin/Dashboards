"""Tests for the pipeline overlap module."""

from __future__ import annotations

import polars as pl
import pytest

from scripts.pipeline.blank_filter import filter_blanks
from scripts.pipeline.cumulative_filter import filter_cumulative
from scripts.pipeline.loader import load_data
from scripts.pipeline.overlap import _get_peaks_in_group, calculate_overlap
from scripts.pipeline.types import PipelineState


@pytest.fixture
def cumulative_filtered_state() -> PipelineState:
    """Load, blank-filter, and cumulative-filter data for testing."""
    state = load_data()
    state = filter_blanks(state)
    return filter_cumulative(state)


def test_calculate_overlap_requires_df_80() -> None:
    """Test calculate_overlap raises if df_80 is None."""
    state = PipelineState()
    with pytest.raises(ValueError, match="df_80 is None"):
        calculate_overlap(state)


def test_calculate_overlap_requires_config() -> None:
    """Test calculate_overlap raises if config is None."""
    state = PipelineState()
    state.df_80 = pl.DataFrame({"Compound": ["A", "B"]})
    with pytest.raises(ValueError, match="config is None"):
        calculate_overlap(state)


def test_calculate_overlap_populates_venn_data(
    cumulative_filtered_state: PipelineState,
) -> None:
    """Test calculate_overlap populates venn_data."""
    state = calculate_overlap(cumulative_filtered_state)

    assert state.venn_data is not None
    assert "Leaf" in state.venn_data
    assert "Root" in state.venn_data

    # Check VennData structure
    for tissue in ["Leaf", "Root"]:
        venn = state.venn_data[tissue]
        assert "drought" in venn
        assert "ambient" in venn
        assert "watered" in venn
        assert "all" in venn
        assert "drought_only" in venn
        assert "ambient_only" in venn
        assert "watered_only" in venn
        assert "all_three" in venn


def test_calculate_overlap_populates_treatment_peaks(
    cumulative_filtered_state: PipelineState,
) -> None:
    """Test calculate_overlap populates treatment_peaks."""
    state = calculate_overlap(cumulative_filtered_state)

    assert state.treatment_peaks is not None
    assert "Leaf" in state.treatment_peaks
    assert "Root" in state.treatment_peaks

    # Check treatment_peaks structure
    for tissue in ["Leaf", "Root"]:
        peaks = state.treatment_peaks[tissue]
        assert "drought" in peaks
        assert "ambient" in peaks
        assert "watered" in peaks
        assert "drought_only" in peaks
        assert "ambient_only" in peaks
        assert "watered_only" in peaks
        # Values should be sets
        assert isinstance(peaks["drought"], set)


def test_calculate_overlap_records_stage_result(
    cumulative_filtered_state: PipelineState,
) -> None:
    """Test calculate_overlap records a stage result."""
    state = calculate_overlap(cumulative_filtered_state)

    result = state.stage_results[-1]
    assert result.stage_name == "overlap"
    assert result.success is True
    assert "overlap" in state.completed_stages


def test_calculate_overlap_venn_counts_are_consistent(
    cumulative_filtered_state: PipelineState,
) -> None:
    """Test Venn diagram counts are mathematically consistent."""
    state = calculate_overlap(cumulative_filtered_state)

    for tissue in ["Leaf", "Root"]:
        venn = state.venn_data[tissue]

        # Sum of exclusive regions should equal 'all'
        exclusive_sum = (
            venn["drought_only"]
            + venn["ambient_only"]
            + venn["watered_only"]
            + venn["drought_ambient"]
            + venn["drought_watered"]
            + venn["ambient_watered"]
            + venn["all_three"]
        )
        assert exclusive_sum == venn["all"]


def test_get_peaks_in_group_basic() -> None:
    """Test basic peak detection in group."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C", "D"],
            "Col1": [100.0, 0.0, None, 50.0],
            "Col2": [None, 200.0, 300.0, 0.0],
        }
    )

    peaks = _get_peaks_in_group(df, ["Col1", "Col2"])

    # A: Col1=100 (yes), B: Col2=200 (yes), C: Col2=300 (yes), D: Col1=50 (yes)
    assert peaks == {"A", "B", "C", "D"}


def test_get_peaks_in_group_with_zeros() -> None:
    """Test peaks exclude zeros."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C"],
            "Col1": [100.0, 0.0, 0.0],
        }
    )

    peaks = _get_peaks_in_group(df, ["Col1"])

    # Only A has non-zero value
    assert peaks == {"A"}


def test_get_peaks_in_group_empty() -> None:
    """Test peaks with all nulls/zeros."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B"],
            "Col1": [None, 0.0],
        }
    )

    peaks = _get_peaks_in_group(df, ["Col1"])

    assert peaks == set()


def test_get_peaks_in_group_missing_column() -> None:
    """Test peaks skips missing columns."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B"],
            "Col1": [100.0, 200.0],
        }
    )

    peaks = _get_peaks_in_group(df, ["Col1", "NonexistentColumn"])

    # Should only use Col1
    assert peaks == {"A", "B"}


def test_get_peaks_in_group_union_across_columns() -> None:
    """Test peaks are union across columns."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C"],
            "Col1": [100.0, None, None],
            "Col2": [None, 200.0, None],
            "Col3": [None, None, 300.0],
        }
    )

    peaks = _get_peaks_in_group(df, ["Col1", "Col2", "Col3"])

    # Each compound detected in exactly one column
    assert peaks == {"A", "B", "C"}
