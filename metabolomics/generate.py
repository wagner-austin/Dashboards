"""Generate HTML report with embedded interactive data tables."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

import polars as pl


# =============================================================================
# CONFIGURATION — loaded from config.json (single source of truth)
# =============================================================================

def _load_thresholds() -> tuple[float, float, bool, float, float]:
    """Load thresholds from config.json."""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)
    t = cfg["thresholds"]
    return (
        t["blank_filter"]["fold_change"],
        t["blank_filter"]["p_value"],
        t["blank_filter"]["fdr_correction"],
        t["cumulative_filter"]["threshold"],
        t["detection"]["min_value"],
    )

BLANK_FOLD_THRESHOLD, P_VALUE_CUTOFF, FDR_CORRECTION, CUMULATIVE_THRESHOLD, DETECTION_THRESHOLD = _load_thresholds()

# =============================================================================
# SAMPLE DEFINITIONS
# =============================================================================

# Treatment group definitions (Emily's samples with labeled columns)
TREATMENTS = {
    "Leaf": {
        "Drought": ["BL - Drought", "CL - Drought", "EL - Drought", "GL - Drought"],
        "Ambient": ["IL - Ambient", "JL - Ambient", "LL - Ambient", "ML - Ambient"],
        "Watered": ["OL - Watered", "PL - Watered", "RL - Watered", "TL - Watered"],
    },
    "Root": {
        "Drought": ["AR - Drought", "DR - Drought", "ER - Drought", "GR - Drought"],
        "Ambient": ["HR - Ambient", "IR - Ambient", "JR - Ambient", "MR - Ambient"],
        "Watered": ["RR - Watered", "SR - Watered", "TR - Watered"],
    },
}

# Tissue-specific blanks
# Blk1/Blk2 = leaf blanks, ebtruong blanks = root blanks
TISSUE_BLANKS = {
    "Leaf": ["Blk1", "Blk2"],
    "Root": [
        "250220_ebtruong_blank1",
        "250220_ebtruong_blank2",
        "250220_ebtruong_blank3",
        "250220_ebtruong_blank4",
    ],
}


def filter_cumulative(
    df: pl.DataFrame, col: str, threshold: float
) -> tuple[set[str], int, float]:
    """Filter to cumulative threshold."""
    temp = df.select(["Compound", col]).drop_nulls()
    if temp.height == 0:
        return set(), 0, 0
    temp = temp.sort(col, descending=True)
    compounds = temp["Compound"].to_list()
    areas = temp[col].to_list()
    total = sum(areas)
    if total == 0:
        return set(), 0, 0
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


def filter_min_pct(df: pl.DataFrame, col: str, min_pct: float) -> set[str]:
    """Filter to minimum percentage threshold."""
    temp = df.select(["Compound", col]).drop_nulls()
    if temp.height == 0:
        return set()
    compounds = temp["Compound"].to_list()
    areas = temp[col].to_list()
    total = sum(areas)
    if total == 0:
        return set()
    return {c for c, a in zip(compounds, areas, strict=True) if a / total >= min_pct}


def filter_blanks(
    df: pl.DataFrame, sample_cols: list[str], blank_cols: list[str],
    threshold: float | None = None,
    use_statistical_test: bool = True,
    p_value_cutoff: float | None = None,
    fdr_correction: bool | None = None
) -> tuple[set[str], dict]:
    """
    Filter peaks based on blank subtraction with optional statistical validation.

    Publication-quality filtering requires BOTH:
    1. Fold-change >= threshold (default from BLANK_FOLD_THRESHOLD) - biological significance
    2. Statistical test p-value < cutoff (default from P_VALUE_CUTOFF) - statistical significance

    When use_statistical_test=True:
    - Performs Welch's t-test (unequal variance t-test) for peaks in both samples and blanks
    - Applies FDR correction (Benjamini-Hochberg) for multiple testing when fdr_correction=True
    - Keeps peaks that pass BOTH fold-change AND statistical significance

    Returns (set of kept compounds, stats dict with validation metrics).
    """
    from scipy import stats as scipy_stats

    # Use centralized config defaults
    if threshold is None:
        threshold = BLANK_FOLD_THRESHOLD
    if p_value_cutoff is None:
        p_value_cutoff = P_VALUE_CUTOFF
    if fdr_correction is None:
        fdr_correction = FDR_CORRECTION

    compounds = df["Compound"].to_list()
    kept: set[str] = set()
    # Per-compound category: "sample_only", "both_keep", "both_discard", "blank_only", "neither"
    compound_category: dict[str, str] = {}
    # Per-compound detail for "both" peaks: "fold_pass", "fold_fail", "stat_pass", "stat_fail", "insufficient"
    compound_detail: dict[str, list[str]] = {}
    filter_stats = {
        "sample_only": 0,      # Peak in samples but not blanks (auto-keep)
        "both_keep": 0,        # Peak in both, passes all criteria
        "both_discard": 0,     # Peak in both, fails criteria
        "blank_only": 0,       # Peak only in blanks
        "neither": 0,          # Peak in neither
        "fold_change_pass": 0, # Passed fold-change test
        "fold_change_fail": 0, # Failed fold-change test
        "stat_test_pass": 0,   # Passed statistical test (before FDR)
        "stat_test_fail": 0,   # Failed statistical test
        "insufficient_data": 0, # Not enough data points for t-test
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
            compound_category[compound] = "sample_only"
        elif has_sample and has_blank:
            sample_avg = sum(sample_vals) / len(sample_vals)
            blank_avg = sum(blank_vals) / len(blank_vals)
            fold_change = sample_avg / blank_avg if blank_avg > 0 else float('inf')
            peak_data.append((compound, sample_vals, blank_vals, fold_change))
        elif has_blank and not has_sample:
            filter_stats["blank_only"] += 1
            compound_category[compound] = "blank_only"
        else:
            filter_stats["neither"] += 1
            compound_category[compound] = "neither"

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
                    compound_detail[compound] = ["insufficient"]
                    # Fall back to fold-change only
                    if fold_change >= threshold:
                        kept.add(compound)
                        filter_stats["both_keep"] += 1
                        compound_category[compound] = "both_keep"
                    else:
                        filter_stats["both_discard"] += 1
                        compound_category[compound] = "both_discard"
            else:
                filter_stats["insufficient_data"] += 1
                compound_detail[compound] = ["insufficient"]
                # Not enough data for t-test - use fold-change only
                if fold_change >= threshold:
                    kept.add(compound)
                    filter_stats["both_keep"] += 1
                    compound_category[compound] = "both_keep"
                else:
                    filter_stats["both_discard"] += 1
                    compound_category[compound] = "both_discard"

        # Apply FDR correction (Benjamini-Hochberg)
        if fdr_correction and p_values:
            from scipy.stats import false_discovery_control
            try:
                # Benjamini-Hochberg FDR correction
                adjusted_p = false_discovery_control(p_values, method='bh')
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
        for i, (compound, fold_change, n_sample, n_blank) in enumerate(valid_peaks):
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

            details = []
            if passes_fold:
                details.append("fold_pass")
            else:
                details.append("fold_fail")
            if passes_stat:
                details.append("stat_pass")
            else:
                details.append("stat_fail")
            compound_detail[compound] = details

            if passes_fold and passes_stat:
                kept.add(compound)
                filter_stats["both_keep"] += 1
                compound_category[compound] = "both_keep"
            else:
                filter_stats["both_discard"] += 1
                compound_category[compound] = "both_discard"
    else:
        # No statistical test - use fold-change only (original behavior)
        for compound, sample_vals, blank_vals, fold_change in peak_data:
            if fold_change >= threshold:
                kept.add(compound)
                filter_stats["both_keep"] += 1
                filter_stats["fold_change_pass"] += 1
                compound_category[compound] = "both_keep"
                compound_detail[compound] = ["fold_pass"]
            else:
                filter_stats["both_discard"] += 1
                filter_stats["fold_change_fail"] += 1
                compound_category[compound] = "both_discard"
                compound_detail[compound] = ["fold_fail"]

    filter_stats["total_clean"] = filter_stats["sample_only"] + filter_stats["both_keep"]
    filter_stats["statistical_test_used"] = use_statistical_test
    filter_stats["fdr_corrected"] = fdr_correction
    filter_stats["p_value_cutoff"] = p_value_cutoff
    filter_stats["fold_change_threshold"] = threshold
    filter_stats["compound_category"] = compound_category
    filter_stats["compound_detail"] = compound_detail

    return kept, filter_stats


def get_peaks_in_group(df: pl.DataFrame, cols: list[str]) -> set[str]:
    """Get peaks that have non-zero signal in any column of the group."""
    peaks = set()
    for col in cols:
        if col in df.columns:
            temp = df.select(["Compound", col]).drop_nulls()
            temp = temp.filter(pl.col(col) > 0)
            peaks.update(temp["Compound"].to_list())
    return peaks


def df_to_json(df: pl.DataFrame, sample_cols: list[str], formula_lookup: dict = None) -> str:
    """Convert DataFrame to JSON for DataTables."""
    records = []
    for row in df.iter_rows(named=True):
        record = {"Compound": row["Compound"]}

        # Add formula if lookup provided
        if formula_lookup:
            mz = row.get("m/z")
            rt = row.get("Retention time (min)")
            if mz and rt:
                key = (round(float(mz), 4), round(float(rt), 2))
                formula_info = formula_lookup.get(key, {})
                record["Formula"] = formula_info.get("formula", "")
            else:
                record["Formula"] = ""

        for col in sample_cols:
            val = row.get(col)
            if val is not None:
                record[col] = round(float(val), 2) if isinstance(val, (int, float)) else val
            else:
                record[col] = None
        records.append(record)
    return json.dumps(records)


def load_formulas() -> dict:
    """Load formula assignments and create lookup dict by (mz_round, rt_round)."""
    formula_path = Path(__file__).parent / "formulas_assigned.csv"
    if not formula_path.exists():
        print("No formulas_assigned.csv found, skipping formula integration")
        return {}

    import csv
    formulas = {}
    with open(formula_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                mz = round(float(row["exp_mass"]), 4)
                rt = round(float(row["RT"]), 2)
                formulas[(mz, rt)] = {
                    "formula": row["formula"],
                    "err_ppm": round(float(row["err_ppm"]), 2),
                }
            except (ValueError, KeyError):
                continue
    print(f"Loaded {len(formulas)} formula assignments")
    return formulas


def calculate_richness(data: pl.DataFrame, sample_cols: list[str]) -> list[int]:
    """Count non-zero peaks per sample."""
    richness = []
    for col in sample_cols:
        if col not in data.columns:
            continue
        count = data.filter(
            (pl.col(col).is_not_null()) & (pl.col(col) > DETECTION_THRESHOLD)
        ).height
        richness.append(count)
    return richness


def calc_se(values: list[int | float]) -> float:
    """Calculate standard error = stdev / sqrt(n)."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance / len(values))


def calculate_shannon(data: pl.DataFrame, sample_col: str) -> float:
    """Calculate Shannon diversity index for a sample."""
    if sample_col not in data.columns:
        return 0.0
    vals = data.select(sample_col).drop_nulls().to_series().to_list()
    vals = [v for v in vals if v > DETECTION_THRESHOLD]
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


