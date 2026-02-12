"""Blank subtraction stage for the metabolomics pipeline.

Removes contamination peaks by comparing sample intensities to blank intensities.
Uses fold-change threshold (20x) and statistical validation (Welch's t-test with FDR).

Extracted from generate.py lines 100-289, 400-430.

Reference:
    pmp/Bioconductor: https://bioconductor.org/packages/release/bioc/html/pmp.html
    Jankevics A, Lloyd GR, Weber RJM. pmp: Peak Matrix Processing.
"""

from __future__ import annotations

import polars as pl

from scripts.config import get_blank_columns, get_sample_columns
from scripts.pipeline.types import (
    BlankFilterStats,
    PipelineState,
    StageResult,
    create_blank_filter_stats,
)


def _filter_blanks_single_tissue(
    df: pl.DataFrame,
    sample_cols: list[str],
    blank_cols: list[str],
    threshold: float,
    p_value_cutoff: float,
    fdr_correction: bool,
    use_statistical_test: bool = True,
) -> tuple[set[str], BlankFilterStats]:
    """
    Filter peaks for a single tissue based on blank subtraction.

    EXACT CODE from generate.py lines 100-289.

    Publication-quality filtering requires BOTH:
    1. Fold-change >= threshold (default 20x, per pmp/Bioconductor)
    2. Statistical test p-value < cutoff (default 0.05, FDR-corrected)

    Args:
        df: DataFrame with Compound column and sample/blank columns.
        sample_cols: List of sample column names.
        blank_cols: List of blank column names.
        threshold: Fold-change threshold (sample_mean / blank_mean).
        p_value_cutoff: P-value threshold for statistical test.
        fdr_correction: Whether to apply Benjamini-Hochberg FDR correction.
        use_statistical_test: Whether to use t-test (True) or fold-change only.

    Returns:
        Tuple of (set of kept compound names, statistics dict).
    """
    from scipy import stats as scipy_stats

    compounds = df["Compound"].to_list()
    kept: set[str] = set()
    filter_stats: BlankFilterStats = {
        "sample_only": 0,
        "both_keep": 0,
        "both_discard": 0,
        "blank_only": 0,
        "neither": 0,
        "fold_change_pass": 0,
        "fold_change_fail": 0,
        "stat_test_pass": 0,
        "stat_test_fail": 0,
        "insufficient_data": 0,
        "total_clean": 0,
        "statistical_test_used": use_statistical_test,
        "fdr_corrected": fdr_correction,
        "p_value_cutoff": p_value_cutoff,
        "fold_change_threshold": threshold,
    }

    # For statistical testing, collect all p-values first for FDR correction
    peak_data = []  # List of (compound, sample_vals, blank_vals, fold_change)

    for i, compound in enumerate(compounds):
        # Get sample values
        sample_vals = []
        for col in sample_cols:
            if col in df.columns:
                val = df[col][i]
                if val is not None:
                    try:
                        v = float(val)
                        if v > 0:
                            sample_vals.append(v)
                    except (ValueError, TypeError):
                        pass

        # Get blank values
        blank_vals = []
        for col in blank_cols:
            if col in df.columns:
                val = df[col][i]
                if val is not None:
                    try:
                        v = float(val)
                        if v > 0:
                            blank_vals.append(v)
                    except (ValueError, TypeError):
                        pass

        has_sample = len(sample_vals) > 0
        has_blank = len(blank_vals) > 0

        if has_sample and not has_blank:
            # Peak only in samples - keep it (no blank contamination possible)
            kept.add(compound)
            filter_stats["sample_only"] += 1
        elif has_sample and has_blank:
            sample_avg = sum(sample_vals) / len(sample_vals)
            blank_avg = sum(blank_vals) / len(blank_vals)
            fold_change = sample_avg / blank_avg if blank_avg > 0 else float("inf")
            peak_data.append((compound, sample_vals, blank_vals, fold_change))
        elif has_blank and not has_sample:
            filter_stats["blank_only"] += 1
        else:
            filter_stats["neither"] += 1

    # Process peaks found in both samples and blanks
    if use_statistical_test and peak_data:
        # Calculate p-values for all peaks
        p_values = []
        valid_peaks = []  # Peaks with enough data for t-test

        for compound, sample_vals, blank_vals, fold_change in peak_data:
            # Need at least 2 values in each group for t-test
            if len(sample_vals) >= 2 and len(blank_vals) >= 2:
                # Welch's t-test (does not assume equal variance)
                try:
                    t_stat, p_val = scipy_stats.ttest_ind(sample_vals, blank_vals, equal_var=False)
                    # One-sided test: we want sample > blank
                    if t_stat > 0:
                        p_val_onesided = p_val / 2
                    else:
                        p_val_onesided = 1 - (p_val / 2)
                    p_values.append(p_val_onesided)
                    valid_peaks.append((compound, fold_change, len(sample_vals), len(blank_vals)))
                except Exception:
                    filter_stats["insufficient_data"] += 1
                    # Fall back to fold-change only
                    if fold_change >= threshold:
                        kept.add(compound)
                        filter_stats["both_keep"] += 1
                    else:
                        filter_stats["both_discard"] += 1
            else:
                filter_stats["insufficient_data"] += 1
                # Not enough data for t-test - use fold-change only
                if fold_change >= threshold:
                    kept.add(compound)
                    filter_stats["both_keep"] += 1
                else:
                    filter_stats["both_discard"] += 1

        # Apply FDR correction (Benjamini-Hochberg)
        if fdr_correction and p_values:
            from scipy.stats import false_discovery_control

            try:
                adjusted_p = false_discovery_control(p_values, method="bh")
            except AttributeError:
                # Older scipy version - manual BH correction
                n = len(p_values)
                sorted_indices = sorted(range(n), key=lambda i: p_values[i])
                adjusted_p = [0.0] * n
                for rank, idx in enumerate(sorted_indices, 1):
                    adjusted_p[idx] = p_values[idx] * n / rank
                # Ensure monotonicity
                for i in range(n - 2, -1, -1):
                    sorted_idx = sorted_indices[i]
                    next_sorted_idx = sorted_indices[i + 1]
                    if adjusted_p[sorted_idx] > adjusted_p[next_sorted_idx]:
                        adjusted_p[sorted_idx] = adjusted_p[next_sorted_idx]
                adjusted_p = [min(p, 1.0) for p in adjusted_p]
        else:
            adjusted_p = p_values

        # Apply criteria: fold-change >= threshold AND adjusted p-value < cutoff
        for i, (compound, fold_change, _, _) in enumerate(valid_peaks):
            passes_fold = fold_change >= threshold
            passes_stat = adjusted_p[i] < p_value_cutoff if i < len(adjusted_p) else True

            if passes_fold:
                filter_stats["fold_change_pass"] += 1
            else:
                filter_stats["fold_change_fail"] += 1

            if passes_stat:
                filter_stats["stat_test_pass"] += 1
            else:
                filter_stats["stat_test_fail"] += 1

            if passes_fold and passes_stat:
                kept.add(compound)
                filter_stats["both_keep"] += 1
            else:
                filter_stats["both_discard"] += 1
    else:
        # No statistical test - use fold-change only
        for compound, _, _, fold_change in peak_data:
            if fold_change >= threshold:
                kept.add(compound)
                filter_stats["both_keep"] += 1
                filter_stats["fold_change_pass"] += 1
            else:
                filter_stats["both_discard"] += 1
                filter_stats["fold_change_fail"] += 1

    filter_stats["total_clean"] = filter_stats["sample_only"] + filter_stats["both_keep"]

    return kept, filter_stats


