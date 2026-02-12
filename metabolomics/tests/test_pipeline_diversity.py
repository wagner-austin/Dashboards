"""Tests for the pipeline diversity module."""

from __future__ import annotations

import math

import polars as pl
import pytest

from scripts.pipeline.blank_filter import filter_blanks
from scripts.pipeline.diversity import (
    _calc_se,
    _calculate_richness,
    _calculate_shannon,
    calculate_diversity,
)
from scripts.pipeline.loader import load_data
from scripts.pipeline.types import PipelineState


@pytest.fixture
def blank_filtered_state() -> PipelineState:
    """Load and blank-filter data for testing."""
    state = load_data()
    return filter_blanks(state)


def test_calculate_diversity_requires_df_blank_filtered() -> None:
    """Test calculate_diversity raises if df_blank_filtered is None."""
    state = PipelineState()
    with pytest.raises(ValueError, match="df_blank_filtered is None"):
        calculate_diversity(state)


def test_calculate_diversity_requires_config() -> None:
    """Test calculate_diversity raises if config is None."""
    state = PipelineState()
    state.df_blank_filtered = pl.DataFrame({"Compound": ["A", "B"]})
    with pytest.raises(ValueError, match="config is None"):
        calculate_diversity(state)


def test_calculate_diversity_populates_chemical_richness(
    blank_filtered_state: PipelineState,
) -> None:
    """Test calculate_diversity populates chemical_richness."""
    state = calculate_diversity(blank_filtered_state)

    assert state.chemical_richness is not None
    assert "Leaf" in state.chemical_richness
    assert "Root" in state.chemical_richness

    # Each tissue should have all three treatments
    for tissue in ["Leaf", "Root"]:
        assert "Drought" in state.chemical_richness[tissue]
        assert "Ambient" in state.chemical_richness[tissue]
        assert "Watered" in state.chemical_richness[tissue]


def test_calculate_diversity_populates_shannon_diversity(
    blank_filtered_state: PipelineState,
) -> None:
    """Test calculate_diversity populates shannon_diversity."""
    state = calculate_diversity(blank_filtered_state)

    assert state.shannon_diversity is not None
    assert "Leaf" in state.shannon_diversity
    assert "Root" in state.shannon_diversity

    # Shannon values should be positive
    for tissue in ["Leaf", "Root"]:
        tissue_data = state.shannon_diversity[tissue]
        assert tissue_data["Drought"]["mean"] >= 0
        assert tissue_data["Ambient"]["mean"] >= 0
        assert tissue_data["Watered"]["mean"] >= 0


def test_calculate_diversity_records_stage_result(
    blank_filtered_state: PipelineState,
) -> None:
    """Test calculate_diversity records a stage result."""
    state = calculate_diversity(blank_filtered_state)

    result = state.stage_results[-1]
    assert result.stage_name == "diversity"
    assert result.success is True
    assert "diversity" in state.completed_stages


def test_calculate_richness_basic() -> None:
    """Test basic richness calculation."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C", "D"],
            "Sample1": [100.0, 200.0, None, 0.0],
            "Sample2": [50.0, None, 300.0, 400.0],
        }
    )

    richness = _calculate_richness(df, ["Sample1", "Sample2"], 0.0)

    # Sample1: A=100, B=200 (2 detected, C is null, D is 0)
    # Sample2: A=50, C=300, D=400 (3 detected)
    assert richness == [2, 3]


def test_calculate_richness_with_threshold() -> None:
    """Test richness calculation with detection threshold."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C"],
            "Sample1": [100.0, 5.0, 200.0],  # B is below threshold
        }
    )

    richness = _calculate_richness(df, ["Sample1"], 10.0)

    # Only A=100 and C=200 are above threshold 10
    assert richness == [2]


def test_calculate_richness_missing_column() -> None:
    """Test richness skips missing columns."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B"],
            "Sample1": [100.0, 200.0],
        }
    )

    richness = _calculate_richness(df, ["Sample1", "NonexistentColumn"], 0.0)

    # Should only count Sample1
    assert richness == [2]


def test_calculate_richness_empty() -> None:
    """Test richness with all nulls."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B"],
            "Sample1": [None, None],
        }
    )

    richness = _calculate_richness(df, ["Sample1"], 0.0)

    assert richness == [0]


