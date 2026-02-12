"""Tests for the pipeline blank_filter module."""

from __future__ import annotations

import polars as pl
import pytest

from scripts.pipeline.blank_filter import _filter_blanks_single_tissue, filter_blanks
from scripts.pipeline.loader import load_data
from scripts.pipeline.types import PipelineState


@pytest.fixture
def loaded_state() -> PipelineState:
    """Load data for testing."""
    return load_data()


def test_filter_blanks_requires_df_raw() -> None:
    """Test filter_blanks raises if df_raw is None."""
    state = PipelineState()
    with pytest.raises(ValueError, match="df_raw is None"):
        filter_blanks(state)


def test_filter_blanks_requires_config() -> None:
    """Test filter_blanks raises if config is None."""
    state = PipelineState()
    state.df_raw = pl.DataFrame({"Compound": ["A", "B"]})
    with pytest.raises(ValueError, match="config is None"):
        filter_blanks(state)


def test_filter_blanks_creates_filtered_df(loaded_state: PipelineState) -> None:
    """Test filter_blanks creates df_blank_filtered."""
    state = filter_blanks(loaded_state)

    assert state.df_blank_filtered is not None
    assert state.df_raw is not None
    assert state.df_blank_filtered.height > 0
    assert state.df_blank_filtered.height <= state.df_raw.height


def test_filter_blanks_populates_kept_blank(loaded_state: PipelineState) -> None:
    """Test filter_blanks populates kept_blank set."""
    state = filter_blanks(loaded_state)

    assert len(state.kept_blank) > 0
    assert state.df_blank_filtered is not None
    # All kept compounds should be in the filtered df
    filtered_compounds = set(state.df_blank_filtered["Compound"].to_list())
    assert state.kept_blank == filtered_compounds


def test_filter_blanks_populates_blank_stats(loaded_state: PipelineState) -> None:
    """Test filter_blanks populates blank_stats."""
    state = filter_blanks(loaded_state)

    assert state.blank_stats is not None
    assert "sample_only" in state.blank_stats
    assert "both_keep" in state.blank_stats
    assert "both_discard" in state.blank_stats
    assert "total_clean" in state.blank_stats


def test_filter_blanks_records_stage_result(loaded_state: PipelineState) -> None:
    """Test filter_blanks records a stage result."""
    state = filter_blanks(loaded_state)

    # Should have load + blank_filter results
    assert len(state.stage_results) == 2
    result = state.stage_results[1]
    assert result.stage_name == "blank_filter"
    assert result.success is True
    assert "blank_filter" in state.completed_stages


def test_filter_blanks_single_tissue_sample_only() -> None:
    """Test single tissue filter with sample-only peaks."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C"],
            "Sample1": [100.0, 200.0, 300.0],
            "Sample2": [110.0, 210.0, 310.0],
            "Blank1": [None, None, None],
        }
    )
    sample_cols = ["Sample1", "Sample2"]
    blank_cols = ["Blank1"]

    kept, stats = _filter_blanks_single_tissue(
        df, sample_cols, blank_cols, threshold=20.0, p_value_cutoff=0.05, fdr_correction=True
    )

    # All peaks should be kept since they're only in samples
    assert len(kept) == 3
    assert stats["sample_only"] == 3
    assert stats["both_keep"] == 0


def test_filter_blanks_single_tissue_blank_only() -> None:
    """Test single tissue filter with blank-only peaks."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B"],
            "Sample1": [None, None],
            "Blank1": [100.0, 200.0],
        }
    )
    sample_cols = ["Sample1"]
    blank_cols = ["Blank1"]

    kept, stats = _filter_blanks_single_tissue(
        df, sample_cols, blank_cols, threshold=20.0, p_value_cutoff=0.05, fdr_correction=True
    )

    # No peaks should be kept since they're only in blanks
    assert len(kept) == 0
    assert stats["blank_only"] == 2


def test_filter_blanks_single_tissue_high_fold_change() -> None:
    """Test single tissue filter with high fold change passes."""
    df = pl.DataFrame(
        {
            "Compound": ["A"],
            "Sample1": [1000.0],
            "Sample2": [1000.0],
            "Blank1": [10.0],
            "Blank2": [10.0],
        }
    )
    sample_cols = ["Sample1", "Sample2"]
    blank_cols = ["Blank1", "Blank2"]

    # 100x fold change should pass 20x threshold
    kept, stats = _filter_blanks_single_tissue(
        df, sample_cols, blank_cols, threshold=20.0, p_value_cutoff=0.05, fdr_correction=True
    )

    assert "A" in kept
    assert stats["fold_change_pass"] >= 1