def run_pipeline(df: pl.DataFrame, formula_lookup: dict, sheet_name: str = "") -> dict:
    """Run the full filtering pipeline on a DataFrame.

    Returns a dict with all computed values needed for HTML generation.
    """
    label = f"[{sheet_name}] " if sheet_name else ""

    # Build sample columns from treatment definitions
    sample_cols = []
    for tissue_treatments in TREATMENTS.values():
        for samples in tissue_treatments.values():
            sample_cols.extend(samples)

    # Build tissue-specific sample lists
    leaf_samples = []
    root_samples = []
    for treatment, samples in TREATMENTS["Leaf"].items():
        leaf_samples.extend(samples)
    for treatment, samples in TREATMENTS["Root"].items():
        root_samples.extend(samples)

    # Filter to blanks that exist in the data
    leaf_blanks = [c for c in TISSUE_BLANKS["Leaf"] if c in df.columns]
    root_blanks = [c for c in TISSUE_BLANKS["Root"] if c in df.columns]

    print(f"\n{'=' * 60}")
    print(f"{label}BLANK FILTERING CONFIGURATION")
    print("=" * 60)
    print(f"\nLEAF samples ({len(leaf_samples)}): {', '.join(leaf_samples)}")
    print(f"LEAF blanks ({len(leaf_blanks)}): {', '.join(leaf_blanks)}")
    print(f"\nROOT samples ({len(root_samples)}): {', '.join(root_samples)}")
    print(f"ROOT blanks ({len(root_blanks)}): {', '.join(root_blanks)}")
    print("=" * 60 + "\n")

    print(f"{label}Running filtering...")

    total = df["Compound"].n_unique()

    # Step 1: Tissue-specific blank filtering
    print(f"{label}Step 1: Tissue-specific blank filtering...")

    print(f"  Filtering LEAF samples with {len(leaf_blanks)} leaf blanks (threshold={BLANK_FOLD_THRESHOLD}x)...")
    kept_leaf, leaf_blank_stats = filter_blanks(df, leaf_samples, leaf_blanks)
    print(f"    Leaf: kept {len(kept_leaf):,} peaks, removed {leaf_blank_stats['both_discard']:,} contamination")

    print(f"  Filtering ROOT samples with {len(root_blanks)} root blanks (threshold={BLANK_FOLD_THRESHOLD}x)...")
    kept_root, root_blank_stats = filter_blanks(df, root_samples, root_blanks)
    print(f"    Root: kept {len(kept_root):,} peaks, removed {root_blank_stats['both_discard']:,} contamination")

    # Union of peaks kept from both tissues
    kept_blank = kept_leaf | kept_root

    # Compute deduplicated per-compound stats across tissues
    # A compound's combined category uses best outcome: kept in either tissue = kept
    leaf_cat = leaf_blank_stats["compound_category"]
    root_cat = root_blank_stats["compound_category"]
    leaf_det = leaf_blank_stats["compound_detail"]
    root_det = root_blank_stats["compound_detail"]
    all_compounds = set(leaf_cat.keys()) | set(root_cat.keys())

    # Priority: sample_only > both_keep > both_discard > blank_only > neither
    _cat_priority = {"sample_only": 4, "both_keep": 3, "both_discard": 2, "blank_only": 1, "neither": 0}
    combined_cat: dict[str, str] = {}
    for comp in all_compounds:
        lc = leaf_cat.get(comp)
        rc = root_cat.get(comp)
        if lc is None:
            combined_cat[comp] = rc  # type: ignore[assignment]
        elif rc is None:
            combined_cat[comp] = lc
        else:
            combined_cat[comp] = lc if _cat_priority[lc] >= _cat_priority[rc] else rc

    # Count deduplicated categories
    cat_counts = {"sample_only": 0, "both_keep": 0, "both_discard": 0, "blank_only": 0, "neither": 0}
    for cat in combined_cat.values():
        cat_counts[cat] += 1

    # Deduplicated detail stats - mutually exclusive groups
    # "had_test_data" = had enough replicates for t-test in at least one tissue
    # "insufficient_only" = lacked data in ALL tissues (fold-change only)
    detail_counts = {"fold_change_pass": 0, "fold_change_fail": 0, "stat_test_pass": 0, "stat_test_fail": 0, "insufficient_data": 0}
    both_compounds = {c for c, cat in combined_cat.items() if cat in ("both_keep", "both_discard")}
    for comp in both_compounds:
        ld = leaf_det.get(comp, [])
        rd = root_det.get(comp, [])
        all_details = set(ld) | set(rd)
        had_test_data = "stat_pass" in all_details or "stat_fail" in all_details
        if had_test_data:
            # Count fold/stat results (best outcome across tissues)
            if "fold_pass" in all_details:
                detail_counts["fold_change_pass"] += 1
            else:
                detail_counts["fold_change_fail"] += 1
            if "stat_pass" in all_details:
                detail_counts["stat_test_pass"] += 1
            else:
                detail_counts["stat_test_fail"] += 1
        else:
            # Insufficient data in all tissues — used fold-change only
            detail_counts["insufficient_data"] += 1

    blank_stats = {
        "sample_only": cat_counts["sample_only"],
        "both_keep": cat_counts["both_keep"],
        "both_discard": cat_counts["both_discard"],
        "blank_only": cat_counts["blank_only"],
        "neither": cat_counts["neither"],
        "total_clean": len(kept_blank),
        "fold_change_pass": detail_counts["fold_change_pass"],
        "fold_change_fail": detail_counts["fold_change_fail"],
        "stat_test_pass": detail_counts["stat_test_pass"],
        "stat_test_fail": detail_counts["stat_test_fail"],
        "insufficient_data": detail_counts["insufficient_data"],
    }
    df_blank_filtered = df.filter(pl.col("Compound").is_in(list(kept_blank)))
    print(f"  Combined: {len(kept_blank):,} unique peaks after tissue-specific blank filtering")

    # Step 2: 80% cumulative filtering on blank-filtered data
    print(f"{label}Step 2: 80% cumulative filtering...")
    kept_80: set[str] = set()
    sample_data_80: list[tuple[str, str, int, float]] = []

    for col in sample_cols:
        if col not in df_blank_filtered.columns:
            continue
        k80, n80, pct80 = filter_cumulative(df_blank_filtered, col, CUMULATIVE_THRESHOLD)
        kept_80.update(k80)
        tissue = "Leaf" if col[1] == "L" else "Root"
        sample_data_80.append((col, tissue, n80, pct80 * 100))

    # Create final filtered DataFrame
    print(f"{label}Creating filtered dataset...")
    available_cols = [c for c in sample_cols if c in df_blank_filtered.columns]
    extra_cols = [c for c in ["m/z", "Retention time (min)"] if c in df_blank_filtered.columns]
    df_80 = df_blank_filtered.filter(pl.col("Compound").is_in(list(kept_80))).select(["Compound"] + extra_cols + available_cols)

    # Convert to JSON
    print(f"{label}Converting to JSON...")
    json_80 = df_to_json(df_80, available_cols, formula_lookup)

    # Calculate stats
    leaf_80 = [x for x in sample_data_80 if x[1] == "Leaf"]
    root_80 = [x for x in sample_data_80 if x[1] == "Root"]

    # Venn diagram calculations
    print(f"{label}Calculating treatment overlaps...")
    venn_data = {}
    for tissue in ["Leaf", "Root"]:
        drought_peaks = get_peaks_in_group(df_80, TREATMENTS[tissue]["Drought"])
        ambient_peaks = get_peaks_in_group(df_80, TREATMENTS[tissue]["Ambient"])
        watered_peaks = get_peaks_in_group(df_80, TREATMENTS[tissue]["Watered"])

        all_peaks = drought_peaks | ambient_peaks | watered_peaks
        venn_data[tissue] = {
            "drought": len(drought_peaks),
            "ambient": len(ambient_peaks),
            "watered": len(watered_peaks),
            "all": len(all_peaks),
            "drought_only": len(drought_peaks - ambient_peaks - watered_peaks),
            "ambient_only": len(ambient_peaks - drought_peaks - watered_peaks),
            "watered_only": len(watered_peaks - drought_peaks - ambient_peaks),
            "drought_ambient": len((drought_peaks & ambient_peaks) - watered_peaks),
            "drought_watered": len((drought_peaks & watered_peaks) - ambient_peaks),
            "ambient_watered": len((ambient_peaks & watered_peaks) - drought_peaks),
            "all_three": len(drought_peaks & ambient_peaks & watered_peaks),
        }

    # Cross-tissue overlap
    leaf_all = get_peaks_in_group(df_80, [c for t in TREATMENTS["Leaf"].values() for c in t])
    root_all = get_peaks_in_group(df_80, [c for t in TREATMENTS["Root"].values() for c in t])
    venn_data["cross_tissue"] = {
        "total": len(leaf_all | root_all),
        "leaf_only": len(leaf_all - root_all),
        "root_only": len(root_all - leaf_all),
        "both": len(leaf_all & root_all),
    }

    # Chemical richness
    print(f"{label}Calculating chemical richness (from {df_blank_filtered.height:,} blank-filtered peaks)...")
    chemical_richness = {}
    total_blank_filtered = df_blank_filtered.height
    for tissue in ["Leaf", "Root"]:
        chemical_richness[tissue] = {}
        for treatment in ["Drought", "Ambient", "Watered"]:
            cols = TREATMENTS[tissue][treatment]
            richness_vals = calculate_richness(df_blank_filtered, cols)
            if richness_vals:
                mean_val = sum(richness_vals) / len(richness_vals)
                se_val = calc_se(richness_vals)
            else:
                mean_val, se_val = 0.0, 0.0
            chemical_richness[tissue][treatment] = {
                "mean": mean_val,
                "se": se_val,
                "n": len(richness_vals),
                "values": richness_vals,
                "total_possible": total_blank_filtered,
            }
            print(f"    {tissue} {treatment}: {mean_val:.1f} ± {se_val:.1f} peaks (n={len(richness_vals)}) out of {total_blank_filtered:,}")

    # Shannon diversity
    print(f"{label}Calculating Shannon diversity (from {df_blank_filtered.height:,} blank-filtered peaks)...")
    shannon_diversity = {}
    for tissue in ["Leaf", "Root"]:
        shannon_diversity[tissue] = {}
        for treatment in ["Drought", "Ambient", "Watered"]:
            cols = TREATMENTS[tissue][treatment]
            h_vals = [calculate_shannon(df_blank_filtered, col) for col in cols if col in df_blank_filtered.columns]
            if h_vals:
                mean_val = sum(h_vals) / len(h_vals)
                se_val = calc_se(h_vals)
            else:
                mean_val, se_val = 0.0, 0.0
            shannon_diversity[tissue][treatment] = {
                "mean": mean_val,
                "se": se_val,
                "n": len(h_vals),
                "values": h_vals,
            }
            print(f"    {tissue} {treatment}: H = {mean_val:.3f} ± {se_val:.3f} (n={len(h_vals)})")

    # Priority peaks analysis
    print(f"{label}Building priority peaks data...")
    meta_cols = ["Compound", "m/z", "Retention time (min)", "Anova (p)", "q Value", "Max Fold Change", "Minimum CV%"]
    meta_cols = [c for c in meta_cols if c in df.columns]
    df_meta = df.select(meta_cols)

    all_peaks_data = {"Leaf": [], "Root": []}
    for tissue in ["Leaf", "Root"]:
        compounds = df_80["Compound"].to_list()

        for compound in compounds:
            meta_row = df_meta.filter(pl.col("Compound") == compound)
            if meta_row.height == 0:
                continue
            meta_row = meta_row.row(0, named=True)

            data_row = df_80.filter(pl.col("Compound") == compound)
            if data_row.height == 0:
                continue

            abundances = {}
            occurrences = {}
            for treat_name in ["Drought", "Ambient", "Watered"]:
                treat_cols = [c for c in TREATMENTS[tissue][treat_name] if c in df_80.columns]
                if treat_cols:
                    vals = [data_row[c][0] for c in treat_cols if data_row[c][0] is not None and data_row[c][0] > 0]
                    abundances[treat_name.lower()] = sum(float(v) for v in vals) / len(vals) if vals else 0
                    occurrences[treat_name.lower()] = f"{len(vals)}/{len(treat_cols)}"
                else:
                    abundances[treat_name.lower()] = 0
                    occurrences[treat_name.lower()] = "0/0"

            if abundances["drought"] == 0 and abundances["ambient"] == 0 and abundances["watered"] == 0:
                continue

            in_drought = abundances["drought"] > 0
            in_ambient = abundances["ambient"] > 0
            in_watered = abundances["watered"] > 0

            p_val = meta_row.get("Anova (p)", 1)
            try:
                p_val = float(p_val) if p_val is not None else 1
            except:
                p_val = 1

            fold_change = meta_row.get("Max Fold Change", "")
            try:
                fold_change = float(fold_change) if fold_change and str(fold_change) != "Infinity" else None
            except:
                fold_change = None

            cv_pct = meta_row.get("Minimum CV%", None)
            try:
                cv_pct = float(cv_pct) if cv_pct is not None else None
            except:
                cv_pct = None

            mz_val = meta_row.get("m/z", "")
            rt_val = meta_row.get("Retention time (min)", "")
            formula_info = formula_lookup.get(
                (round(float(mz_val), 4), round(float(rt_val), 2)) if mz_val and rt_val else (0, 0),
                {}
            )

            all_peaks_data[tissue].append({
                "compound": compound,
                "mz": mz_val,
                "rt": rt_val,
                "formula": formula_info.get("formula", ""),
                "drought": abundances["drought"],
                "ambient": abundances["ambient"],
                "watered": abundances["watered"],
                "drought_occ": occurrences["drought"],
                "ambient_occ": occurrences["ambient"],
                "watered_occ": occurrences["watered"],
                "in_drought": in_drought,
                "in_ambient": in_ambient,
                "in_watered": in_watered,
                "p_value": p_val,
                "fold_change": fold_change,
                "cv": cv_pct,
            })

        all_peaks_data[tissue].sort(key=lambda x: max(x["drought"], x["ambient"], x["watered"]), reverse=True)

    # Count formula matches among filtered peaks and collect ppm errors
    formula_matched = set()
    formula_ppm_values: list[float] = []
    for tissue_peaks in all_peaks_data.values():
        for peak in tissue_peaks:
            if peak["formula"] and peak["compound"] not in formula_matched:
                formula_matched.add(peak["compound"])
                mz_key = (round(float(peak["mz"]), 4), round(float(peak["rt"]), 2)) if peak["mz"] and peak["rt"] else (0, 0)
                info = formula_lookup.get(mz_key, {})
                if "err_ppm" in info:
                    formula_ppm_values.append(abs(info["err_ppm"]))
    formula_match_count = len(formula_matched)
    formula_mean_ppm = round(sum(formula_ppm_values) / len(formula_ppm_values), 2) if formula_ppm_values else 0

    # Build column definitions for DataTables
    col_defs = [{"data": "Compound", "title": "Compound"}]
    if formula_lookup:
        col_defs.append({"data": "Formula", "title": "Formula"})
    for col in available_cols:
        col_defs.append({"data": col, "title": col})

    # Build per-sample table rows
    leaf_rows = ""
    root_rows = ""
    leaf_num = 1
    root_num = 1
    for col, tissue, count, pct in sample_data_80:
        if tissue == "Leaf":
            row = f'<tr><td>{leaf_num}</td><td>{col}</td><td><strong>{count:,}</strong></td><td><strong>{pct:.4f}%</strong></td></tr>'
            leaf_rows += row
            leaf_num += 1
        else:
            row = f'<tr><td>{root_num}</td><td>{col}</td><td><strong>{count:,}</strong></td><td><strong>{pct:.4f}%</strong></td></tr>'
            root_rows += row
            root_num += 1

    # Package overview stats for JS
    overview_stats = {
        "total": total,
        "kept_blank": len(kept_blank),
        "kept_80": len(kept_80),
        "pct_kept": round(100 * len(kept_80) / total, 1) if total > 0 else 0,
        "total_removed": total - len(kept_blank),
        "both_discard": blank_stats["both_discard"],
        "sample_only": blank_stats["sample_only"],
        "both_keep": blank_stats["both_keep"],
        "blank_only": blank_stats["blank_only"],
        "neither": blank_stats["neither"],
        "fold_change_pass": blank_stats.get("fold_change_pass", 0),
        "fold_change_fail": blank_stats.get("fold_change_fail", 0),
        "stat_test_pass": blank_stats.get("stat_test_pass", 0),
        "stat_test_fail": blank_stats.get("stat_test_fail", 0),
        "insufficient_data": blank_stats.get("insufficient_data", 0),
        "leaf_blanks": ", ".join(leaf_blanks),
        "root_blanks": ", ".join(root_blanks),
        "leaf_avg_80": round(sum(x[2] for x in leaf_80) / len(leaf_80)) if leaf_80 else 0,
        "root_avg_80": round(sum(x[2] for x in root_80) / len(root_80)) if root_80 else 0,
        "leaf_rows_html": leaf_rows,
        "root_rows_html": root_rows,
        "formula_match_count": formula_match_count,
        "formula_match_pct": round(100 * formula_match_count / len(kept_80), 1) if len(kept_80) > 0 else 0,
        "formula_mean_ppm": formula_mean_ppm,
    }

    return {
        "total": total,
        "kept_blank": kept_blank,
        "blank_stats": blank_stats,
        "kept_80": kept_80,
        "sample_data_80": sample_data_80,
        "leaf_80": leaf_80,
        "root_80": root_80,
        "json_80": json_80,
        "col_defs_json": json.dumps(col_defs),
        "available_cols": available_cols,
        "chemical_richness": chemical_richness,
        "shannon_diversity": shannon_diversity,
        "venn_data": venn_data,
        "all_peaks_data": all_peaks_data,
        "all_peaks_json": json.dumps(all_peaks_data),
        "leaf_rows": leaf_rows,
        "root_rows": root_rows,
        "overview_stats": overview_stats,
    }


