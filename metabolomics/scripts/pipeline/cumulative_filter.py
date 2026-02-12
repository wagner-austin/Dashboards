"""Cumulative signal filtering stage for the metabolomics pipeline.

Keeps only peaks that contribute to the top N% of signal in any sample.
This reduces noise by focusing on the most abundant compounds.

Extracted from generate.py lines 62-84, 432-451.
"""

from __future__ import annotations

import polars as pl

from scripts.config import get_all_sample_columns, get_threshold
from scripts.pipeline.types import PipelineState, StageResult


def _filter_cumulative_single_sample(
    df: pl.DataFrame,
    col: str,
    threshold: float,
) -> tuple[set[str], int, float]:
    """
    Filter to cumulative threshold for a single sample.

    EXACT CODE from generate.py lines 62-84.

    Args:
        df: DataFrame with Compound column and sample column.
        col: Sample column name.
        threshold: Cumulative threshold (e.g., 0.80 for 80%).

    Returns:
        Tuple of (set of kept compound names, count, smallest_pct_kept).
    """
    temp = df.select(["Compound", col]).drop_nulls()
    if temp.height == 0:
        return set(), 0, 0.0

    temp = temp.sort(col, descending=True)
    compounds = temp["Compound"].to_list()
    areas = temp[col].to_list()
    total = sum(areas)

    if total == 0:
        return set(), 0, 0.0

    kept: set[str] = set()
    cumsum = 0.0
    last_pct = 0.0

    for compound, area in zip(compounds, areas, strict=True):
        cumsum += area
        kept.add(compound)
        last_pct = area / total
        if cumsum / total >= threshold:
            break

    return kept, len(kept), last_pct


def filter_cumulative(state: PipelineState) -> PipelineState:
    """
    Apply cumulative signal filtering to blank-filtered data.

    Extracted from generate.py lines 432-451.

    This stage:
    1. For each sample, keeps peaks contributing to top N% of signal
    2. Takes union across all samples (peak kept if it's in top N% for ANY sample)

    DATA SOURCE: df_blank_filtered (not df_raw)

    Args:
        state: PipelineState with df_blank_filtered populated.

    Returns:
        Updated PipelineState with df_80, kept_80, sample_data_80.
    """
    if state.df_blank_filtered is None:
        raise ValueError("df_blank_filtered is None - run blank_filter stage first")
    if state.config is None:
        raise ValueError("config is None - run load stage first")

    config = state.config
    df = state.df_blank_filtered

    # Get threshold from config
    threshold = get_threshold(config, "cumulative_filter", "threshold")

    print(f"\n{'='*60}")
    print("CUMULATIVE FILTERING")
    print(f"{'='*60}")
    print(f"Threshold: {threshold*100:.0f}% of signal per sample")
    print(f"Input: {df.height:,} peaks (after blank filtering)")
    print(f"{'='*60}\n")

    # Get all sample columns
    sample_cols = get_all_sample_columns(config)

    kept_80: set[str] = set()
    sample_data_80: list[tuple[str, str, int, float]] = []

    for col in sample_cols:
        if col not in df.columns:
            continue

        k80, n80, pct80 = _filter_cumulative_single_sample(df, col, threshold)
        kept_80.update(k80)

        # Determine tissue from column name
        # Format: "BL - Drought" -> Leaf (second char is L)
        # Format: "AR - Drought" -> Root (second char is R)
        tissue = "Leaf" if len(col) > 1 and col[1] == "L" else "Root"
        sample_data_80.append((col, tissue, n80, pct80 * 100))

    print("Sample filtering results:")
    for col, _, n80, pct80 in sample_data_80[:5]:
        print(f"  {col}: {n80:,} peaks ({pct80:.2f}% smallest)")
    if len(sample_data_80) > 5:
        print(f"  ... and {len(sample_data_80) - 5} more samples")

    print(f"\nUnion: {len(kept_80):,} unique peaks after {threshold*100:.0f}% filtering")

    # Create filtered DataFrame
    extra_cols = [c for c in ["m/z", "Retention time (min)"] if c in df.columns]
    available_cols = [c for c in sample_cols if c in df.columns]
    df_80 = df.filter(pl.col("Compound").is_in(list(kept_80))).select(
        ["Compound"] + extra_cols + available_cols
    )

    # Update state
    state.df_80 = df_80
    state.kept_80 = kept_80
    state.sample_data_80 = sample_data_80

    # Record stage completion
    state.add_stage_result(
        StageResult(
            stage_name="cumulative_filter",
            success=True,
            message=f"Kept {len(kept_80):,} peaks after {threshold*100:.0f}% filtering",
            data={
                "input_peaks": df.height,
                "output_peaks": len(kept_80),
                "threshold": threshold,
                "samples_processed": len(sample_data_80),
            },
        )
    )

    return state
