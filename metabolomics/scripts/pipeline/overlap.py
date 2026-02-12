"""Treatment overlap calculation stage for the metabolomics pipeline.

Calculates peak overlap between treatment groups for Venn diagram visualization.

Extracted from generate.py lines 292-300, 461-491.
"""

from __future__ import annotations

import polars as pl

from scripts.config import get_sample_columns
from scripts.pipeline.types import PipelineState, StageResult, VennData


def _get_peaks_in_group(df: pl.DataFrame, cols: list[str]) -> set[str]:
    """
    Get peaks that have non-zero signal in any column of the group.

    EXACT CODE from generate.py lines 292-300.

    Args:
        df: DataFrame with Compound column and sample columns.
        cols: List of sample column names.

    Returns:
        Set of compound names with signal in the group.
    """
    peaks = set()
    for col in cols:
        if col in df.columns:
            temp = df.select(["Compound", col]).drop_nulls()
            temp = temp.filter(pl.col(col) > 0)
            peaks.update(temp["Compound"].to_list())
    return peaks


def calculate_overlap(state: PipelineState) -> PipelineState:
    """
    Calculate treatment overlap for Venn diagrams.

    Extracted from generate.py lines 461-491.

    Uses df_80 (after 80% cumulative filter) for overlap calculations.

    Args:
        state: PipelineState with df_80 populated.

    Returns:
        Updated PipelineState with venn_data and treatment_peaks.
    """
    if state.df_80 is None:
        raise ValueError("df_80 is None - run cumulative_filter stage first")
    if state.config is None:
        raise ValueError("config is None - run load stage first")

    config = state.config
    df = state.df_80

    print(f"\n{'='*60}")
    print("TREATMENT OVERLAP")
    print(f"{'='*60}")
    print(f"Data source: df_80 ({df.height:,} peaks)")
    print(f"{'='*60}\n")

    venn_data: dict[str, VennData] = {}
    treatment_peaks: dict[str, dict[str, set[str]]] = {}

    for tissue in ["Leaf", "Root"]:
        tissue_lower = tissue.lower()

        drought_cols = get_sample_columns(config, tissue_lower, "drought")
        ambient_cols = get_sample_columns(config, tissue_lower, "ambient")
        watered_cols = get_sample_columns(config, tissue_lower, "watered")

        drought_peaks = _get_peaks_in_group(df, drought_cols)
        ambient_peaks = _get_peaks_in_group(df, ambient_cols)
        watered_peaks = _get_peaks_in_group(df, watered_cols)

        all_peaks = drought_peaks | ambient_peaks | watered_peaks

        venn_data[tissue] = VennData(
            drought=len(drought_peaks),
            ambient=len(ambient_peaks),
            watered=len(watered_peaks),
            all=len(all_peaks),
            # Unique to each treatment (not in the other two)
            drought_only=len(drought_peaks - ambient_peaks - watered_peaks),
            ambient_only=len(ambient_peaks - drought_peaks - watered_peaks),
            watered_only=len(watered_peaks - drought_peaks - ambient_peaks),
            # Shared between pairs (but not all three)
            drought_ambient=len((drought_peaks & ambient_peaks) - watered_peaks),
            drought_watered=len((drought_peaks & watered_peaks) - ambient_peaks),
            ambient_watered=len((ambient_peaks & watered_peaks) - drought_peaks),
            # Shared by all three
            all_three=len(drought_peaks & ambient_peaks & watered_peaks),
        )

        treatment_peaks[tissue] = {
            "drought_only": drought_peaks - ambient_peaks - watered_peaks,
            "ambient_only": ambient_peaks - drought_peaks - watered_peaks,
            "watered_only": watered_peaks - drought_peaks - ambient_peaks,
            "drought": drought_peaks,
            "ambient": ambient_peaks,
            "watered": watered_peaks,
        }

        print(f"{tissue}:")
        print(
            f"  Drought: {venn_data[tissue]['drought']:,} peaks ({venn_data[tissue]['drought_only']:,} unique)"
        )
        print(
            f"  Ambient: {venn_data[tissue]['ambient']:,} peaks ({venn_data[tissue]['ambient_only']:,} unique)"
        )
        print(
            f"  Watered: {venn_data[tissue]['watered']:,} peaks ({venn_data[tissue]['watered_only']:,} unique)"
        )
        print(f"  All three: {venn_data[tissue]['all_three']:,} peaks")

    # Update state
    state.venn_data = venn_data
    state.treatment_peaks = treatment_peaks

    # Record stage completion
    state.add_stage_result(
        StageResult(
            stage_name="overlap",
            success=True,
            message=f"Calculated overlap for {df.height:,} peaks",
            data={
                "data_source": "df_80",
                "peak_count": df.height,
            },
        )
    )

    return state