def test_filter_blanks_single_tissue_low_fold_change() -> None:
    """Test single tissue filter with low fold change fails."""
    df = pl.DataFrame(
        {
            "Compound": ["A"],
            "Sample1": [100.0],
            "Sample2": [100.0],
            "Blank1": [50.0],
            "Blank2": [50.0],
        }
    )
    sample_cols = ["Sample1", "Sample2"]
    blank_cols = ["Blank1", "Blank2"]

    # 2x fold change should fail 20x threshold
    kept, stats = _filter_blanks_single_tissue(
        df, sample_cols, blank_cols, threshold=20.0, p_value_cutoff=0.05, fdr_correction=True
    )

    assert "A" not in kept
    assert stats["both_discard"] >= 1


def test_filter_blanks_single_tissue_no_statistical_test() -> None:
    """Test single tissue filter without statistical test."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B"],
            "Sample1": [2100.0, 100.0],
            "Blank1": [100.0, 100.0],
        }
    )
    sample_cols = ["Sample1"]
    blank_cols = ["Blank1"]

    kept, stats = _filter_blanks_single_tissue(
        df,
        sample_cols,
        blank_cols,
        threshold=20.0,
        p_value_cutoff=0.05,
        fdr_correction=True,
        use_statistical_test=False,
    )

    # A has 21x fold change (passes), B has 1x (fails)
    assert "A" in kept
    assert "B" not in kept
    assert stats["statistical_test_used"] is False


def test_filter_blanks_single_tissue_neither() -> None:
    """Test single tissue filter with peaks in neither samples nor blanks."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B"],
            "Sample1": [None, None],
            "Blank1": [None, None],
        }
    )
    sample_cols = ["Sample1"]
    blank_cols = ["Blank1"]

    kept, stats = _filter_blanks_single_tissue(
        df, sample_cols, blank_cols, threshold=20.0, p_value_cutoff=0.05, fdr_correction=True
    )

    assert len(kept) == 0
    assert stats["neither"] == 2


def test_filter_blanks_single_tissue_missing_columns() -> None:
    """Test single tissue filter handles missing columns gracefully."""
    df = pl.DataFrame(
        {
            "Compound": ["A"],
            "Sample1": [100.0],
        }
    )
    sample_cols = ["Sample1", "NonexistentSample"]
    blank_cols = ["NonexistentBlank"]

    kept, stats = _filter_blanks_single_tissue(
        df, sample_cols, blank_cols, threshold=20.0, p_value_cutoff=0.05, fdr_correction=True
    )

    # Should still process available columns
    assert "A" in kept
    assert stats["sample_only"] == 1


def test_filter_blanks_single_tissue_insufficient_data_for_ttest() -> None:
    """Test filter falls back to fold-change when not enough data for t-test."""
    df = pl.DataFrame(
        {
            "Compound": ["A"],
            "Sample1": [2100.0],  # Only 1 sample value
            "Blank1": [100.0],  # Only 1 blank value
        }
    )
    sample_cols = ["Sample1"]
    blank_cols = ["Blank1"]

    kept, stats = _filter_blanks_single_tissue(
        df, sample_cols, blank_cols, threshold=20.0, p_value_cutoff=0.05, fdr_correction=True
    )

    # Need 2+ values for t-test, should fall back to fold-change only
    # 2100/100 = 21x fold change > 20 threshold -> kept
    assert stats["insufficient_data"] == 1
    assert "A" in kept


def test_filter_blanks_single_tissue_no_fdr_correction() -> None:
    """Test filter without FDR correction."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B"],
            "Sample1": [1000.0, 100.0],
            "Sample2": [1000.0, 100.0],
            "Blank1": [10.0, 100.0],
            "Blank2": [10.0, 100.0],
        }
    )
    sample_cols = ["Sample1", "Sample2"]
    blank_cols = ["Blank1", "Blank2"]

    kept, stats = _filter_blanks_single_tissue(
        df, sample_cols, blank_cols, threshold=20.0, p_value_cutoff=0.05, fdr_correction=False
    )

    # A has 100x fold change, B has 1x fold change
    assert stats["fdr_corrected"] is False
    assert "A" in kept