def main() -> int:
    # Use local copy of labeled data
    data_path = Path(__file__).parent / "Emily_Data_Pruned_Labeled.xlsx"

    # Load formula assignments
    formula_lookup = load_formulas()

    # Run pipeline for both sheets
    print("Loading Normalized data...")
    df_norm = pl.read_excel(data_path, sheet_name="Normalized", infer_schema_length=None)
    norm = run_pipeline(df_norm, formula_lookup, "Normalized")

    print("\nLoading Unnormalized data...")
    df_unnorm = pl.read_excel(data_path, sheet_name="Unnormalized", infer_schema_length=None)
    unnorm = run_pipeline(df_unnorm, formula_lookup, "Unnormalized")

    print("\nGenerating HTML...")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1024, viewport-fit=cover, user-scalable=yes">
    <title>Metabolomics Filtering Analysis</title>

    <!-- DataTables CSS -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
    <link rel="stylesheet" href="https://cdn.datatables.net/buttons/2.4.2/css/buttons.dataTables.min.css">

    <style>
        :root {{
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --primary-light: #dbeafe;
            --success: #16a34a;
            --success-light: #dcfce7;
            --warning: #ca8a04;
            --warning-light: #fef3c7;
            --leaf-color: #10b981;
            --leaf-bg: #ecfdf5;
            --root-color: #f59e0b;
            --root-bg: #fffbeb;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-600: #374151;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            font-size: 1.25rem;
            line-height: 1.6;
            color: var(--gray-800);
            background: var(--gray-100);
        }}

        .header {{
            background: white;
            border-bottom: 1px solid var(--gray-200);
            padding: 1.5rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .header h1 {{
            font-size: 1.5rem;
            color: var(--gray-900);
        }}

        .header-container {{
            position: sticky;
            top: 0;
            z-index: 100;
            background: white;
        }}

        .tabs {{
            display: flex;
            gap: 0.25rem;
            background: white;
            padding: 0.5rem 2rem;
            border-bottom: 1px solid var(--gray-200);
        }}

        .tab {{
            padding: 1rem 1.5rem;
            cursor: pointer;
            border: none;
            background: #fef9e7;
            font-size: 1rem;
            color: var(--gray-700);
            border-bottom: 3px solid transparent;
            border-radius: 6px;
            transition: all 0.2s;
        }}

        .tab:hover {{
            background: #fef3c7;
        }}

        .tab.active {{
            color: var(--gray-800);
            border: none;
            border-bottom: 3px solid var(--primary);
            background: white;
        }}

        .tab-content {{
            display: none;
            padding: 2rem;
            background: white;
            min-height: calc(100vh - 150px);
        }}

        .tab-content.active {{
            display: block;
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .card {{
            background: var(--gray-50);
            border-radius: 8px;
            padding: 1.25rem;
            border: 1px solid var(--gray-200);
        }}

        .card.highlight {{
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            border-color: var(--primary);
        }}

        .card.leaf {{
            background: linear-gradient(135deg, var(--leaf-bg) 0%, #d1fae5 100%);
            border-color: var(--leaf-color);
        }}

        .card.root {{
            background: linear-gradient(135deg, var(--root-bg) 0%, #fef3c7 100%);
            border-color: var(--root-color);
        }}

        .card h4 {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--gray-600);
            margin-bottom: 0.25rem;
        }}

        .card .value {{
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--gray-900);
        }}

        .card .subtext {{
            font-size: 0.8rem;
            color: var(--gray-600);
        }}

        h2 {{
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: var(--gray-800);
        }}

        h3 {{
            font-size: 1rem;
            margin: 1.5rem 0 0.75rem;
            color: var(--gray-700);
        }}

        p {{
            margin-bottom: 1rem;
            color: var(--gray-600);
        }}

        .alert {{
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-size: 0.9rem;
        }}

        .alert-info {{
            background: #eff6ff;
            border-left: 4px solid var(--primary);
            color: var(--primary-dark);
        }}

        .alert-success {{
            background: #f0fdf4;
            border-left: 4px solid var(--success);
            color: #166534;
        }}

        pre {{
            background: var(--gray-800);
            color: #e5e7eb;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
            font-size: 0.85rem;
        }}

        code {{
            background: var(--gray-100);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-size: 0.85rem;
        }}

        ul, ol {{
            margin: 1rem 0;
            padding-left: 1.5rem;
            color: var(--gray-600);
        }}

        li {{
            margin-bottom: 0.5rem;
        }}

        table.dataTable {{
            font-size: 0.85rem;
        }}

        table.dataTable thead th {{
            background: var(--gray-100);
            font-weight: 600;
        }}

        .dataTables_wrapper {{
            margin-top: 1rem;
        }}

        .dt-buttons {{
            margin-bottom: 1rem;
        }}

        .dt-button {{
            background: var(--primary) !important;
            color: white !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            border-radius: 6px !important;
            font-size: 0.85rem !important;
        }}

        .dt-button:hover {{
            background: var(--primary-dark) !important;
        }}

        .method-section {{
            background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            border: 1px solid var(--gray-200);
        }}

        .method-section.method-1 {{
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            border-color: var(--primary-light);
        }}

        .method-section.method-2 {{
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            border-color: var(--success-light);
        }}

        .two-col {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
        }}


        .table-container {{
            overflow-x: auto;
        }}

        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            font-size: 0.9rem;
        }}

        .info-table th, .info-table td {{
            padding: 0.6rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--gray-200);
        }}

        .info-table th {{
            background: var(--gray-100);
            font-weight: 600;
        }}

        .kept {{ color: var(--success); font-weight: 600; }}
        .filtered {{ color: #dc2626; font-weight: 600; }}

        /* Priority peaks highlight */
        .priority-row-highlight {{
            background: #fef3c7 !important;
            border-color: #f59e0b !important;
            box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.3);
        }}

        /* Treatment toggle buttons */
        .treatment-toggle {{
            padding: 0.5rem 1.25rem;
            border: 2px solid transparent;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.15s;
        }}
        .treatment-toggle:hover {{
            opacity: 0.85;
        }}
        .treatment-toggle.active[data-treatment="drought"] {{
            background: #dc2626 !important;
            color: white !important;
            border-color: #b91c1c;
        }}
        .treatment-toggle.active[data-treatment="ambient"] {{
            background: #2563eb !important;
            color: white !important;
            border-color: #1d4ed8;
        }}
        .treatment-toggle.active[data-treatment="watered"] {{
            background: #16a34a !important;
            color: white !important;
            border-color: #15803d;
        }}

        /* Viz toggle buttons */
        .viz-toggle {{
            padding: 0.4rem 0.8rem;
            border: 1px solid #e5e7eb;
            border-radius: 4px;
            background: white;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.15s;
        }}
        .viz-toggle:hover {{
            background: #f3f4f6;
        }}
        .viz-toggle.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}
        /* Make chart containers scrollable on small screens */
        #chart-area {{
            overflow-x: auto;
            max-width: 100%;
        }}
        #chart-area svg {{
            display: block;
            max-width: 100%;
            height: auto;
        }}
        /* Normalized/Unnormalized toggle */
        .norm-btn {{
            padding: 0.5rem 1.25rem;
            border: none;
            background: white;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s;
            color: var(--gray-600);
        }}
        .norm-btn.active {{
            background: var(--primary);
            color: white;
        }}
        .norm-btn:hover:not(.active) {{
            background: var(--primary-light);
        }}
    </style>