def test_calculate_shannon_basic() -> None:
    """Test basic Shannon diversity calculation."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C"],
            "Sample": [100.0, 100.0, 100.0],  # Equal abundances
        }
    )

    h = _calculate_shannon(df, "Sample", 0.0)

    # For equal abundances, H = ln(n) = ln(3)
    assert abs(h - math.log(3)) < 0.01


def test_calculate_shannon_single_species() -> None:
    """Test Shannon diversity with single species."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C"],
            "Sample": [1000.0, 0.0, 0.0],
        }
    )

    h = _calculate_shannon(df, "Sample", 0.0)

    # Single species dominance -> H approaches 0
    # But with zeros, only A contributes, so p=1, H = -1*ln(1) = 0
    assert h == 0.0


def test_calculate_shannon_missing_column() -> None:
    """Test Shannon returns 0 for missing column."""
    df = pl.DataFrame(
        {
            "Compound": ["A"],
            "Sample": [100.0],
        }
    )

    h = _calculate_shannon(df, "NonexistentColumn", 0.0)

    assert h == 0.0


def test_calculate_shannon_empty() -> None:
    """Test Shannon returns 0 for empty data."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B"],
            "Sample": [None, None],
        }
    )

    h = _calculate_shannon(df, "Sample", 0.0)

    assert h == 0.0


def test_calculate_shannon_with_threshold() -> None:
    """Test Shannon with detection threshold."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C"],
            "Sample": [100.0, 5.0, 100.0],  # B below threshold
        }
    )

    h = _calculate_shannon(df, "Sample", 10.0)

    # Only A and C count, equal abundances -> H = ln(2)
    assert abs(h - math.log(2)) < 0.01


def test_calc_se_single_value() -> None:
    """Test SE calculation with single value."""
    se = _calc_se([5.0])

    assert se == 0.0


def test_calc_se_empty() -> None:
    """Test SE calculation with empty list."""
    se = _calc_se([])

    assert se == 0.0


def test_calc_se_multiple_values() -> None:
    """Test SE calculation with multiple values."""
    values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    se = _calc_se(values)

    # SE = stdev / sqrt(n)
    # Mean = 5, variance = sum((x-5)^2)/7, stdev = sqrt(variance)
    assert se > 0


def test_calc_se_identical_values() -> None:
    """Test SE calculation with identical values."""
    se = _calc_se([5.0, 5.0, 5.0, 5.0])

    # No variance -> SE = 0
    assert se == 0.0


def test_calculate_shannon_zero_sum() -> None:
    """Test Shannon returns 0 when sum of values is zero."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B"],
            # Note: zeros are filtered out by threshold > 0, so we need threshold=0
            # and values that pass threshold but sum to 0 - which is impossible
            # if threshold is 0 and all values are 0. Let's use empty after filter.
            "Sample": [0.0, 0.0],  # These will be filtered out by > threshold
        }
    )

    # With threshold 0, all zeros are excluded (val > 0 check)
    h = _calculate_shannon(df, "Sample", 0.0)
    assert h == 0.0


def test_calculate_shannon_very_small_values() -> None:
    """Test Shannon with very small positive values."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C"],
            "Sample": [0.001, 0.001, 0.001],
        }
    )

    h = _calculate_shannon(df, "Sample", 0.0)

    # Equal small abundances -> H = ln(3)
    import math

    assert abs(h - math.log(3)) < 0.01


def test_calculate_richness_all_zeros() -> None:
    """Test richness with all zero values."""
    df = pl.DataFrame(
        {
            "Compound": ["A", "B", "C"],
            "Sample1": [0.0, 0.0, 0.0],
        }
    )

    richness = _calculate_richness(df, ["Sample1"], 0.0)

    # All zeros, nothing detected (filter is > threshold)
    assert richness == [0]