def filter_blanks(state: PipelineState) -> PipelineState:
    """
    Run blank subtraction on all tissues.

    Extracted from generate.py lines 400-430.

    This stage:
    1. Filters leaf samples against leaf blanks
    2. Filters root samples against root blanks
    3. Takes union of kept peaks (peak kept if it passes in EITHER tissue)

    Args:
        state: PipelineState with df_raw populated.

    Returns:
        Updated PipelineState with df_blank_filtered, kept_blank, blank_stats.
    """
    if state.df_raw is None:
        raise ValueError("df_raw is None - run load stage first")
    if state.config is None:
        raise ValueError("config is None - run load stage first")

    config = state.config
    df = state.df_raw

    # Get thresholds from config (direct typed access)
    threshold = config["thresholds"]["blank_filter"]["fold_change"]
    p_value_cutoff = config["thresholds"]["blank_filter"]["p_value"]
    fdr_correction = config["thresholds"]["blank_filter"]["fdr_correction"]

    print(f"\n{'='*60}")
    print("BLANK FILTERING")
    print(f"{'='*60}")
    print(f"Threshold: {threshold}x fold-change")
    print(f"P-value cutoff: {p_value_cutoff}")
    print(f"FDR correction: {fdr_correction}")
    print(f"Reference: {config['references']['blank_subtraction']['url']}")
    print(f"{'='*60}\n")

    # Get column names from config
    leaf_samples: list[str] = []
    for treatment in ["drought", "ambient", "watered"]:
        leaf_samples.extend(get_sample_columns(config, "leaf", treatment))

    root_samples: list[str] = []
    for treatment in ["drought", "ambient", "watered"]:
        root_samples.extend(get_sample_columns(config, "root", treatment))

    leaf_blanks = [c for c in get_blank_columns(config, "leaf") if c in df.columns]
    root_blanks = [c for c in get_blank_columns(config, "root") if c in df.columns]

    print(f"LEAF samples ({len(leaf_samples)}): {', '.join(leaf_samples[:3])}...")
    print(f"LEAF blanks ({len(leaf_blanks)}): {', '.join(leaf_blanks)}")
    print(f"ROOT samples ({len(root_samples)}): {', '.join(root_samples[:3])}...")
    print(f"ROOT blanks ({len(root_blanks)}): {', '.join(root_blanks)}")

    # Filter leaf samples
    print(f"\nFiltering LEAF samples with {len(leaf_blanks)} blanks...")
    kept_leaf, leaf_stats = _filter_blanks_single_tissue(
        df, leaf_samples, leaf_blanks, threshold, p_value_cutoff, fdr_correction
    )
    print(f"  Kept {len(kept_leaf):,} peaks, removed {leaf_stats['both_discard']:,}")

    # Filter root samples
    print(f"\nFiltering ROOT samples with {len(root_blanks)} blanks...")
    kept_root, root_stats = _filter_blanks_single_tissue(
        df, root_samples, root_blanks, threshold, p_value_cutoff, fdr_correction
    )
    print(f"  Kept {len(kept_root):,} peaks, removed {root_stats['both_discard']:,}")

    # Union of kept peaks
    kept_blank = kept_leaf | kept_root
    print(f"\nCombined: {len(kept_blank):,} unique peaks after blank filtering")

    # Aggregate stats (use create_blank_filter_stats for proper TypedDict)
    blank_stats = create_blank_filter_stats(
        sample_only=leaf_stats["sample_only"] + root_stats["sample_only"],
        both_keep=leaf_stats["both_keep"] + root_stats["both_keep"],
        both_discard=leaf_stats["both_discard"] + root_stats["both_discard"],
        blank_only=leaf_stats["blank_only"] + root_stats["blank_only"],
        neither=leaf_stats["neither"] + root_stats["neither"],
        fold_change_pass=leaf_stats["fold_change_pass"] + root_stats["fold_change_pass"],
        fold_change_fail=leaf_stats["fold_change_fail"] + root_stats["fold_change_fail"],
        stat_test_pass=leaf_stats["stat_test_pass"] + root_stats["stat_test_pass"],
        stat_test_fail=leaf_stats["stat_test_fail"] + root_stats["stat_test_fail"],
        insufficient_data=leaf_stats["insufficient_data"] + root_stats["insufficient_data"],
        statistical_test_used=leaf_stats["statistical_test_used"],
        fdr_corrected=leaf_stats["fdr_corrected"],
        p_value_cutoff=leaf_stats["p_value_cutoff"],
        fold_change_threshold=leaf_stats["fold_change_threshold"],
    )

    # Create filtered DataFrame
    df_blank_filtered = df.filter(pl.col("Compound").is_in(list(kept_blank)))

    # Update state
    state.df_blank_filtered = df_blank_filtered
    state.kept_blank = kept_blank
    state.blank_stats = blank_stats

    # Record stage completion
    state.add_stage_result(
        StageResult(
            stage_name="blank_filter",
            success=True,
            message=f"Kept {len(kept_blank):,} peaks after blank subtraction",
            input_count=df.height,
            output_count=len(kept_blank),
        )
    )

    return state
