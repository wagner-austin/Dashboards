"""Diversity calculation stage for the metabolomics pipeline.

Calculates chemical richness (peak counts) and Shannon diversity index.

IMPORTANT: Uses df_blank_filtered (14,307 peaks), NOT df_80 (1,626 peaks).
Diversity metrics should capture full metabolome complexity before the
80% cumulative filter removes low-abundance peaks.

Extracted from generate.py lines 493-598.

References:
    Shannon diversity: Vinaixa et al. 2012, Metabolites
    https://pmc.ncbi.nlm.nih.gov/articles/PMC3901240/
"""

from __future__ import annotations

import math

import polars as pl

from scripts.config import get_sample_columns, get_threshold
from scripts.pipeline.types import (
    DiversityResult,
    PipelineState,
    StageResult,
    TreatmentDiversity,
)


def _calculate_richness(
    df: pl.DataFrame,
    sample_cols: list[str],
    detection_threshold: float,
) -> list[int]:
    """
    Count detected peaks per sample.

    EXACT CODE from generate.py lines 506-517.

    Args:
        df: DataFrame with sample columns.
        sample_cols: List of sample column names.
        detection_threshold: Values > this are considered detected.

    Returns:
        List of peak counts, one per sample.
    """
    richness = []
    for col in sample_cols:
        if col not in df.columns:
            continue
        # Count non-null, non-zero values
        count = df.filter((pl.col(col).is_not_null()) & (pl.col(col) > detection_threshold)).height
        richness.append(count)
    return richness


def _calculate_shannon(
    df: pl.DataFrame,
    sample_col: str,
    detection_threshold: float,
) -> float:
    """
    Calculate Shannon diversity index for a sample.

    EXACT CODE from generate.py lines 562-578.

    Shannon H = -Σ(p × ln(p)) where p = relative abundance

    Args:
        df: DataFrame with sample column.
        sample_col: Sample column name.
        detection_threshold: Values > this are considered detected.

    Returns:
        Shannon diversity index H.
    """
    if sample_col not in df.columns:
        return 0.0

    vals = df.select(sample_col).drop_nulls().to_series().to_list()
    vals = [v for v in vals if v > detection_threshold]

    if not vals:
        return 0.0

    total = sum(vals)
    if total == 0:
        return 0.0

    h = 0.0
    for v in vals:
        p = v / total
        if p > 0:
            h -= p * math.log(p)

    return h


def _calc_se(values: list[float]) -> float:
    """
    Calculate standard error = stdev / sqrt(n).

    EXACT CODE from generate.py lines 519-525.
    """
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance / len(values))


def calculate_diversity(state: PipelineState) -> PipelineState:
    """
    Calculate chemical richness and Shannon diversity.

    Extracted from generate.py lines 493-598.

    IMPORTANT: This uses df_blank_filtered, NOT df_80.
    Diversity should capture full metabolome complexity.

    Args:
        state: PipelineState with df_blank_filtered populated.

    Returns:
        Updated PipelineState with chemical_richness and shannon_diversity.
    """
    if state.df_blank_filtered is None:
        raise ValueError("df_blank_filtered is None - run blank_filter stage first")
    if state.config is None:
        raise ValueError("config is None - run load stage first")

    config = state.config
    df = state.df_blank_filtered  # NOT df_80!

    # Get detection threshold from config
    detection_threshold = get_threshold(config, "detection", "min_value")

    print(f"\n{'='*60}")
    print("DIVERSITY CALCULATIONS")
    print(f"{'='*60}")
    print(f"Data source: df_blank_filtered ({df.height:,} peaks)")
    print(f"Detection threshold: {detection_threshold}")
    print(f"Reference: {config['references']['shannon_diversity']['url']}")
    print(f"{'='*60}\n")

    total_peaks = df.height
    chemical_richness: dict[str, TreatmentDiversity] = {}
    shannon_diversity: dict[str, TreatmentDiversity] = {}

    for tissue in ["Leaf", "Root"]:
        tissue_lower = tissue.lower()

        # Build results for each treatment
        richness_results: dict[str, DiversityResult] = {}
        shannon_results: dict[str, DiversityResult] = {}

        for treatment in ["Drought", "Ambient", "Watered"]:
            treatment_lower = treatment.lower()
            cols = get_sample_columns(config, tissue_lower, treatment_lower)

            # Chemical richness
            richness_vals_int = _calculate_richness(df, cols, detection_threshold)
            richness_vals = [float(v) for v in richness_vals_int]
            if richness_vals:
                mean_val = sum(richness_vals) / len(richness_vals)
                se_val = _calc_se(richness_vals)
            else:
                mean_val, se_val = 0.0, 0.0

            richness_results[treatment] = DiversityResult(
                mean=mean_val,
                se=se_val,
                n=len(richness_vals),
                values=richness_vals,
            )
            print(
                f"  {tissue} {treatment} richness: {mean_val:.1f} ± {se_val:.1f} peaks (n={len(richness_vals)}) / {total_peaks:,}"
            )

            # Shannon diversity
            h_vals = [
                _calculate_shannon(df, col, detection_threshold)
                for col in cols
                if col in df.columns
            ]
            if h_vals:
                h_mean = sum(h_vals) / len(h_vals)
                h_se = _calc_se(h_vals)
            else:
                h_mean, h_se = 0.0, 0.0

            shannon_results[treatment] = DiversityResult(
                mean=h_mean,
                se=h_se,
                n=len(h_vals),
                values=h_vals,
            )
            print(f"  {tissue} {treatment} Shannon H: {h_mean:.3f} ± {h_se:.3f} (n={len(h_vals)})")

        # Build TreatmentDiversity TypedDicts
        chemical_richness[tissue] = TreatmentDiversity(
            Drought=richness_results["Drought"],
            Ambient=richness_results["Ambient"],
            Watered=richness_results["Watered"],
        )
        shannon_diversity[tissue] = TreatmentDiversity(
            Drought=shannon_results["Drought"],
            Ambient=shannon_results["Ambient"],
            Watered=shannon_results["Watered"],
        )

    # Update state
    state.chemical_richness = chemical_richness
    state.shannon_diversity = shannon_diversity

    # Record stage completion
    state.add_stage_result(
        StageResult(
            stage_name="diversity",
            success=True,
            message=f"Calculated diversity metrics from {df.height:,} peaks",
            data={
                "data_source": "df_blank_filtered",
                "peak_count": df.height,
                "detection_threshold": detection_threshold,
            },
        )
    )

    return state