</head>
<body>
    <div class="header-container">
        <div class="header" style="display: flex; align-items: center; justify-content: space-between;">
            <h1>Metabolomics Filtering Analysis</h1>
            <div id="norm-toggle" style="display: flex; gap: 0; border: 2px solid var(--primary); border-radius: 8px; overflow: hidden;">
                <button class="norm-btn active" onclick="switchDataset('Normalized')">Normalized</button>
                <button class="norm-btn" onclick="switchDataset('Unnormalized')">Unnormalized</button>
            </div>
        </div>

        <div class="tabs">
        <button class="tab active" onclick="showTab('overview')">Overview</button>
        <button class="tab" onclick="showTab('diversity')">Diversity</button>
        <button class="tab" onclick="showTab('priority')">Priority Peaks</button>
        <button class="tab" onclick="showTab('venn')">Treatment Overlap</button>
        <button class="tab" onclick="showTab('methods')">Methods</button>
        <button class="tab" onclick="showTab('data80')">Filtered Data (<span id="tab-kept-80"></span>)</button>
        <button class="tab" onclick="showTab('peaks')">Understanding Peaks</button>
        </div>
    </div>

    <!-- OVERVIEW TAB -->
    <div id="overview" class="tab-content active">
        <h2>Summary</h2>
        <p>Filtered metabolomics data using a two-step process: blank subtraction followed by 80% cumulative signal threshold.</p>

        <div class="summary-cards">
            <div class="card">
                <h4>Original Data</h4>
                <div class="value"><span id="ov-total"></span> <span style="font-size: 0.5em; font-weight: normal;">Peaks</span></div>
                <div class="subtext">unique peaks before filtering</div>
            </div>
            <div class="card" style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border-color: #f87171;">
                <h4>After Blank Filter</h4>
                <div class="value"><span id="ov-kept-blank"></span> <span style="font-size: 0.5em; font-weight: normal;">Peaks</span></div>
                <div class="subtext"><span id="ov-total-removed"></span> peaks removed</div>
            </div>
            <div class="card highlight">
                <h4>Final (80% Filter)</h4>
                <div class="value"><span id="ov-kept-80"></span> <span style="font-size: 0.5em; font-weight: normal;">Peaks</span></div>
                <div class="subtext"><span id="ov-pct-kept"></span>% of original kept</div>
            </div>
        </div>

        <div class="alert alert-success" style="margin: 1.5rem 0;">
            <strong>Two-Step Filtering:</strong> First, we remove peaks that appear in blanks (contamination). Then we apply 80% cumulative signal filtering to keep only the most significant peaks.
        </div>

        <h3>Blank Filtering Results</h3>
        <table class="info-table">
            <tr><th>Category</th><th>Count</th><th>Description</th></tr>
            <tr><td class="kept">Sample Only</td><td><span id="ov-sample-only"></span></td><td>Peaks only in samples, not in blanks (auto-kept)</td></tr>
            <tr><td class="kept">Passed Validation</td><td><span id="ov-both-keep"></span></td><td>Passed both fold-change (≥{BLANK_FOLD_THRESHOLD:.0f}x) AND statistical test (p&lt;{P_VALUE_CUTOFF}, FDR-corrected)</td></tr>
            <tr><td class="filtered">Contamination</td><td><span id="ov-both-discard2"></span></td><td>Failed fold-change or statistical test (removed)</td></tr>
            <tr><td>Blank Only</td><td><span id="ov-blank-only"></span></td><td>Peaks only in blanks (not in samples)</td></tr>
            <tr><td>No Signal</td><td><span id="ov-neither"></span></td><td>No detectable signal in any sample or blank</td></tr>
        </table>

        <h4 style="margin-top: 1.5rem;">Statistical Validation Details</h4>
        <table class="info-table">
            <tr><th>Criterion</th><th>Passed</th><th>Failed</th><th>Description</th></tr>
            <tr><td>Fold-Change ≥{BLANK_FOLD_THRESHOLD:.0f}x</td><td class="kept"><span id="ov-fc-pass"></span></td><td class="filtered"><span id="ov-fc-fail"></span></td><td>Sample mean ≥ {BLANK_FOLD_THRESHOLD:.0f}× blank mean (<a href="https://bioconductor.org/packages/release/bioc/html/pmp.html" target="_blank">pmp/Bioconductor</a>)</td></tr>
            <tr><td>Welch's t-test</td><td class="kept"><span id="ov-stat-pass"></span></td><td class="filtered"><span id="ov-stat-fail"></span></td><td>p &lt; {P_VALUE_CUTOFF} (FDR-corrected, one-sided)</td></tr>
            <tr><td>Insufficient Data</td><td colspan="2"><span id="ov-insufficient"></span></td><td>Not enough replicates for t-test (used fold-change only)</td></tr>
        </table>

        <div class="alert alert-success" style="margin-top: 1rem;">
            <strong>Validation Method:</strong> Publication-quality blank subtraction using dual criteria: (1) fold-change ≥{BLANK_FOLD_THRESHOLD:.0f}x for biological significance (<a href="https://bioconductor.org/packages/release/bioc/html/pmp.html" target="_blank">pmp/Bioconductor</a>), and (2) Welch's t-test with Benjamini-Hochberg FDR correction for statistical significance (p &lt; {P_VALUE_CUTOFF}).
        </div>

        <h3>Source Data</h3>
        <ul>
            <li><strong>File:</strong> Emily_Data_Pruned_Labeled.xlsx</li>
            <li><strong>Sheet:</strong> <span id="ov-sheet">Normalized</span></li>
            <li><strong>Samples:</strong> 23 total (12 Leaf, 11 Root) - Emily's samples only</li>
            <li><strong>Leaf blanks:</strong> <span id="ov-leaf-blanks"></span></li>
            <li><strong>Root blanks:</strong> <span id="ov-root-blanks"></span></li>
        </ul>

        <div class="alert alert-info" style="margin: 1.5rem 0;">
            <strong>Key Finding:</strong> Root tissue reaches 80% much faster (avg ~<span id="ov-root-avg"></span> peaks) than leaf tissue (avg ~<span id="ov-leaf-avg"></span> peaks). This means roots have a few dominant compounds while leaves have signal spread across more compounds.
        </div>

        <h3>Leaf vs Root</h3>
        <p>Root samples have more concentrated signal - fewer peaks make up 80% of the total.</p>

        <div class="summary-cards">
            <div class="card leaf">
                <h4>Leaf Avg</h4>
                <div class="value"><span id="ov-leaf-avg2"></span></div>
                <div class="subtext">peaks to reach 80%</div>
            </div>
            <div class="card root">
                <h4>Root Avg</h4>
                <div class="value"><span id="ov-root-avg2"></span></div>
                <div class="subtext">peaks to reach 80%</div>
            </div>
        </div>

        <h2 style="margin-top: 2rem; padding: 1rem; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 8px; margin-bottom: 0;">80% Threshold Results - Per Sample</h2>
        <p style="color: var(--gray-600); margin-bottom: 1.5rem; padding: 0.75rem 1rem; background: var(--gray-50); border-left: 3px solid var(--primary); font-size: 0.9rem; font-style: italic;">Each row shows one tissue sample and how many peaks were needed to account for 80% of its total signal (after blank filtering). Samples with fewer peaks needed have more concentrated signal.</p>

        <div class="two-col">
            <div>
                <h4 style="color: var(--leaf-color); padding: 0.5rem; background: var(--leaf-bg); border-radius: 6px; display: inline-block;">Leaf Tissue (12 samples)</h4>
                <table class="info-table" style="margin-top: 0.75rem;">
                    <tr style="background: var(--leaf-bg);"><th>#</th><th>ID</th><th>Peaks Needed</th><th>Smallest Peak Kept</th></tr>
                    <tbody id="ov-leaf-rows"></tbody>
                </table>
            </div>
            <div>
                <h4 style="color: var(--root-color); padding: 0.5rem; background: var(--root-bg); border-radius: 6px; display: inline-block;">Root Tissue (11 samples)</h4>
                <table class="info-table" style="margin-top: 0.75rem;">
                    <tr style="background: var(--root-bg);"><th>#</th><th>ID</th><th>Peaks Needed</th><th>Smallest Peak Kept</th></tr>
                    <tbody id="ov-root-rows"></tbody>
                </table>
            </div>
        </div>

        <div class="method-section" style="margin-top: 1.5rem;">
            <h4>How to Read This Table</h4>
            <ul>
                <li><strong>Peaks Needed</strong> = How many peaks it takes to add up to 80% of that tissue's total signal</li>
                <li><strong>Smallest Peak Kept</strong> = The % contribution of the last peak that made the cut (anything smaller was filtered out)</li>
            </ul>
            <p style="margin-top: 1rem;"><strong>Example:</strong> If a sample needed 500 peaks to reach 80% of its signal, those 500 peaks are the most abundant compounds. The smallest peak kept might contribute 0.02% - anything contributing less was filtered as noise.</p>
        </div>

    </div>

    <!-- DIVERSITY TAB -->
    <div id="diversity" class="tab-content">
        <h2>Chemical Richness & Diversity</h2>
        <p>Comparison of metabolite richness (peak counts) and Shannon diversity index across treatments.</p>

        <div class="alert alert-info" style="margin-bottom: 1.5rem;">
            <strong>Data Source:</strong> Blank-filtered dataset (<span id="div-kept-blank"></span> peaks after {BLANK_FOLD_THRESHOLD:.0f}x blank subtraction).<br>
            <strong>NOT</strong> the 80% cumulative-filtered dataset (<span id="div-kept-80"></span> peaks).<br>
            <em>Richness and diversity are calculated BEFORE the 80% filter to capture full metabolome complexity.</em>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 2rem; margin-top: 1.5rem;">
            <!-- Chemical Richness Section -->
            <div>
                <h3>Chemical Richness (Peak Counts)</h3>
                <p style="color: var(--gray-600); font-size: 0.9em;">Number of detected metabolites per sample (mean ± SE) out of <span id="div-kept-blank2"></span> total peaks</p>

                <div style="margin-top: 1rem;">
                    <h4 style="color: var(--leaf-color);">Leaf Tissue</h4>
                    <div id="richness-table-leaf"></div>
                </div>

                <div style="margin-top: 1rem;">
                    <h4 style="color: var(--root-color);">Root Tissue</h4>
                    <div id="richness-table-root"></div>
                </div>

                <div id="richness-chart" style="margin-top: 1rem; min-height: 300px;"></div>
            </div>

            <!-- Shannon Diversity Section -->
            <div>
                <h3>Shannon Diversity Index (H)</h3>
                <p style="color: var(--gray-600); font-size: 0.9em;">H = -Σ(p × ln(p)) where p = relative abundance (<a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC3901240/" target="_blank">Vinaixa et al. 2012</a>)</p>

                <div style="margin-top: 1rem;">
                    <h4 style="color: var(--leaf-color);">Leaf Tissue</h4>
                    <div id="shannon-table-leaf"></div>
                </div>

                <div style="margin-top: 1rem;">
                    <h4 style="color: var(--root-color);">Root Tissue</h4>
                    <div id="shannon-table-root"></div>
                </div>

                <div id="shannon-chart" style="margin-top: 1rem; min-height: 300px;"></div>
            </div>
        </div>

        <div class="alert alert-info" style="margin-top: 2rem;">
            <strong>Interpretation:</strong><br>
            • <strong>Chemical Richness:</strong> Higher values indicate more metabolites detected. Differences may reflect stress responses or metabolic shifts.<br>
            • <strong>Shannon Diversity:</strong> Higher H indicates more even distribution of metabolite abundances. Lower H suggests dominance by fewer compounds.
        </div>

        <div class="method-section" style="margin-top: 2rem; padding: 1.5rem; background: var(--gray-50); border-radius: 8px; border-left: 4px solid var(--primary);">
            <h4 style="margin-top: 0;">Methodology (Exact Calculations)</h4>

            <h5>Chemical Richness</h5>
            <pre>
Data source: df_blank_filtered (after {BLANK_FOLD_THRESHOLD:.0f}x blank subtraction)

For each sample column (e.g., "BL - Drought"):
    richness = COUNT of rows WHERE value > {DETECTION_THRESHOLD}

For each treatment:
    mean = SUM(sample_richness_values) / n_samples
    SE = STDEV(sample_richness_values) / SQRT(n_samples)</pre>

            <h5 style="margin-top: 1rem;">Shannon Diversity Index</h5>
            <pre>
Data source: df_blank_filtered (after {BLANK_FOLD_THRESHOLD:.0f}x blank subtraction)

For each sample column:
    1. Get all peak abundances where value > {DETECTION_THRESHOLD}
    2. total = SUM(all abundances)
    3. For each peak: p = abundance / total
    4. H = -SUM(p × ln(p))

For each treatment:
    mean = SUM(H_values) / n_samples
    SE = STDEV(H_values) / SQRT(n_samples)</pre>

            <p style="margin-top: 1rem; color: var(--gray-600); font-size: 0.9em;">
                <strong>Why blank-filtered, not 80%-filtered?</strong> The 80% cumulative filter removes low-abundance peaks to focus analysis.
                But richness and diversity metrics should capture the FULL metabolome complexity, so we use the larger blank-filtered dataset.
            </p>
        </div>

        <div class="alert alert-success" style="margin-top: 1rem;">
            <strong>References:</strong><br>
            • Shannon diversity index: <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC3901240/" target="_blank">Vinaixa et al. 2012, Metabolites</a><br>
            • Chemical richness methods: <a href="https://link.springer.com/article/10.1134/S1021443720030085" target="_blank">Fu et al. 2020, Russian Journal of Plant Physiology</a>
        </div>
    </div>

    <!-- PRIORITY PEAKS TAB -->
    <div id="priority" class="tab-content">
        <h2>Compare Treatments</h2>
        <p>Toggle treatments to compare. Shows peaks that differ between selected treatments.</p>

        <!-- Toggle buttons -->
        <div style="display: flex; gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap; align-items: center;">
            <span style="font-weight: 600; color: var(--gray-600);">Select treatments:</span>
            <button id="toggle-drought" class="treatment-toggle active" onclick="toggleTreatment('drought')" style="background: #dc2626; color: white;">Drought</button>
            <button id="toggle-ambient" class="treatment-toggle" onclick="toggleTreatment('ambient')" style="background: #e5e7eb; color: #374151;">Ambient</button>
            <button id="toggle-watered" class="treatment-toggle" onclick="toggleTreatment('watered')" style="background: #e5e7eb; color: #374151;">Watered</button>
            <span id="comparison-hint" style="color: var(--gray-600); font-size: 0.9em; margin-left: 1rem;"></span>
        </div>

        <!-- Visualization section (shows when 2 treatments selected) -->
        <div id="viz-section" style="display: none; margin-bottom: 2rem;">
            <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem; align-items: center; flex-wrap: wrap;">
                <span style="font-weight: 600; color: var(--gray-600);">View:</span>
                <button class="viz-toggle active" data-viz="bubble" onclick="setVizType('bubble')">Bubble Chart</button>
                <button class="viz-toggle" data-viz="bars" onclick="setVizType('bars')">Fold Change Bars</button>
            </div>
            <div class="two-col">
                <div>
                    <h4 style="color: var(--root-color); margin-bottom: 0.5rem;">Root</h4>
                    <div id="viz-root" style="background: white; border-radius: 8px; padding: 0.5rem; min-height: 550px;"></div>
                </div>
                <div>
                    <h4 style="color: var(--leaf-color); margin-bottom: 0.5rem;">Leaf</h4>
                    <div id="viz-leaf" style="background: white; border-radius: 8px; padding: 0.5rem; min-height: 550px;"></div>
                </div>
            </div>
            <p id="viz-info" style="color: var(--gray-600); font-size: 0.85em; margin-top: 0.5rem; text-align: center;"></p>
        </div>

        <div class="two-col" style="margin-top: 1rem;">
            <div>
                <h3 style="color: var(--root-color); margin-bottom: 1rem;">
                    Root Tissue <span id="root-peak-count" style="font-weight: normal; font-size: 0.8em;"></span>
                </h3>
                <div id="priority-root" style="background: white; border-radius: 8px; padding: 1rem; max-height: 500px; overflow: auto;"></div>
            </div>
            <div>
                <h3 style="color: var(--leaf-color); margin-bottom: 1rem;">
                    Leaf Tissue <span id="leaf-peak-count" style="font-weight: normal; font-size: 0.8em;"></span>
                </h3>
                <div id="priority-leaf" style="background: white; border-radius: 8px; padding: 1rem; max-height: 500px; overflow: auto;"></div>
            </div>
        </div>

        <div class="alert alert-info" style="margin-top: 1.5rem;">
            <strong>m/z</strong> = mass-to-charge ratio. Molecular formulas assigned via MFAssignR (see Methods tab)
            <br>
            <strong>RT</strong> = retention time (minutes)
            <br>
            <strong>Abundance</strong> = normalized peak area (unitless, higher = more compound)
        </div>
    </div>

    <!-- TREATMENT OVERLAP TAB -->
    <div id="venn" class="tab-content">
        <h2>Treatment Overlap</h2>
        <p>Shows how peaks are distributed across treatment groups (Drought, Ambient, Watered). "Unique" means the peak is ONLY found in that treatment, not in the others.</p>

        <div class="two-col" style="margin-top: 1.5rem;">
            <div class="method-section" style="background: linear-gradient(135deg, var(--leaf-bg) 0%, #d1fae5 100%); border-color: var(--leaf-color);">
                <h3 style="color: var(--leaf-color); margin-top: 0;">Leaf Tissue (<span id="venn-leaf-all"></span> peaks)</h3>
                <div id="venn-leaf-table"></div>
                <div class="alert alert-info" style="margin-top: 1rem;">
                    <strong><span id="venn-leaf-pct"></span>%</strong> of leaf peaks are shared across all treatments
                </div>
            </div>

            <div class="method-section" style="background: linear-gradient(135deg, var(--root-bg) 0%, #fef3c7 100%); border-color: var(--root-color);">
                <h3 style="color: var(--root-color); margin-top: 0;">Root Tissue (<span id="venn-root-all"></span> peaks)</h3>
                <div id="venn-root-table"></div>
                <div class="alert alert-info" style="margin-top: 1rem;">
                    <strong><span id="venn-root-pct"></span>%</strong> of root peaks are shared across all treatments
                </div>
            </div>
        </div>

        <div class="method-section" style="margin-top: 2rem; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-color: #3b82f6;">
            <h3 style="color: #1e40af; margin-top: 0;">Cross-Tissue Overlap</h3>
            <p style="margin-bottom: 0.75rem;">How peaks are shared between leaf and root tissues (<span id="venn-cross-total"></span> unique peaks total).</p>
            <table class="info-table">
                <tr><th>Region</th><th>Peaks</th><th>Meaning</th></tr>
                <tr><td><strong style="color: var(--leaf-color);">Leaf Only</strong></td><td><strong><span id="venn-cross-leaf"></span></strong></td><td>Detected in leaf but not root</td></tr>
                <tr><td><strong style="color: var(--root-color);">Root Only</strong></td><td><strong><span id="venn-cross-root"></span></strong></td><td>Detected in root but not leaf</td></tr>
                <tr><td><strong>Both Tissues</strong></td><td><strong><span id="venn-cross-both"></span></strong></td><td>Detected in both leaf and root</td></tr>
            </table>
            <div class="alert alert-info" style="margin-top: 1rem;">
                <strong><span id="venn-cross-pct"></span>%</strong> of peaks are found in both tissues
            </div>
        </div>

        <div class="alert alert-success" style="margin-top: 2rem;">
            <strong>How to interpret:</strong> Peaks unique to a treatment (e.g., "Drought Only") are potential biomarkers for that stress condition. Peaks shared by all three are likely core metabolites present regardless of water availability. Peaks unique to a tissue (leaf-only or root-only) may reflect tissue-specific metabolism.
        </div>
    </div>

    <!-- METHODS TAB -->
    <div id="methods" class="tab-content">
        <h2>Two-Step Filtering Process</h2>
        <p>We use a two-step filtering approach to ensure data quality: first removing contamination, then keeping only significant peaks.</p>

        <div class="method-section" style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border-color: #f87171;">
            <h3>Step 1: Blank Subtraction (Contamination Removal)</h3>
            <p>Blanks are samples run through the instrument with no plant material - they capture background contamination from solvents, plastics, and the instrument itself.</p>

            <div class="alert alert-info">
                <strong>How it works:</strong>
            </div>

            <pre>For each peak found in BOTH samples and blanks:
1. Calculate fold-change: sample_mean / blank_mean
2. Perform Welch's t-test (one-sided: sample > blank)
3. Apply Benjamini-Hochberg FDR correction for multiple testing
4. KEEP only if BOTH criteria pass:
   - Fold-change ≥ {BLANK_FOLD_THRESHOLD:.0f}x (biological significance, per pmp/Bioconductor)
   - FDR-adjusted p-value &lt; {P_VALUE_CUTOFF} (statistical significance)

Peaks ONLY in samples (not in blanks) → auto-KEEP</pre>

            <p><strong>Why dual criteria?</strong> The {BLANK_FOLD_THRESHOLD:.0f}x fold-change threshold (<a href="https://bioconductor.org/packages/release/bioc/html/pmp.html" target="_blank">pmp/Bioconductor standard</a>) ensures biological relevance (a peak must be meaningfully higher in samples). The statistical test ensures the difference isn't due to random variation. FDR correction accounts for testing thousands of peaks simultaneously.</p>

            <div class="alert alert-info" style="margin-top: 1rem;">
                <strong>Statistical Details:</strong><br>
                • <strong>Welch's t-test:</strong> Compares sample vs blank means without assuming equal variance<br>
                • <strong>One-sided test:</strong> Tests if sample > blank (not just different)<br>
                • <strong>FDR correction:</strong> Benjamini-Hochberg method controls false discovery rate at 5%
            </div>

            <div class="alert alert-success">
                <strong>Leaf blanks:</strong> <span id="meth-leaf-blanks"></span><br>
                <strong>Root blanks:</strong> <span id="meth-root-blanks"></span>
            </div>
        </div>

        <div class="method-section method-1">
            <h3>Step 2: 80% Cumulative Signal Threshold</h3>
            <p>After removing contamination, we filter to keep only the most abundant peaks.</p>

            <div class="alert alert-info">
                <strong>How it works (for each sample separately):</strong>
            </div>

            <pre>1. Take all peaks and their area values for one sample
2. Sort peaks from LARGEST to SMALLEST
3. Add up the areas as you go down the list
4. Stop when you've added up 80% of the total
5. Everything above that line is kept</pre>

            <p><strong>Important:</strong> A compound is kept if it makes the cut in ANY sample. This ensures we don't lose peaks that are important in specific tissues.</p>
        </div>

        <h3>Why Two Steps?</h3>
        <table class="info-table">
            <tr><th>Step</th><th>Purpose</th><th>What it removes</th></tr>
            <tr><td>Blank Subtraction</td><td>Remove contamination</td><td>Plasticizers, solvent impurities, instrument background</td></tr>
            <tr><td>80% Threshold</td><td>Remove noise</td><td>Low-abundance peaks that contribute little to the biological profile</td></tr>
        </table>

        <div class="alert alert-info" style="margin-top: 1.5rem;">
            <strong>Note on the 80% cutoff:</strong> The algorithm keeps adding peaks until the cumulative sum crosses 80%. Two peaks with nearly identical contributions may get different treatment based on where the threshold falls. This is inherent to cumulative thresholds but ensures a consistent reduction in data complexity.
        </div>

        <div class="method-section" style="margin-top: 2rem; background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-color: #3b82f6;">
            <h3>Step 3: Molecular Formula Assignment (MFAssignR)</h3>
            <p>After filtering, we assign molecular formulas to peaks using the <strong>MFAssignR</strong> R package, which calculates which chemical formulas could produce each measured mass.</p>

            <div class="alert alert-info">
                <strong>How it works:</strong>
            </div>

            <pre>For each peak's m/z value:
1. Calculate neutral mass: m/z - 1.007276 (remove proton from [M+H]+)
2. Find all formulas (combinations of C, H, O, N, S, P) that match within 3 ppm
3. Apply chemical rules to filter invalid formulas:
   - H/C ratio between 0.2 and 3.0
   - O/C ratio between 0 and 1.2
   - Nitrogen rule (even/odd mass)
   - Valid double bond equivalents (DBE)
4. Use isotope patterns (13C, 34S) to confirm assignments
5. Select best-matching formula</pre>

            <h4 style="margin-top: 1.5rem;">Parameters Used</h4>
            <table class="info-table">
                <tr><th>Parameter</th><th>Value</th><th>Meaning</th></tr>
                <tr><td>Ion Mode</td><td>Positive [M+H]+</td><td>Compounds detected as protonated molecules</td></tr>
                <tr><td>Mass Error</td><td>3 ppm</td><td>Maximum allowed difference between measured and theoretical mass</td></tr>
                <tr><td>Mass Range</td><td>100-1000 Da</td><td>Only assign formulas to peaks in this range</td></tr>
                <tr><td>Elements</td><td>C, H, O, N≤4, S≤2, P≤2</td><td>Allowed elements and maximum counts</td></tr>
            </table>

            <h4 style="margin-top: 1.5rem;">Understanding PPM Error</h4>
            <p><strong>PPM (parts per million)</strong> measures how close the measured mass is to the theoretical formula mass:</p>
            <pre>ppm = (measured - theoretical) / theoretical × 1,000,000

Example: m/z 427.3778 vs C26H50O4+H theoretical 427.3782
         ppm = (427.3778 - 427.3782) / 427.3782 × 1,000,000 = -0.9 ppm</pre>
            <p>Lower ppm = higher confidence. Our assignments average <strong><span id="meth-formula-ppm2"></span> ppm</strong>, which is excellent.</p>

            <h4 style="margin-top: 1.5rem;">Formula Classes</h4>
            <table class="info-table">
                <tr><th>Class</th><th>Elements</th><th>Typical Compounds</th></tr>
                <tr><td>CHO</td><td>C, H, O only</td><td>Sugars, fatty acids, terpenes</td></tr>
                <tr><td>CHNO</td><td>+ Nitrogen</td><td>Amino acids, alkaloids</td></tr>
                <tr><td>CHNOS</td><td>+ Sulfur</td><td>Sulfur-containing amino acids</td></tr>
                <tr><td>CHNOP</td><td>+ Phosphorus</td><td>Phospholipids, nucleotides</td></tr>
            </table>

            <div class="alert alert-warning" style="margin-top: 1.5rem; background: #fefce8; border-color: #facc15;">
                <strong>Important Limitation:</strong> A molecular formula (e.g., C26H50O4) tells you the <em>atoms</em> present, not the <em>structure</em>. Many different compounds (isomers) can share the same formula. Definitive identification requires MS/MS fragmentation data.
            </div>

            <div class="alert alert-success" style="margin-top: 1rem;">
                <strong>Assignment Results:</strong> <span id="meth-formula-count"></span> peaks assigned formulas (<span id="meth-formula-pct"></span>% of filtered peaks). Mean mass error: <span id="meth-formula-ppm"></span> ppm.
            </div>
        </div>
    </div>

    <!-- FILTERED DATA TAB -->
    <div id="data80" class="tab-content">
        <h2 style="padding: 1rem; background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-radius: 8px; margin-bottom: 0;">Filtered Metabolomics Data</h2>
        <p style="color: var(--gray-600); margin-bottom: 1.5rem; padding: 0.75rem 1rem; background: var(--gray-50); border-left: 3px solid var(--primary); font-size: 0.9rem; font-style: italic;">Two-step filtered data: blank subtraction ({BLANK_FOLD_THRESHOLD:.0f}x threshold, <a href="https://bioconductor.org/packages/release/bioc/html/pmp.html" target="_blank">pmp/Bioconductor</a>) followed by {CUMULATIVE_THRESHOLD*100:.0f}% cumulative signal threshold.</p>
        <div class="summary-cards">
            <div class="card">
                <h4>Original Peaks</h4>
                <div class="value"><span id="dt-total"></span></div>
                <div class="subtext">before any filtering</div>
            </div>
            <div class="card" style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border-color: #f87171;">
                <h4>After Blank Filter</h4>
                <div class="value"><span id="dt-kept-blank"></span></div>
                <div class="subtext"><span id="dt-total-removed"></span> peaks removed</div>
            </div>
            <div class="card highlight">
                <h4>Final Peaks</h4>
                <div class="value"><span id="dt-kept-80"></span></div>
                <div class="subtext"><span id="dt-pct-kept"></span>% of original kept</div>
            </div>
        </div>
        <div class="table-container">
            <table id="table80" class="display" style="width:100%"></table>
        </div>
    </div>

    <!-- PEAKS TAB -->
    <div id="peaks" class="tab-content">
        <h2 style="padding: 1rem; background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%); border-radius: 8px; margin-bottom: 1rem;">What Do These Peak Names Mean?</h2>

        <p><strong>Each compound is identified by a code like <code>3.90_564.1489n</code>. This encodes two measurements:</strong></p>

        <table class="info-table">
            <tr><th>Part</th><th>Example</th><th>Meaning</th></tr>
            <tr><td>First number</td><td>3.90</td><td><strong>Retention time</strong> (minutes) - how long it took to pass through the column</td></tr>
            <tr><td>Second number</td><td>564.1489</td><td><strong>Mass</strong> (m/z) - the molecular weight detected</td></tr>
            <tr><td>Suffix</td><td>n or m/z</td><td>Just notation style</td></tr>
        </table>

        <div class="alert alert-info">
            <strong>Important:</strong> These are NOT identified compounds. We know something with mass 564.1489 eluted at 3.90 minutes, but we don't know what molecule it is yet.
        </div>

        <h3>How to Identify Peaks</h3>
        <ol>
            <li><strong>Database search</strong> - Look up the mass in METLIN, HMDB, or MassBank</li>
            <li><strong>Run standards</strong> - Buy a pure compound and see if it matches</li>
            <li><strong>MS/MS fragmentation</strong> - Break it apart and look at the pieces</li>
            <li><strong>Literature</strong> - Check what others found in similar plants</li>
        </ol>

        <h3>What You Can Do Without Identification</h3>
        <ul>
            <li>Compare samples - "Sample A has more of peak X than Sample B"</li>
            <li>Find patterns - "Leaves have these 50 peaks that roots don't"</li>
            <li>Track changes - "This peak increased over time"</li>
            <li>Prioritize - Focus on identifying the biggest/most variable peaks first</li>
        </ul>
    </div>

    <!-- JavaScript -->
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.4.2/js/dataTables.buttons.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.4.2/js/buttons.html5.min.js"></script>

    <script>
        // Both datasets
        const DATASETS = {{
            "Normalized": {{
                data80: {norm["json_80"]},
                columns: {norm["col_defs_json"]},
                chemicalRichness: {json.dumps(norm["chemical_richness"])},
                shannonDiversity: {json.dumps(norm["shannon_diversity"])},
                allPeaksData: {norm["all_peaks_json"]},
                overviewStats: {json.dumps(norm["overview_stats"])},
                vennData: {json.dumps(norm["venn_data"])}
            }},
            "Unnormalized": {{
                data80: {unnorm["json_80"]},
                columns: {unnorm["col_defs_json"]},
                chemicalRichness: {json.dumps(unnorm["chemical_richness"])},
                shannonDiversity: {json.dumps(unnorm["shannon_diversity"])},
                allPeaksData: {unnorm["all_peaks_json"]},
                overviewStats: {json.dumps(unnorm["overview_stats"])},
                vennData: {json.dumps(unnorm["venn_data"])}
            }}
        }};

        var currentMode = "Normalized";

        // Active dataset references
        var data80 = DATASETS[currentMode].data80;
        var columns = DATASETS[currentMode].columns;
        var chemicalRichness = DATASETS[currentMode].chemicalRichness;
        var shannonDiversity = DATASETS[currentMode].shannonDiversity;
        var allPeaksData = DATASETS[currentMode].allPeaksData;

        // Format number with commas
        function fmt(n) {{ return n.toLocaleString(); }}

        // Update overview tab from stats object
        function updateOverview(s) {{
            document.getElementById('ov-total').textContent = fmt(s.total);
            document.getElementById('ov-kept-blank').textContent = fmt(s.kept_blank);
            document.getElementById('ov-total-removed').textContent = fmt(s.total_removed);
            document.getElementById('ov-kept-80').textContent = fmt(s.kept_80);
            document.getElementById('ov-pct-kept').textContent = s.pct_kept;
            document.getElementById('ov-sample-only').textContent = fmt(s.sample_only);
            document.getElementById('ov-both-keep').textContent = fmt(s.both_keep);
            document.getElementById('ov-both-discard2').textContent = fmt(s.both_discard);
            document.getElementById('ov-blank-only').textContent = fmt(s.blank_only);
            document.getElementById('ov-neither').textContent = fmt(s.neither);
            document.getElementById('ov-fc-pass').textContent = fmt(s.fold_change_pass);
            document.getElementById('ov-fc-fail').textContent = fmt(s.fold_change_fail);
            document.getElementById('ov-stat-pass').textContent = fmt(s.stat_test_pass);
            document.getElementById('ov-stat-fail').textContent = fmt(s.stat_test_fail);
            document.getElementById('ov-insufficient').textContent = fmt(s.insufficient_data);
            document.getElementById('ov-sheet').textContent = currentMode;
            document.getElementById('ov-leaf-blanks').textContent = s.leaf_blanks;
            document.getElementById('ov-root-blanks').textContent = s.root_blanks;
            document.getElementById('ov-leaf-avg').textContent = fmt(s.leaf_avg_80);
            document.getElementById('ov-root-avg').textContent = fmt(s.root_avg_80);
            document.getElementById('ov-leaf-avg2').textContent = fmt(s.leaf_avg_80);
            document.getElementById('ov-root-avg2').textContent = fmt(s.root_avg_80);
            document.getElementById('ov-leaf-rows').innerHTML = s.leaf_rows_html;
            document.getElementById('ov-root-rows').innerHTML = s.root_rows_html;
            // Methods tab
            document.getElementById('meth-leaf-blanks').textContent = s.leaf_blanks;
            document.getElementById('meth-root-blanks').textContent = s.root_blanks;
            document.getElementById('meth-formula-count').textContent = fmt(s.formula_match_count);
            document.getElementById('meth-formula-pct').textContent = s.formula_match_pct;
            document.getElementById('meth-formula-ppm').textContent = s.formula_mean_ppm;
            document.getElementById('meth-formula-ppm2').textContent = s.formula_mean_ppm;
        }}

        // Update diversity tab tables
        function updateDiversityTables(cr, sd) {{
            document.getElementById('div-kept-blank').textContent = fmt(DATASETS[currentMode].overviewStats.kept_blank);
            document.getElementById('div-kept-80').textContent = fmt(DATASETS[currentMode].overviewStats.kept_80);
            document.getElementById('div-kept-blank2').textContent = fmt(DATASETS[currentMode].overviewStats.kept_blank);

            ['Leaf', 'Root'].forEach(function(tissue) {{
                var colors = {{Drought: '#fee2e2', Ambient: '#dbeafe', Watered: '#dcfce7'}};
                // Richness table
                var rhtml = '<table class="info-table"><tr><th>Treatment</th><th>Mean</th><th>SE</th><th>n</th></tr>';
                ['Drought', 'Ambient', 'Watered'].forEach(function(t) {{
                    rhtml += '<tr><td style="background:' + colors[t] + ';">' + t + '</td><td>' + cr[tissue][t].mean.toFixed(1) + '</td><td>±' + cr[tissue][t].se.toFixed(1) + '</td><td>' + cr[tissue][t].n + '</td></tr>';
                }});
                rhtml += '</table>';
                document.getElementById('richness-table-' + tissue.toLowerCase()).innerHTML = rhtml;
                // Shannon table
                var shtml = '<table class="info-table"><tr><th>Treatment</th><th>Mean H</th><th>SE</th><th>n</th></tr>';
                ['Drought', 'Ambient', 'Watered'].forEach(function(t) {{
                    shtml += '<tr><td style="background:' + colors[t] + ';">' + t + '</td><td>' + sd[tissue][t].mean.toFixed(3) + '</td><td>±' + sd[tissue][t].se.toFixed(3) + '</td><td>' + sd[tissue][t].n + '</td></tr>';
                }});
                shtml += '</table>';
                document.getElementById('shannon-table-' + tissue.toLowerCase()).innerHTML = shtml;
            }});
        }}

        // Update venn tab
        function updateVennTab(vd) {{
            ['Leaf', 'Root'].forEach(function(tissue) {{
                var t = tissue.toLowerCase();
                var d = vd[tissue];
                document.getElementById('venn-' + t + '-all').textContent = fmt(d.all);
                var pct = d.all > 0 ? (100 * d.all_three / d.all).toFixed(1) : '0.0';
                document.getElementById('venn-' + t + '-pct').textContent = pct;
                var html = '<table class="info-table"><tr><th>Region</th><th>Peaks</th><th>Meaning</th></tr>';
                html += '<tr><td><strong style="color:#dc2626;">Drought Only</strong></td><td><strong>' + fmt(d.drought_only) + '</strong></td><td>Only in drought, not ambient or watered</td></tr>';
                html += '<tr><td><strong style="color:#2563eb;">Ambient Only</strong></td><td><strong>' + fmt(d.ambient_only) + '</strong></td><td>Only in ambient, not drought or watered</td></tr>';
                html += '<tr><td><strong style="color:#16a34a;">Watered Only</strong></td><td><strong>' + fmt(d.watered_only) + '</strong></td><td>Only in watered, not drought or ambient</td></tr>';
                html += '<tr><td>Drought + Ambient</td><td><strong>' + fmt(d.drought_ambient) + '</strong></td><td>Shared by D &amp; A, not W</td></tr>';
                html += '<tr><td>Drought + Watered</td><td><strong>' + fmt(d.drought_watered) + '</strong></td><td>Shared by D &amp; W, not A</td></tr>';
                html += '<tr><td>Ambient + Watered</td><td><strong>' + fmt(d.ambient_watered) + '</strong></td><td>Shared by A &amp; W, not D</td></tr>';
                html += '<tr><td><strong>All Three</strong></td><td><strong>' + fmt(d.all_three) + '</strong></td><td>Present in all treatments (core metabolites)</td></tr>';
                html += '</table>';
                document.getElementById('venn-' + t + '-table').innerHTML = html;
            }});
            var ct = vd.cross_tissue;
            document.getElementById('venn-cross-total').textContent = fmt(ct.total);
            document.getElementById('venn-cross-leaf').textContent = fmt(ct.leaf_only);
            document.getElementById('venn-cross-root').textContent = fmt(ct.root_only);
            document.getElementById('venn-cross-both').textContent = fmt(ct.both);
            document.getElementById('venn-cross-pct').textContent = ct.total > 0 ? (100 * ct.both / ct.total).toFixed(1) : '0.0';
        }}

        // Update filtered data tab stats
        function updateDataTabStats(s) {{
            document.getElementById('dt-total').textContent = fmt(s.total);
            document.getElementById('dt-kept-blank').textContent = fmt(s.kept_blank);
            document.getElementById('dt-total-removed').textContent = fmt(s.total_removed);
            document.getElementById('dt-kept-80').textContent = fmt(s.kept_80);
            document.getElementById('dt-pct-kept').textContent = s.pct_kept;
            document.getElementById('tab-kept-80').textContent = fmt(s.kept_80);
        }}

        // Switch between Normalized/Unnormalized
        function switchDataset(mode) {{
            currentMode = mode;
            var ds = DATASETS[mode];

            // Update active references
            data80 = ds.data80;
            columns = ds.columns;
            chemicalRichness = ds.chemicalRichness;
            shannonDiversity = ds.shannonDiversity;
            allPeaksData = ds.allPeaksData;

            // Toggle button styling
            document.querySelectorAll('.norm-btn').forEach(function(btn) {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');

            // Update all tabs
            updateOverview(ds.overviewStats);
            updateDiversityTables(ds.chemicalRichness, ds.shannonDiversity);
            updateVennTab(ds.vennData);
            updateDataTabStats(ds.overviewStats);

            // Destroy and recreate DataTable
            if ($.fn.DataTable.isDataTable('#table80')) {{
                $('#table80').DataTable().destroy();
                $('#table80').empty();
            }}
            initTable('#table80', ds.data80, ds.columns);

            // Re-render diversity charts
            renderDiversityCharts();

            // Re-render priority peaks
            updateComparison();
            updateVisualization();
        }}

        // Tab switching
        function showTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }}

        function initTable(selector, tableData, tableCols) {{
            if (tableCols === undefined) tableCols = columns;
            $(selector).DataTable({{
                data: tableData,
                columns: tableCols,
                pageLength: 50,
                scrollX: true,
                dom: 'Bfrtip',
                buttons: [
                    {{
                        extend: 'csv',
                        text: 'Export CSV',
                        filename: 'metabolomics_filtered'
                    }},
                    {{
                        extend: 'excel',
                        text: 'Export Excel',
                        filename: 'metabolomics_filtered'
                    }}
                ],
                language: {{
                    search: "Search compounds:"
                }}
            }});
        }}

        // Initialize on page load
        $(document).ready(function() {{
            // Populate all dynamic content
            updateOverview(DATASETS[currentMode].overviewStats);
            updateDiversityTables(DATASETS[currentMode].chemicalRichness, DATASETS[currentMode].shannonDiversity);
            updateVennTab(DATASETS[currentMode].vennData);
            updateDataTabStats(DATASETS[currentMode].overviewStats);

            setTimeout(function() {{
                initTable('#table80', data80, columns);
            }}, 500);
        }});

        // Toggle state
        var toggleState = {{ drought: true, ambient: false, watered: false }};

        // Toggle treatment button
        function toggleTreatment(treatment) {{
            toggleState[treatment] = !toggleState[treatment];
            updateToggleButtons();
            updateComparison();
            updateVisualization();
        }}

        function updateToggleButtons() {{
            ['drought', 'ambient', 'watered'].forEach(function(t) {{
                var btn = document.getElementById('toggle-' + t);
                btn.setAttribute('data-treatment', t);
                if (toggleState[t]) {{
                    btn.classList.add('active');
                }} else {{
                    btn.classList.remove('active');
                    btn.style.background = '#e5e7eb';
                    btn.style.color = '#374151';
                }}
            }});

            // Update hint text
            var active = Object.keys(toggleState).filter(function(k) {{ return toggleState[k]; }});
            var hint = document.getElementById('comparison-hint');
            if (active.length === 0) {{
                hint.textContent = '(select at least one treatment)';
            }} else if (active.length === 1) {{
                hint.textContent = '→ Showing peaks unique to ' + active[0];
            }} else if (active.length === 2) {{
                hint.textContent = '→ Comparing ' + active[0] + ' vs ' + active[1];
            }} else {{
                hint.textContent = '→ Showing all peaks';
            }}
        }}

        function updateComparison() {{
            renderFilteredPeaks('#priority-root', allPeaksData.Root);
            renderFilteredPeaks('#priority-leaf', allPeaksData.Leaf);
        }}

        function renderFilteredPeaks(selector, data) {{
            var container = d3.select(selector);
            container.html('');

            var active = Object.keys(toggleState).filter(function(k) {{ return toggleState[k]; }});

            if (active.length === 0) {{
                container.append('p').style('color', '#666').text('Select at least one treatment above.');
                d3.select(selector.replace('priority-', '') + '-peak-count').text('');
                return;
            }}

            // Filter peaks based on toggle state
            var filtered = data.filter(function(d) {{
                if (active.length === 1) {{
                    // Show peaks ONLY in this treatment
                    var t = active[0];
                    return d['in_' + t] && !d['in_' + otherTreatments(t)[0]] && !d['in_' + otherTreatments(t)[1]];
                }} else if (active.length === 2) {{
                    // Show peaks in either treatment (for comparison)
                    var t1 = active[0], t2 = active[1];
                    return d['in_' + t1] || d['in_' + t2];
                }} else {{
                    // Show all peaks
                    return true;
                }}
            }});

            // Sort by max abundance in selected treatments
            filtered.sort(function(a, b) {{
                var maxA = Math.max.apply(null, active.map(function(t) {{ return a[t] || 0; }}));
                var maxB = Math.max.apply(null, active.map(function(t) {{ return b[t] || 0; }}));
                return maxB - maxA;
            }});

            // Update count
            var countId = selector === '#priority-root' ? 'root-peak-count' : 'leaf-peak-count';
            document.getElementById(countId).textContent = '(' + filtered.length + ' peaks)';

            if (filtered.length === 0) {{
                container.append('p').style('color', '#666').text('No peaks match this selection.');
                return;
            }}

            // Wrapper for horizontal scroll
            var tableWrapper = container.append('div')
                .style('min-width', '600px');

            // Column headers
            var headerRow = tableWrapper.append('div')
                .style('display', 'flex')
                .style('flex-wrap', 'nowrap')
                .style('font-size', '0.7em')
                .style('color', '#666')
                .style('margin-bottom', '0.5rem')
                .style('padding', '0.25rem')
                .style('font-weight', '600')
                .style('border-bottom', '2px solid #e5e7eb');
            headerRow.append('div').style('width', '25px').style('text-align', 'center').text('#');
            headerRow.append('div').style('width', '130px').style('margin-right', '8px').text('Compound');
            headerRow.append('div').style('width', '100px').style('margin-right', '8px').text('Formula');
            headerRow.append('div').style('width', '75px').style('text-align', 'right').style('margin-right', '8px').text('m/z');
            headerRow.append('div').style('width', '40px').style('text-align', 'right').style('margin-right', '8px').text('RT');
            headerRow.append('div').style('width', '45px').style('text-align', 'right').style('margin-right', '8px').text('CV%');

            // Dynamic abundance columns based on selection (with occurrence sub-header)
            active.forEach(function(t) {{
                var color = {{ drought: '#dc2626', ambient: '#2563eb', watered: '#16a34a' }}[t];
                headerRow.append('div')
                    .style('width', '90px')
                    .style('text-align', 'right')
                    .style('color', color)
                    .html(t.charAt(0).toUpperCase() + t.slice(1) + '<br><span style="font-weight:normal;font-size:0.85em">(n/total)</span>');
            }});

            // Rows (limit to 100 for performance)
            var rowContainer = tableWrapper.append('div');
            filtered.slice(0, 100).forEach(function(d, i) {{
                var row = rowContainer.append('div')
                    .style('display', 'flex')
                    .style('flex-wrap', 'nowrap')
                    .style('align-items', 'center')
                    .style('padding', '0.3rem 0.25rem')
                    .style('background', i % 2 === 0 ? '#f9fafb' : 'white')
                    .style('font-size', '0.75em');

                row.append('div').style('width', '25px').style('text-align', 'center').style('color', '#999').text(i + 1);

                var name = d.compound.length > 16 ? d.compound.substring(0, 13) + '...' : d.compound;
                row.append('div').style('width', '130px').style('margin-right', '8px').style('font-family', 'monospace').style('font-size', '0.95em').attr('title', d.compound).text(name);
                row.append('div').style('width', '100px').style('margin-right', '8px').style('font-family', 'monospace').style('font-size', '0.95em').style('color', d.formula ? '#2563eb' : '#ccc').text(d.formula || '-');
                row.append('div').style('width', '75px').style('margin-right', '8px').style('text-align', 'right').style('font-family', 'monospace').text(d.mz ? parseFloat(d.mz).toFixed(4) : '-');
                row.append('div').style('width', '40px').style('margin-right', '8px').style('text-align', 'right').style('font-family', 'monospace').text(d.rt ? parseFloat(d.rt).toFixed(1) : '-');

                // CV% with color coding
                var cvText = d.cv ? d.cv.toFixed(0) + '%' : '-';
                var cvColor = d.cv ? (d.cv < 30 ? '#16a34a' : d.cv < 60 ? '#ca8a04' : '#dc2626') : '#999';
                row.append('div').style('width', '45px').style('margin-right', '8px').style('text-align', 'right').style('color', cvColor).text(cvText);

                active.forEach(function(t) {{
                    var val = d[t] || 0;
                    var occ = d[t + '_occ'] || '0/0';
                    var color = {{ drought: '#dc2626', ambient: '#2563eb', watered: '#16a34a' }}[t];
                    var cellDiv = row.append('div')
                        .style('width', '90px')
                        .style('text-align', 'right')
                        .style('font-family', 'monospace');

                    if (val > 0) {{
                        cellDiv.html('<span style="color:' + color + '">' + val.toExponential(1) + '</span> <span style="color:#999;font-size:0.85em">(' + occ + ')</span>');
                    }} else {{
                        cellDiv.style('color', '#ccc').text('0 (' + occ + ')');
                    }}
                }});
            }});

            if (filtered.length > 100) {{
                container.append('p')
                    .style('color', '#666')
                    .style('font-size', '0.85em')
                    .style('margin-top', '0.5rem')
                    .text('Showing top 100 of ' + filtered.length + ' peaks');
            }}
        }}

        function otherTreatments(t) {{
            var all = ['drought', 'ambient', 'watered'];
            return all.filter(function(x) {{ return x !== t; }});
        }}

        // Visualization state
        var currentVizType = 'bubble';
        var treatmentColors = {{ drought: '#dc2626', ambient: '#2563eb', watered: '#16a34a' }};

        function setVizType(type) {{
            currentVizType = type;
            document.querySelectorAll('.viz-toggle').forEach(function(btn) {{
                btn.classList.toggle('active', btn.getAttribute('data-viz') === type);
            }});
            updateVisualization();
        }}

        function updateVisualization() {{
            var active = Object.keys(toggleState).filter(function(k) {{ return toggleState[k]; }});

            // Show viz section for any selection (1, 2, or 3 treatments)
            var vizSection = document.getElementById('viz-section');
            if (active.length >= 1) {{
                vizSection.style.display = 'block';
                renderViz('#viz-root', allPeaksData.Root, active);
                renderViz('#viz-leaf', allPeaksData.Leaf, active);
            }} else {{
                vizSection.style.display = 'none';
            }}
        }}

        function renderViz(selector, data, treatments) {{
            var container = d3.select(selector);
            container.html('');

            // Filter data based on selection
            var filtered;
            if (treatments.length === 1) {{
                // Peaks unique to this treatment
                var t = treatments[0];
                var others = ['drought', 'ambient', 'watered'].filter(function(x) {{ return x !== t; }});
                filtered = data.filter(function(d) {{ return d['in_' + t] && !d['in_' + others[0]] && !d['in_' + others[1]]; }});
            }} else if (treatments.length === 2) {{
                // Peaks in either treatment
                filtered = data.filter(function(d) {{ return d['in_' + treatments[0]] || d['in_' + treatments[1]]; }});
            }} else {{
                // All peaks
                filtered = data;
            }}

            if (currentVizType === 'bars') {{
                if (treatments.length === 2) {{
                    renderBars(container, filtered, treatments[0], treatments[1], treatmentColors[treatments[0]], treatmentColors[treatments[1]]);
                }} else {{
                    container.append('p').style('color', '#666').style('font-size', '0.9em').text('Fold change bars require exactly 2 treatments selected');
                }}
            }} else if (currentVizType === 'bubble') {{
                renderBubble(container, filtered, treatments);
            }}
        }}

        function renderScatter(container, data, t1, t2, color1, color2) {{
            var width = 320, height = 280;
            var margin = {{ top: 20, right: 20, bottom: 40, left: 50 }};

            var svg = container.append('svg')
                .attr('width', width)
                .attr('height', height)
                .attr('viewBox', '0 0 ' + width + ' ' + height)
                .style('max-width', '100%')
                .style('height', 'auto');

            // Get max values for scales (use log scale)
            var maxVal = Math.max(
                d3.max(data, function(d) {{ return d[t1] || 1; }}),
                d3.max(data, function(d) {{ return d[t2] || 1; }})
            );

            var xScale = d3.scaleLog().domain([1, maxVal]).range([margin.left, width - margin.right]);
            var yScale = d3.scaleLog().domain([1, maxVal]).range([height - margin.bottom, margin.top]);

            // Diagonal line (equal abundance)
            svg.append('line')
                .attr('x1', margin.left).attr('y1', height - margin.bottom)
                .attr('x2', width - margin.right).attr('y2', margin.top)
                .attr('stroke', '#e5e7eb').attr('stroke-width', 1).attr('stroke-dasharray', '4');

            // Points
            svg.selectAll('circle')
                .data(data)
                .enter()
                .append('circle')
                .attr('cx', function(d) {{ return xScale(Math.max(d[t1] || 1, 1)); }})
                .attr('cy', function(d) {{ return yScale(Math.max(d[t2] || 1, 1)); }})
                .attr('r', 4)
                .attr('fill', function(d) {{
                    if (d[t1] > 0 && d[t2] === 0) return color1;
                    if (d[t2] > 0 && d[t1] === 0) return color2;
                    return '#8b5cf6'; // purple for shared
                }})
                .attr('opacity', 0.6)
                .append('title')
                .text(function(d) {{
                    return d.compound + '\\n' + t1 + ': ' + (d[t1] ? d[t1].toExponential(1) : '0') + '\\n' + t2 + ': ' + (d[t2] ? d[t2].toExponential(1) : '0');
                }});

            // Axes labels
            svg.append('text').attr('x', width/2).attr('y', height - 5).attr('text-anchor', 'middle').attr('font-size', '11px').attr('fill', color1).text(t1.charAt(0).toUpperCase() + t1.slice(1) + ' →');
            svg.append('text').attr('transform', 'rotate(-90)').attr('x', -height/2).attr('y', 12).attr('text-anchor', 'middle').attr('font-size', '11px').attr('fill', color2).text(t2.charAt(0).toUpperCase() + t2.slice(1) + ' →');

            document.getElementById('viz-info').innerHTML = '<span style="color:' + color1 + '">●</span> Only in ' + t1 + ' &nbsp; <span style="color:' + color2 + '">●</span> Only in ' + t2 + ' &nbsp; <span style="color:#8b5cf6">●</span> In both (off-diagonal = different levels)';
        }}

        function renderBars(container, data, t1, t2, color1, color2) {{
            var width = 600, height = 520;

            // Calculate fold change and sort
            var withFC = data.map(function(d) {{
                var v1 = d[t1] || 0.1, v2 = d[t2] || 0.1;
                var fc = v1 > v2 ? v1/v2 : -v2/v1;
                return {{ compound: d.compound, mz: d.mz, fc: fc, t1val: d[t1], t2val: d[t2] }};
            }}).filter(function(d) {{ return Math.abs(d.fc) > 2; }}) // Only show >2x differences
              .sort(function(a, b) {{ return Math.abs(b.fc) - Math.abs(a.fc); }})
              .slice(0, 20);

            var svg = container.append('svg').attr('width', width).attr('height', height).attr('viewBox', '0 0 ' + width + ' ' + height).style('max-width', '100%').style('height', 'auto');

            if (withFC.length === 0) {{
                svg.append('text').attr('x', width/2).attr('y', height/2).attr('text-anchor', 'middle').attr('fill', '#666').text('No peaks with >2x difference');
                return;
            }}

            var barHeight = Math.min(12, (height - 30) / withFC.length);
            var maxFC = d3.max(withFC, function(d) {{ return Math.abs(d.fc); }});
            var xScale = d3.scaleLinear().domain([-maxFC, maxFC]).range([60, width - 10]);

            withFC.forEach(function(d, i) {{
                var y = i * barHeight + 15;
                var barColor = d.fc > 0 ? color1 : color2;

                // Bar
                svg.append('rect')
                    .attr('x', d.fc > 0 ? xScale(0) : xScale(d.fc))
                    .attr('y', y)
                    .attr('width', Math.abs(xScale(d.fc) - xScale(0)))
                    .attr('height', barHeight - 2)
                    .attr('fill', barColor)
                    .attr('opacity', 0.7)
                    .append('title')
                    .text(d.compound + '\\nFold change: ' + d.fc.toFixed(1) + 'x');

                // Label
                var label = d.mz ? parseFloat(d.mz).toFixed(1) : d.compound.substring(0, 8);
                svg.append('text')
                    .attr('x', 5)
                    .attr('y', y + barHeight/2 + 3)
                    .attr('font-size', '8px')
                    .attr('fill', '#666')
                    .text(label);
            }});

            // Center line
            svg.append('line').attr('x1', xScale(0)).attr('y1', 10).attr('x2', xScale(0)).attr('y2', height - 5).attr('stroke', '#333').attr('stroke-width', 1);

            document.getElementById('viz-info').innerHTML = 'Top peaks with >2x fold change. <span style="color:' + color1 + '">◀ Higher in ' + t1 + '</span> | <span style="color:' + color2 + '">Higher in ' + t2 + ' ▶</span>';
        }}

        // COMPOUND CLOUD - circles sized by abundance
        function renderCloud(container, data, treatments) {{
            var width = 320, height = 280;
            var svg = container.append('svg').attr('width', width).attr('height', height).attr('viewBox', '0 0 ' + width + ' ' + height).style('max-width', '100%').style('height', 'auto');

            if (data.length === 0) {{
                svg.append('text').attr('x', width/2).attr('y', height/2).attr('text-anchor', 'middle').attr('fill', '#666').text('No peaks to display');
                return;
            }}

            // Sort by max abundance and take top 100
            var sorted = data.slice().sort(function(a, b) {{
                var maxA = Math.max(a.drought || 0, a.ambient || 0, a.watered || 0);
                var maxB = Math.max(b.drought || 0, b.ambient || 0, b.watered || 0);
                return maxB - maxA;
            }}).slice(0, 100);

            // Determine dominant treatment for color
            function getDominantColor(d) {{
                var vals = [
                    {{ t: 'drought', v: d.drought || 0 }},
                    {{ t: 'ambient', v: d.ambient || 0 }},
                    {{ t: 'watered', v: d.watered || 0 }}
                ].filter(function(x) {{ return treatments.indexOf(x.t) >= 0; }});
                vals.sort(function(a, b) {{ return b.v - a.v; }});
                return treatmentColors[vals[0].t];
            }}

            // Use D3 pack layout for circles
            var pack = d3.pack()
                .size([width - 10, height - 30])
                .padding(2);

            var root = d3.hierarchy({{ children: sorted }})
                .sum(function(d) {{ return Math.max(d.drought || 0, d.ambient || 0, d.watered || 0); }});

            pack(root);

            // Draw circles
            var nodes = svg.selectAll('g')
                .data(root.leaves())
                .enter()
                .append('g')
                .attr('transform', function(d) {{ return 'translate(' + (d.x + 5) + ',' + (d.y + 15) + ')'; }});

            nodes.append('circle')
                .attr('r', function(d) {{ return d.r; }})
                .attr('fill', function(d) {{ return getDominantColor(d.data); }})
                .attr('opacity', 0.75)
                .attr('stroke', '#fff')
                .attr('stroke-width', 1)
                .style('cursor', 'pointer');

            // Add m/z labels to larger circles
            nodes.filter(function(d) {{ return d.r > 12; }})
                .append('text')
                .attr('text-anchor', 'middle')
                .attr('dy', '0.3em')
                .attr('font-size', function(d) {{ return Math.min(d.r * 0.7, 10) + 'px'; }})
                .attr('fill', 'white')
                .attr('font-weight', 'bold')
                .text(function(d) {{ return d.data.mz ? parseFloat(d.data.mz).toFixed(1) : ''; }});

            // Tooltips
            nodes.append('title')
                .text(function(d) {{
                    var data = d.data;
                    return data.compound + (data.formula ? '\\nFormula: ' + data.formula : '') + '\\nm/z: ' + (data.mz || 'N/A') + '\\nRT: ' + (data.rt || 'N/A') + '\\nDrought: ' + (data.drought ? data.drought.toExponential(1) : '0') + '\\nAmbient: ' + (data.ambient ? data.ambient.toExponential(1) : '0') + '\\nWatered: ' + (data.watered ? data.watered.toExponential(1) : '0');
                }});

            document.getElementById('viz-info').innerHTML = 'Circle size = abundance, color = dominant treatment. Hover for details.';
        }}

        // PIE CHART - distribution of peaks
        function renderPie(container, filtered, treatments, allData) {{
            var width = 320, height = 280;
            var radius = Math.min(width, height) / 2 - 40;

            var svg = container.append('svg').attr('width', width).attr('height', height)
                .attr('viewBox', '0 0 ' + width + ' ' + height).style('max-width', '100%').style('height', 'auto')
                .append('g').attr('transform', 'translate(' + width/2 + ',' + height/2 + ')');

            // Calculate categories based on selection
            var pieData = [];
            if (treatments.length === 2) {{
                var t1 = treatments[0], t2 = treatments[1];
                var onlyT1 = filtered.filter(function(d) {{ return d['in_' + t1] && !d['in_' + t2]; }}).length;
                var onlyT2 = filtered.filter(function(d) {{ return d['in_' + t2] && !d['in_' + t1]; }}).length;
                var both = filtered.filter(function(d) {{ return d['in_' + t1] && d['in_' + t2]; }}).length;
                pieData = [
                    {{ label: 'Only ' + t1, value: onlyT1, color: treatmentColors[t1] }},
                    {{ label: 'Only ' + t2, value: onlyT2, color: treatmentColors[t2] }},
                    {{ label: 'Shared', value: both, color: '#8b5cf6' }}
                ];
            }} else if (treatments.length === 1) {{
                pieData = [{{ label: treatments[0] + ' unique', value: filtered.length, color: treatmentColors[treatments[0]] }}];
            }} else {{
                // 3 treatments - show unique vs shared
                var unique = filtered.filter(function(d) {{
                    var count = (d.in_drought ? 1 : 0) + (d.in_ambient ? 1 : 0) + (d.in_watered ? 1 : 0);
                    return count === 1;
                }}).length;
                var shared2 = filtered.filter(function(d) {{
                    var count = (d.in_drought ? 1 : 0) + (d.in_ambient ? 1 : 0) + (d.in_watered ? 1 : 0);
                    return count === 2;
                }}).length;
                var shared3 = filtered.filter(function(d) {{
                    return d.in_drought && d.in_ambient && d.in_watered;
                }}).length;
                pieData = [
                    {{ label: 'Unique to 1', value: unique, color: '#f59e0b' }},
                    {{ label: 'Shared by 2', value: shared2, color: '#8b5cf6' }},
                    {{ label: 'All three', value: shared3, color: '#10b981' }}
                ];
            }}

            pieData = pieData.filter(function(d) {{ return d.value > 0; }});

            var pie = d3.pie().value(function(d) {{ return d.value; }}).sort(null);
            var arc = d3.arc().innerRadius(0).outerRadius(radius);
            var labelArc = d3.arc().innerRadius(radius * 0.6).outerRadius(radius * 0.6);

            var arcs = svg.selectAll('arc').data(pie(pieData)).enter().append('g');

            arcs.append('path')
                .attr('d', arc)
                .attr('fill', function(d) {{ return d.data.color; }})
                .attr('stroke', 'white')
                .attr('stroke-width', 2)
                .attr('opacity', 0.85);

            arcs.append('text')
                .attr('transform', function(d) {{ return 'translate(' + labelArc.centroid(d) + ')'; }})
                .attr('text-anchor', 'middle')
                .attr('font-size', '10px')
                .attr('fill', 'white')
                .attr('font-weight', 'bold')
                .text(function(d) {{ return d.data.value; }});

            // Legend
            var legend = svg.append('g').attr('transform', 'translate(' + (-width/2 + 10) + ',' + (radius + 15) + ')');
            pieData.forEach(function(d, i) {{
                legend.append('rect').attr('x', i * 100).attr('y', 0).attr('width', 12).attr('height', 12).attr('fill', d.color);
                legend.append('text').attr('x', i * 100 + 16).attr('y', 10).attr('font-size', '9px').text(d.label);
            }});

            document.getElementById('viz-info').innerHTML = 'Peak distribution across treatments';
        }}

        // BUBBLE CHART - each compound is a bubble
        function renderBubble(container, data, treatments) {{
            var width = 600, height = 520;
            var svg = container.append('svg').attr('width', width).attr('height', height).attr('viewBox', '0 0 ' + width + ' ' + height).style('max-width', '100%').style('height', 'auto');

            if (data.length === 0) {{
                svg.append('text').attr('x', width/2).attr('y', height/2).attr('text-anchor', 'middle').attr('fill', '#666').text('No peaks to display');
                return;
            }}

            // Helper to get average abundance from selected treatments
            function getSelectedAvg(d) {{
                var vals = treatments.map(function(t) {{ return d[t] || 0; }});
                var sum = vals.reduce(function(a, b) {{ return a + b; }}, 0);
                return sum / vals.length;
            }}

            // Take top 100 by abundance (using selected treatments)
            var sorted = data.slice().sort(function(a, b) {{
                return getSelectedAvg(b) - getSelectedAvg(a);
            }}).slice(0, 100);

            // Pack layout - size based on average of selected treatments
            var pack = d3.pack().size([width - 20, height - 40]).padding(2);

            var root = d3.hierarchy({{ children: sorted }})
                .sum(function(d) {{ return getSelectedAvg(d); }});

            pack(root);

            // Determine color by dominant treatment among SELECTED treatments only
            function getColor(d) {{
                if (!d.data.compound) return '#ccc';
                var vals = treatments.map(function(t) {{
                    return {{ t: t, v: d.data[t] || 0 }};
                }});
                vals.sort(function(a, b) {{ return b.v - a.v; }});
                return treatmentColors[vals[0].t];
            }}

            var nodes = svg.selectAll('g')
                .data(root.leaves())
                .enter()
                .append('g')
                .attr('transform', function(d) {{ return 'translate(' + (d.x + 10) + ',' + (d.y + 20) + ')'; }});

            nodes.append('circle')
                .attr('r', function(d) {{ return d.r; }})
                .attr('fill', getColor)
                .attr('opacity', 0.75)
                .attr('stroke', '#fff')
                .attr('stroke-width', 1)
                .style('cursor', 'pointer');

            // Add m/z labels to larger circles
            nodes.filter(function(d) {{ return d.r > 12; }})
                .append('text')
                .attr('text-anchor', 'middle')
                .attr('dy', '0.3em')
                .attr('font-size', function(d) {{ return Math.min(d.r * 0.7, 10) + 'px'; }})
                .attr('fill', 'white')
                .attr('font-weight', 'bold')
                .text(function(d) {{ return d.data.mz ? parseFloat(d.data.mz).toFixed(1) : ''; }});

            // Tooltips
            nodes.append('title')
                .text(function(d) {{
                    if (!d.data.compound) return '';
                    return d.data.compound + (d.data.formula ? '\\nFormula: ' + d.data.formula : '') + '\\nm/z: ' + (d.data.mz || 'N/A') + '\\nRT: ' + (d.data.rt || 'N/A') + '\\nDrought: ' + (d.data.drought ? d.data.drought.toExponential(1) : '0') + '\\nAmbient: ' + (d.data.ambient ? d.data.ambient.toExponential(1) : '0') + '\\nWatered: ' + (d.data.watered ? d.data.watered.toExponential(1) : '0');
                }});

            document.getElementById('viz-info').innerHTML = 'Bubble size = average abundance across selected treatments, color = dominant treatment. Hover for details.';
        }}

        // Initialize when priority tab is shown
        document.querySelector('[onclick*=\"priority\"]').addEventListener('click', function() {{
            setTimeout(function() {{
                updateToggleButtons();
                updateComparison();
                updateVisualization();
            }}, 100);
        }});

        // Diversity charts
        function renderDiversityCharts() {{
            // Clear existing charts before re-rendering
            document.getElementById('richness-chart').innerHTML = '';
            document.getElementById('shannon-chart').innerHTML = '';

            const treatments = ['Drought', 'Ambient', 'Watered'];
            const colors = {{'Drought': '#ef4444', 'Ambient': '#3b82f6', 'Watered': '#22c55e'}};
            const margin = {{top: 20, right: 30, bottom: 40, left: 60}};
            const width = 450 - margin.left - margin.right;
            const height = 280 - margin.top - margin.bottom;

            // Richness chart
            const richnessData = [];
            ['Leaf', 'Root'].forEach(tissue => {{
                treatments.forEach(t => {{
                    richnessData.push({{
                        tissue: tissue,
                        treatment: t,
                        mean: chemicalRichness[tissue][t].mean,
                        se: chemicalRichness[tissue][t].se
                    }});
                }});
            }});

            const richnessSvg = d3.select('#richness-chart')
                .append('svg')
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom)
                .append('g')
                .attr('transform', `translate(${{margin.left}},${{margin.top}})`);

            const x0 = d3.scaleBand().domain(['Leaf', 'Root']).rangeRound([0, width]).paddingInner(0.1);
            const x1 = d3.scaleBand().domain(treatments).rangeRound([0, x0.bandwidth()]).padding(0.05);
            const y = d3.scaleLinear().domain([0, d3.max(richnessData, d => d.mean + d.se) * 1.1]).nice().rangeRound([height, 0]);

            richnessSvg.append('g').attr('transform', `translate(0,${{height}})`).call(d3.axisBottom(x0));
            richnessSvg.append('g').call(d3.axisLeft(y));
            richnessSvg.append('text').attr('x', width/2).attr('y', height + 35).attr('text-anchor', 'middle').text('Tissue');
            richnessSvg.append('text').attr('transform', 'rotate(-90)').attr('y', -45).attr('x', -height/2).attr('text-anchor', 'middle').text('Peak Count');

            ['Leaf', 'Root'].forEach(tissue => {{
                const tissueData = richnessData.filter(d => d.tissue === tissue);
                const g = richnessSvg.append('g').attr('transform', `translate(${{x0(tissue)}},0)`);

                g.selectAll('rect')
                    .data(tissueData)
                    .enter().append('rect')
                    .attr('x', d => x1(d.treatment))
                    .attr('y', d => y(d.mean))
                    .attr('width', x1.bandwidth())
                    .attr('height', d => height - y(d.mean))
                    .attr('fill', d => colors[d.treatment]);

                // Error bars
                g.selectAll('.error')
                    .data(tissueData)
                    .enter().append('line')
                    .attr('x1', d => x1(d.treatment) + x1.bandwidth()/2)
                    .attr('x2', d => x1(d.treatment) + x1.bandwidth()/2)
                    .attr('y1', d => y(d.mean - d.se))
                    .attr('y2', d => y(d.mean + d.se))
                    .attr('stroke', '#333').attr('stroke-width', 1.5);
            }});

            // Shannon chart
            const shannonData = [];
            ['Leaf', 'Root'].forEach(tissue => {{
                treatments.forEach(t => {{
                    shannonData.push({{
                        tissue: tissue,
                        treatment: t,
                        mean: shannonDiversity[tissue][t].mean,
                        se: shannonDiversity[tissue][t].se
                    }});
                }});
            }});

            const shannonSvg = d3.select('#shannon-chart')
                .append('svg')
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom)
                .append('g')
                .attr('transform', `translate(${{margin.left}},${{margin.top}})`);

            const yS = d3.scaleLinear().domain([0, d3.max(shannonData, d => d.mean + d.se) * 1.1]).nice().rangeRound([height, 0]);

            shannonSvg.append('g').attr('transform', `translate(0,${{height}})`).call(d3.axisBottom(x0));
            shannonSvg.append('g').call(d3.axisLeft(yS).ticks(5));
            shannonSvg.append('text').attr('x', width/2).attr('y', height + 35).attr('text-anchor', 'middle').text('Tissue');
            shannonSvg.append('text').attr('transform', 'rotate(-90)').attr('y', -45).attr('x', -height/2).attr('text-anchor', 'middle').text('Shannon Index (H)');

            ['Leaf', 'Root'].forEach(tissue => {{
                const tissueData = shannonData.filter(d => d.tissue === tissue);
                const g = shannonSvg.append('g').attr('transform', `translate(${{x0(tissue)}},0)`);

                g.selectAll('rect')
                    .data(tissueData)
                    .enter().append('rect')
                    .attr('x', d => x1(d.treatment))
                    .attr('y', d => yS(d.mean))
                    .attr('width', x1.bandwidth())
                    .attr('height', d => height - yS(d.mean))
                    .attr('fill', d => colors[d.treatment]);

                g.selectAll('.error')
                    .data(tissueData)
                    .enter().append('line')
                    .attr('x1', d => x1(d.treatment) + x1.bandwidth()/2)
                    .attr('x2', d => x1(d.treatment) + x1.bandwidth()/2)
                    .attr('y1', d => yS(d.mean - d.se))
                    .attr('y2', d => yS(d.mean + d.se))
                    .attr('stroke', '#333').attr('stroke-width', 1.5);
            }});

            // Legend
            const legend = richnessSvg.append('g').attr('transform', `translate(${{width - 100}}, 0)`);
            treatments.forEach((t, i) => {{
                legend.append('rect').attr('x', 0).attr('y', i * 18).attr('width', 14).attr('height', 14).attr('fill', colors[t]);
                legend.append('text').attr('x', 18).attr('y', i * 18 + 11).text(t).style('font-size', '11px');
            }});
        }}

        // Initialize diversity charts when tab is shown
        document.querySelector('[onclick*=\"diversity\"]').addEventListener('click', function() {{
            setTimeout(function() {{
                renderDiversityCharts();
            }}, 100);
        }});

    </script>
</body>
</html>'''

    # Write to file
    output_path = Path(
        r"C:\Users\austi\PROJECTS\Dashboards\metabolomics\index.html"
    )
    output_path.write_text(html, encoding="utf-8")
    print(f"Report saved to: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
    for label, result in [("Normalized", norm), ("Unnormalized", unnorm)]:
        print(f"\n{label} filtering summary:")
        print(f"  Original peaks: {result['total']:,}")
        print(f"  After blank filter: {len(result['kept_blank']):,} ({result['total'] - len(result['kept_blank']):,} removed)")
        print(f"  After 80% filter: {len(result['kept_80']):,} ({100*len(result['kept_80'])/result['total']:.1f}% of original)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
