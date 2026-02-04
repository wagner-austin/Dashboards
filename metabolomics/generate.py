"""Generate HTML report with embedded interactive data tables."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

import polars as pl


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
    df: pl.DataFrame, sample_cols: list[str], blank_cols: list[str], threshold: float = 3.0
) -> tuple[set[str], dict]:
    """
    Filter peaks based on blank subtraction.
    A peak is kept if sample_avg >= threshold * blank_avg in at least one sample.
    Returns (set of kept compounds, stats dict).
    """
    compounds = df["Compound"].to_list()
    kept: set[str] = set()
    stats = {
        "sample_only": 0,  # Peak in samples but not blanks
        "both_keep": 0,    # Peak in both, sample >= 3x blank
        "both_discard": 0, # Peak in both, sample < 3x blank
        "blank_only": 0,   # Peak only in blanks
        "neither": 0,      # Peak in neither
    }

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
            # Peak only in samples - keep it
            kept.add(compound)
            stats["sample_only"] += 1
        elif has_sample and has_blank:
            # Peak in both - check ratio
            sample_avg = sum(sample_vals) / len(sample_vals)
            blank_avg = sum(blank_vals) / len(blank_vals)
            if sample_avg >= threshold * blank_avg:
                kept.add(compound)
                stats["both_keep"] += 1
            else:
                stats["both_discard"] += 1
        elif has_blank and not has_sample:
            stats["blank_only"] += 1
        else:
            stats["neither"] += 1

    stats["total_clean"] = stats["sample_only"] + stats["both_keep"]
    return kept, stats


def get_peaks_in_group(df: pl.DataFrame, cols: list[str]) -> set[str]:
    """Get peaks that have non-zero signal in any column of the group."""
    peaks = set()
    for col in cols:
        if col in df.columns:
            temp = df.select(["Compound", col]).drop_nulls()
            temp = temp.filter(pl.col(col) > 0)
            peaks.update(temp["Compound"].to_list())
    return peaks


def df_to_json(df: pl.DataFrame, sample_cols: list[str]) -> str:
    """Convert DataFrame to JSON for DataTables."""
    records = []
    for row in df.iter_rows(named=True):
        record = {"Compound": row["Compound"]}
        for col in sample_cols:
            val = row.get(col)
            if val is not None:
                record[col] = round(float(val), 2) if isinstance(val, (int, float)) else val
            else:
                record[col] = None
        records.append(record)
    return json.dumps(records)


def main() -> int:
    # Use local copy of labeled data
    data_path = Path(__file__).parent / "Emily_Data_Pruned_Labeled.xlsx"

    print("Loading data...")
    df = pl.read_excel(
        data_path,
        sheet_name="Normalized",
        infer_schema_length=None,
    )

    # Build sample columns from treatment definitions
    SAMPLE_COLS = []
    for tissue_treatments in TREATMENTS.values():
        for samples in tissue_treatments.values():
            SAMPLE_COLS.extend(samples)

    # Build tissue-specific sample lists
    LEAF_SAMPLES = []
    ROOT_SAMPLES = []
    for treatment, samples in TREATMENTS["Leaf"].items():
        LEAF_SAMPLES.extend(samples)
    for treatment, samples in TREATMENTS["Root"].items():
        ROOT_SAMPLES.extend(samples)

    # Filter to blanks that exist in the data
    LEAF_BLANKS = [c for c in TISSUE_BLANKS["Leaf"] if c in df.columns]
    ROOT_BLANKS = [c for c in TISSUE_BLANKS["Root"] if c in df.columns]

    print("\n" + "=" * 60)
    print("BLANK FILTERING CONFIGURATION")
    print("=" * 60)
    print(f"\nLEAF samples ({len(LEAF_SAMPLES)}): {', '.join(LEAF_SAMPLES)}")
    print(f"LEAF blanks ({len(LEAF_BLANKS)}): {', '.join(LEAF_BLANKS)}")
    print(f"\nROOT samples ({len(ROOT_SAMPLES)}): {', '.join(ROOT_SAMPLES)}")
    print(f"ROOT blanks ({len(ROOT_BLANKS)}): {', '.join(ROOT_BLANKS)}")
    print("=" * 60 + "\n")

    print("Running filtering...")

    total = df["Compound"].n_unique()

    # Step 1: Tissue-specific blank filtering
    print("Step 1: Tissue-specific blank filtering...")

    # Filter leaf samples with leaf blanks
    print(f"  Filtering LEAF samples with {len(LEAF_BLANKS)} leaf blanks...")
    kept_leaf, leaf_blank_stats = filter_blanks(df, LEAF_SAMPLES, LEAF_BLANKS, threshold=3.0)
    print(f"    Leaf: kept {len(kept_leaf):,} peaks, removed {leaf_blank_stats['both_discard']:,} contamination")

    # Filter root samples with root blanks
    print(f"  Filtering ROOT samples with {len(ROOT_BLANKS)} root blanks...")
    kept_root, root_blank_stats = filter_blanks(df, ROOT_SAMPLES, ROOT_BLANKS, threshold=3.0)
    print(f"    Root: kept {len(kept_root):,} peaks, removed {root_blank_stats['both_discard']:,} contamination")

    # Union of peaks kept from both tissues
    kept_blank = kept_leaf | kept_root
    blank_stats = {
        "sample_only": leaf_blank_stats["sample_only"] + root_blank_stats["sample_only"],
        "both_keep": leaf_blank_stats["both_keep"] + root_blank_stats["both_keep"],
        "both_discard": leaf_blank_stats["both_discard"] + root_blank_stats["both_discard"],
        "blank_only": leaf_blank_stats["blank_only"] + root_blank_stats["blank_only"],
        "neither": leaf_blank_stats["neither"] + root_blank_stats["neither"],
        "total_clean": len(kept_blank),
    }
    df_blank_filtered = df.filter(pl.col("Compound").is_in(list(kept_blank)))
    print(f"  Combined: {len(kept_blank):,} unique peaks after tissue-specific blank filtering")

    # Step 2: 80% cumulative filtering on blank-filtered data
    print("Step 2: 80% cumulative filtering...")
    kept_80: set[str] = set()
    sample_data_80: list[tuple[str, str, int, float]] = []

    for col in SAMPLE_COLS:
        if col not in df_blank_filtered.columns:
            continue
        k80, n80, pct80 = filter_cumulative(df_blank_filtered, col, 0.80)
        kept_80.update(k80)
        # Determine tissue from column name (e.g., "BL - Drought" -> Leaf, "AR - Drought" -> Root)
        tissue = "Leaf" if col[1] == "L" else "Root"
        sample_data_80.append((col, tissue, n80, pct80 * 100))

    # Create final filtered DataFrame
    print("Creating filtered dataset...")
    available_cols = [c for c in SAMPLE_COLS if c in df_blank_filtered.columns]
    df_80 = df_blank_filtered.filter(pl.col("Compound").is_in(list(kept_80))).select(["Compound"] + available_cols)

    # Convert to JSON
    print("Converting to JSON...")
    json_80 = df_to_json(df_80, available_cols)

    # Calculate stats
    leaf_80 = [x for x in sample_data_80 if x[1] == "Leaf"]
    root_80 = [x for x in sample_data_80 if x[1] == "Root"]

    # Venn diagram calculations - peaks by treatment
    print("Calculating treatment overlaps...")
    venn_data = {}
    treatment_peaks = {}  # Store actual peak sets for priority analysis
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
            # Unique to each treatment (not in the other two)
            "drought_only": len(drought_peaks - ambient_peaks - watered_peaks),
            "ambient_only": len(ambient_peaks - drought_peaks - watered_peaks),
            "watered_only": len(watered_peaks - drought_peaks - ambient_peaks),
            # Shared between pairs (but not all three)
            "drought_ambient": len((drought_peaks & ambient_peaks) - watered_peaks),
            "drought_watered": len((drought_peaks & watered_peaks) - ambient_peaks),
            "ambient_watered": len((ambient_peaks & watered_peaks) - drought_peaks),
            # Shared by all three
            "all_three": len(drought_peaks & ambient_peaks & watered_peaks),
        }
        treatment_peaks[tissue] = {
            "drought_only": drought_peaks - ambient_peaks - watered_peaks,
            "ambient_only": ambient_peaks - drought_peaks - watered_peaks,
            "watered_only": watered_peaks - drought_peaks - ambient_peaks,
        }

    # Priority peaks analysis - get ALL peaks with treatment abundances
    print("Building priority peaks data...")
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

            # Get average abundance AND occurrence count for each treatment
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

            # Skip if not present in any treatment for this tissue
            if abundances["drought"] == 0 and abundances["ambient"] == 0 and abundances["watered"] == 0:
                continue

            # Determine which treatments have this peak
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

            all_peaks_data[tissue].append({
                "compound": compound,
                "mz": meta_row.get("m/z", ""),
                "rt": meta_row.get("Retention time (min)", ""),
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

        # Sort by max abundance across treatments
        all_peaks_data[tissue].sort(key=lambda x: max(x["drought"], x["ambient"], x["watered"]), reverse=True)

    all_peaks_json = json.dumps(all_peaks_data)

    print("Generating HTML...")

    # Build column definitions for DataTables
    col_defs = [{"data": "Compound", "title": "Compound"}]
    for col in available_cols:
        col_defs.append({"data": col, "title": col})
    col_defs_json = json.dumps(col_defs)

    # Build per-sample table rows with sample numbers (bold numbers)
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
            --gray-600: #4b5563;
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
            grid-template-columns: 1fr 1fr;
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
    </style>
</head>
<body>
    <div class="header-container">
        <div class="header">
            <h1>Metabolomics Filtering Analysis</h1>
        </div>

        <div class="tabs">
        <button class="tab active" onclick="showTab('overview')">Overview</button>
        <button class="tab" onclick="showTab('priority')">Priority Peaks</button>
        <button class="tab" onclick="showTab('venn')">Treatment Overlap</button>
        <button class="tab" onclick="showTab('methods')">Methods</button>
        <button class="tab" onclick="showTab('data80')">Filtered Data ({len(kept_80):,})</button>
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
                <div class="value">{total:,} <span style="font-size: 0.5em; font-weight: normal;">Peaks</span></div>
                <div class="subtext">unique peaks before filtering</div>
            </div>
            <div class="card" style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border-color: #f87171;">
                <h4>After Blank Filter</h4>
                <div class="value">{len(kept_blank):,} <span style="font-size: 0.5em; font-weight: normal;">Peaks</span></div>
                <div class="subtext">{blank_stats['both_discard']:,} contamination peaks removed</div>
            </div>
            <div class="card highlight">
                <h4>Final (80% Filter)</h4>
                <div class="value">{len(kept_80):,} <span style="font-size: 0.5em; font-weight: normal;">Peaks</span></div>
                <div class="subtext">{100*len(kept_80)/total:.1f}% of original kept</div>
            </div>
        </div>

        <div class="alert alert-success" style="margin: 1.5rem 0;">
            <strong>Two-Step Filtering:</strong> First, we remove peaks that appear in blanks (contamination). Then we apply 80% cumulative signal filtering to keep only the most significant peaks.
        </div>

        <h3>Blank Filtering Results</h3>
        <table class="info-table">
            <tr><th>Category</th><th>Count</th><th>Description</th></tr>
            <tr><td class="kept">Sample Only</td><td>{blank_stats['sample_only']:,}</td><td>Peaks only in samples, not in blanks (kept)</td></tr>
            <tr><td class="kept">Above 3x Blank</td><td>{blank_stats['both_keep']:,}</td><td>Sample signal ≥ 3x blank signal (kept)</td></tr>
            <tr><td class="filtered">Contamination</td><td>{blank_stats['both_discard']:,}</td><td>Sample signal &lt; 3x blank signal (removed)</td></tr>
            <tr><td>Blank Only</td><td>{blank_stats['blank_only']:,}</td><td>Peaks only in blanks (not in samples)</td></tr>
        </table>

        <h3>Source Data</h3>
        <ul>
            <li><strong>File:</strong> Emily_Data_Pruned_Labeled.xlsx</li>
            <li><strong>Sheet:</strong> Normalized</li>
            <li><strong>Samples:</strong> 23 total (12 Leaf, 11 Root) - Emily's samples only</li>
            <li><strong>Leaf blanks:</strong> {', '.join(LEAF_BLANKS)}</li>
            <li><strong>Root blanks:</strong> {', '.join(ROOT_BLANKS)}</li>
        </ul>

        <div class="alert alert-info" style="margin: 1.5rem 0;">
            <strong>Key Finding:</strong> Root tissue reaches 80% much faster (avg ~{sum(x[2] for x in root_80)/len(root_80):,.0f} peaks) than leaf tissue (avg ~{sum(x[2] for x in leaf_80)/len(leaf_80):,.0f} peaks). This means roots have a few dominant compounds while leaves have signal spread across more compounds.
        </div>

        <h3>Leaf vs Root</h3>
        <p>Root samples have more concentrated signal - fewer peaks make up 80% of the total.</p>

        <div class="summary-cards">
            <div class="card leaf">
                <h4>Leaf Avg</h4>
                <div class="value">{sum(x[2] for x in leaf_80)/len(leaf_80):,.0f}</div>
                <div class="subtext">peaks to reach 80%</div>
            </div>
            <div class="card root">
                <h4>Root Avg</h4>
                <div class="value">{sum(x[2] for x in root_80)/len(root_80):,.0f}</div>
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
                    {leaf_rows}
                </table>
            </div>
            <div>
                <h4 style="color: var(--root-color); padding: 0.5rem; background: var(--root-bg); border-radius: 6px; display: inline-block;">Root Tissue (11 samples)</h4>
                <table class="info-table" style="margin-top: 0.75rem;">
                    <tr style="background: var(--root-bg);"><th>#</th><th>ID</th><th>Peaks Needed</th><th>Smallest Peak Kept</th></tr>
                    {root_rows}
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
                <button class="viz-toggle" data-viz="treemap" onclick="setVizType('treemap')">Treemap</button>
                <button class="viz-toggle" data-viz="bars" onclick="setVizType('bars')">Fold Change Bars</button>
            </div>
            <div class="two-col">
                <div>
                    <h4 style="color: var(--root-color); margin-bottom: 0.5rem;">Root</h4>
                    <div id="viz-root" style="background: white; border-radius: 8px; padding: 0.5rem; min-height: 450px;"></div>
                </div>
                <div>
                    <h4 style="color: var(--leaf-color); margin-bottom: 0.5rem;">Leaf</h4>
                    <div id="viz-leaf" style="background: white; border-radius: 8px; padding: 0.5rem; min-height: 450px;"></div>
                </div>
            </div>
            <p id="viz-info" style="color: var(--gray-600); font-size: 0.85em; margin-top: 0.5rem; text-align: center;"></p>
        </div>

        <div class="two-col" style="margin-top: 1rem;">
            <div>
                <h3 style="color: var(--root-color); margin-bottom: 1rem;">
                    Root Tissue <span id="root-peak-count" style="font-weight: normal; font-size: 0.8em;"></span>
                </h3>
                <div id="priority-root" style="background: white; border-radius: 8px; padding: 1rem; max-height: 500px; overflow-y: auto;"></div>
            </div>
            <div>
                <h3 style="color: var(--leaf-color); margin-bottom: 1rem;">
                    Leaf Tissue <span id="leaf-peak-count" style="font-weight: normal; font-size: 0.8em;"></span>
                </h3>
                <div id="priority-leaf" style="background: white; border-radius: 8px; padding: 1rem; max-height: 500px; overflow-y: auto;"></div>
            </div>
        </div>

        <div class="alert alert-info" style="margin-top: 1.5rem;">
            <strong>m/z</strong> = mass-to-charge ratio (use in chemcalc.org to estimate molecular formula)
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
                <h3 style="color: var(--leaf-color); margin-top: 0;">Leaf Tissue ({venn_data['Leaf']['all']:,} peaks)</h3>
                <table class="info-table">
                    <tr><th>Region</th><th>Peaks</th><th>Meaning</th></tr>
                    <tr><td><strong style="color: #dc2626;">Drought Only</strong></td><td><strong>{venn_data['Leaf']['drought_only']:,}</strong></td><td>Only in drought, not ambient or watered</td></tr>
                    <tr><td><strong style="color: #2563eb;">Ambient Only</strong></td><td><strong>{venn_data['Leaf']['ambient_only']:,}</strong></td><td>Only in ambient, not drought or watered</td></tr>
                    <tr><td><strong style="color: #16a34a;">Watered Only</strong></td><td><strong>{venn_data['Leaf']['watered_only']:,}</strong></td><td>Only in watered, not drought or ambient</td></tr>
                    <tr><td>Drought + Ambient</td><td><strong>{venn_data['Leaf']['drought_ambient']:,}</strong></td><td>Shared by D &amp; A, not W</td></tr>
                    <tr><td>Drought + Watered</td><td><strong>{venn_data['Leaf']['drought_watered']:,}</strong></td><td>Shared by D &amp; W, not A</td></tr>
                    <tr><td>Ambient + Watered</td><td><strong>{venn_data['Leaf']['ambient_watered']:,}</strong></td><td>Shared by A &amp; W, not D</td></tr>
                    <tr><td><strong>All Three</strong></td><td><strong>{venn_data['Leaf']['all_three']:,}</strong></td><td>Present in all treatments (core metabolites)</td></tr>
                </table>
                <div class="alert alert-info" style="margin-top: 1rem;">
                    <strong>{100*venn_data['Leaf']['all_three']/venn_data['Leaf']['all']:.1f}%</strong> of leaf peaks are shared across all treatments
                </div>
            </div>

            <div class="method-section" style="background: linear-gradient(135deg, var(--root-bg) 0%, #fef3c7 100%); border-color: var(--root-color);">
                <h3 style="color: var(--root-color); margin-top: 0;">Root Tissue ({venn_data['Root']['all']:,} peaks)</h3>
                <table class="info-table">
                    <tr><th>Region</th><th>Peaks</th><th>Meaning</th></tr>
                    <tr><td><strong style="color: #dc2626;">Drought Only</strong></td><td><strong>{venn_data['Root']['drought_only']:,}</strong></td><td>Only in drought, not ambient or watered</td></tr>
                    <tr><td><strong style="color: #2563eb;">Ambient Only</strong></td><td><strong>{venn_data['Root']['ambient_only']:,}</strong></td><td>Only in ambient, not drought or watered</td></tr>
                    <tr><td><strong style="color: #16a34a;">Watered Only</strong></td><td><strong>{venn_data['Root']['watered_only']:,}</strong></td><td>Only in watered, not drought or ambient</td></tr>
                    <tr><td>Drought + Ambient</td><td><strong>{venn_data['Root']['drought_ambient']:,}</strong></td><td>Shared by D &amp; A, not W</td></tr>
                    <tr><td>Drought + Watered</td><td><strong>{venn_data['Root']['drought_watered']:,}</strong></td><td>Shared by D &amp; W, not A</td></tr>
                    <tr><td>Ambient + Watered</td><td><strong>{venn_data['Root']['ambient_watered']:,}</strong></td><td>Shared by A &amp; W, not D</td></tr>
                    <tr><td><strong>All Three</strong></td><td><strong>{venn_data['Root']['all_three']:,}</strong></td><td>Present in all treatments (core metabolites)</td></tr>
                </table>
                <div class="alert alert-info" style="margin-top: 1rem;">
                    <strong>{100*venn_data['Root']['all_three']/venn_data['Root']['all']:.1f}%</strong> of root peaks are shared across all treatments
                </div>
            </div>
        </div>

        <div class="alert alert-success" style="margin-top: 2rem;">
            <strong>How to interpret:</strong> Peaks unique to a treatment (e.g., "Drought Only") are potential biomarkers for that stress condition. Peaks shared by all three are likely core metabolites present regardless of water availability.
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

            <pre>For each peak:
1. Calculate average signal across all tissue samples
2. Calculate average signal across all blank samples
3. If sample_avg >= 3x blank_avg → KEEP (real biological signal)
4. If sample_avg &lt; 3x blank_avg → REMOVE (likely contamination)
5. If peak only appears in samples (not blanks) → KEEP</pre>

            <p><strong>The 3x threshold</strong> is a standard practice in metabolomics. A peak must be at least 3 times stronger in real samples than in blanks to be considered a true biological signal rather than contamination.</p>

            <div class="alert alert-success">
                <strong>Leaf blanks ({len(LEAF_BLANKS)}):</strong> {', '.join(LEAF_BLANKS)}<br>
                <strong>Root blanks ({len(ROOT_BLANKS)}):</strong> {', '.join(ROOT_BLANKS)}
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
    </div>

    <!-- FILTERED DATA TAB -->
    <div id="data80" class="tab-content">
        <h2 style="padding: 1rem; background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-radius: 8px; margin-bottom: 0;">Filtered Metabolomics Data</h2>
        <p style="color: var(--gray-600); margin-bottom: 1.5rem; padding: 0.75rem 1rem; background: var(--gray-50); border-left: 3px solid var(--primary); font-size: 0.9rem; font-style: italic;">Two-step filtered data: blank subtraction (3x threshold) followed by 80% cumulative signal threshold.</p>
        <div class="summary-cards">
            <div class="card">
                <h4>Original Peaks</h4>
                <div class="value">{total:,}</div>
                <div class="subtext">before any filtering</div>
            </div>
            <div class="card" style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border-color: #f87171;">
                <h4>After Blank Filter</h4>
                <div class="value">{len(kept_blank):,}</div>
                <div class="subtext">{blank_stats['both_discard']:,} contamination removed</div>
            </div>
            <div class="card highlight">
                <h4>Final Peaks</h4>
                <div class="value">{len(kept_80):,}</div>
                <div class="subtext">{100*len(kept_80)/total:.1f}% of original kept</div>
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
        // Data
        const data80 = {json_80};
        const columns = {col_defs_json};

        // Tab switching
        function showTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }}

        function initTable(selector, data) {{
            $(selector).DataTable({{
                data: data,
                columns: columns,
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

        // Initialize table after page loads
        $(document).ready(function() {{
            setTimeout(function() {{
                initTable('#table80', data80);
            }}, 500);
        }});

        // All peaks data with treatment abundances
        var allPeaksData = {all_peaks_json};

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

            // Column headers
            var headerRow = container.append('div')
                .style('display', 'flex')
                .style('font-size', '0.7em')
                .style('color', '#666')
                .style('margin-bottom', '0.5rem')
                .style('padding', '0.25rem')
                .style('font-weight', '600')
                .style('border-bottom', '2px solid #e5e7eb');
            headerRow.append('div').style('width', '25px').style('text-align', 'center').text('#');
            headerRow.append('div').style('width', '140px').text('Compound');
            headerRow.append('div').style('width', '70px').style('text-align', 'right').text('m/z');
            headerRow.append('div').style('width', '35px').style('text-align', 'right').text('RT');
            headerRow.append('div').style('width', '40px').style('text-align', 'right').text('CV%');

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
            var rowContainer = container.append('div');
            filtered.slice(0, 100).forEach(function(d, i) {{
                var row = rowContainer.append('div')
                    .style('display', 'flex')
                    .style('align-items', 'center')
                    .style('padding', '0.3rem 0.25rem')
                    .style('background', i % 2 === 0 ? '#f9fafb' : 'white')
                    .style('font-size', '0.75em');

                row.append('div').style('width', '25px').style('text-align', 'center').style('color', '#999').text(i + 1);

                var name = d.compound.length > 18 ? d.compound.substring(0, 15) + '...' : d.compound;
                row.append('div').style('width', '140px').style('font-family', 'monospace').style('font-size', '0.95em').attr('title', d.compound).text(name);
                row.append('div').style('width', '70px').style('text-align', 'right').style('font-family', 'monospace').text(d.mz ? parseFloat(d.mz).toFixed(4) : '-');
                row.append('div').style('width', '35px').style('text-align', 'right').style('font-family', 'monospace').text(d.rt ? parseFloat(d.rt).toFixed(1) : '-');

                // CV% with color coding
                var cvText = d.cv ? d.cv.toFixed(0) + '%' : '-';
                var cvColor = d.cv ? (d.cv < 30 ? '#16a34a' : d.cv < 60 ? '#ca8a04' : '#dc2626') : '#999';
                row.append('div').style('width', '40px').style('text-align', 'right').style('color', cvColor).text(cvText);

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
            }} else if (currentVizType === 'treemap') {{
                renderTreemap(container, filtered, treatments);
            }}
        }}

        function renderScatter(container, data, t1, t2, color1, color2) {{
            var width = 320, height = 280;
            var margin = {{ top: 20, right: 20, bottom: 40, left: 50 }};

            var svg = container.append('svg')
                .attr('width', width)
                .attr('height', height);

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
            var width = 450, height = 420;

            // Calculate fold change and sort
            var withFC = data.map(function(d) {{
                var v1 = d[t1] || 0.1, v2 = d[t2] || 0.1;
                var fc = v1 > v2 ? v1/v2 : -v2/v1;
                return {{ compound: d.compound, mz: d.mz, fc: fc, t1val: d[t1], t2val: d[t2] }};
            }}).filter(function(d) {{ return Math.abs(d.fc) > 2; }}) // Only show >2x differences
              .sort(function(a, b) {{ return Math.abs(b.fc) - Math.abs(a.fc); }})
              .slice(0, 20);

            var svg = container.append('svg').attr('width', width).attr('height', height);

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
            var svg = container.append('svg').attr('width', width).attr('height', height);

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
                    return data.compound + '\\nm/z: ' + (data.mz || 'N/A') + '\\nRT: ' + (data.rt || 'N/A') + '\\nDrought: ' + (data.drought ? data.drought.toExponential(1) : '0') + '\\nAmbient: ' + (data.ambient ? data.ambient.toExponential(1) : '0') + '\\nWatered: ' + (data.watered ? data.watered.toExponential(1) : '0');
                }});

            document.getElementById('viz-info').innerHTML = 'Circle size = abundance, color = dominant treatment. Hover for details.';
        }}

        // PIE CHART - distribution of peaks
        function renderPie(container, filtered, treatments, allData) {{
            var width = 320, height = 280;
            var radius = Math.min(width, height) / 2 - 40;

            var svg = container.append('svg').attr('width', width).attr('height', height)
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
            var width = 450, height = 420;
            var svg = container.append('svg').attr('width', width).attr('height', height);

            if (data.length === 0) {{
                svg.append('text').attr('x', width/2).attr('y', height/2).attr('text-anchor', 'middle').attr('fill', '#666').text('No peaks to display');
                return;
            }}

            // Helper to get max abundance from selected treatments only
            function getSelectedMax(d) {{
                var vals = treatments.map(function(t) {{ return d[t] || 0; }});
                return Math.max.apply(null, vals);
            }}

            // Take top 100 by abundance (using selected treatments)
            var sorted = data.slice().sort(function(a, b) {{
                return getSelectedMax(b) - getSelectedMax(a);
            }}).slice(0, 100);

            // Pack layout - size based on selected treatments only
            var pack = d3.pack().size([width - 20, height - 40]).padding(2);

            var root = d3.hierarchy({{ children: sorted }})
                .sum(function(d) {{ return getSelectedMax(d); }});

            pack(root);

            // Determine color by absolute dominant treatment (always compares all 3)
            function getColor(d) {{
                if (!d.data.compound) return '#ccc';
                var vals = [
                    {{ t: 'drought', v: d.data.drought || 0 }},
                    {{ t: 'ambient', v: d.data.ambient || 0 }},
                    {{ t: 'watered', v: d.data.watered || 0 }}
                ];
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
                    return d.data.compound + '\\nm/z: ' + (d.data.mz || 'N/A') + '\\nRT: ' + (d.data.rt || 'N/A') + '\\nDrought: ' + (d.data.drought ? d.data.drought.toExponential(1) : '0') + '\\nAmbient: ' + (d.data.ambient ? d.data.ambient.toExponential(1) : '0') + '\\nWatered: ' + (d.data.watered ? d.data.watered.toExponential(1) : '0');
                }});

            document.getElementById('viz-info').innerHTML = 'Bubble size = abundance, color = dominant treatment. Hover for details.';
        }}

        // TREEMAP - rectangles sized by abundance
        function renderTreemap(container, data, treatments) {{
            var width = 450, height = 420;

            if (data.length === 0) {{
                container.append('p').style('color', '#666').text('No peaks to display');
                return;
            }}

            // Group by absolute dominant treatment (always compares all 3)
            function getDominant(d) {{
                var vals = [
                    {{ t: 'drought', v: d.drought || 0 }},
                    {{ t: 'ambient', v: d.ambient || 0 }},
                    {{ t: 'watered', v: d.watered || 0 }}
                ];
                vals.sort(function(a, b) {{ return b.v - a.v; }});
                return vals[0].t;
            }}

            // Helper to get max abundance from selected treatments only
            function getSelectedMax(d) {{
                var vals = treatments.map(function(t) {{ return d[t] || 0; }});
                return Math.max.apply(null, vals);
            }}

            // Take top 100 by abundance (using selected treatments)
            var sorted = data.slice().sort(function(a, b) {{
                return getSelectedMax(b) - getSelectedMax(a);
            }}).slice(0, 100);

            var hierarchy = {{
                name: 'root',
                children: treatments.map(function(t) {{
                    return {{
                        name: t,
                        children: sorted.filter(function(d) {{ return getDominant(d) === t; }}).map(function(d) {{
                            return {{ name: d.mz ? parseFloat(d.mz).toFixed(2) : d.compound.substring(0,8), value: getSelectedMax(d), compound: d.compound, data: d }};
                        }})
                    }};
                }}).filter(function(g) {{ return g.children.length > 0; }})
            }};

            var root = d3.hierarchy(hierarchy).sum(function(d) {{ return d.value || 0; }});
            d3.treemap().size([width, height - 20]).padding(1)(root);

            var svg = container.append('svg').attr('width', width).attr('height', height);

            svg.selectAll('rect')
                .data(root.leaves())
                .enter()
                .append('rect')
                .attr('x', function(d) {{ return d.x0; }})
                .attr('y', function(d) {{ return d.y0; }})
                .attr('width', function(d) {{ return Math.max(0, d.x1 - d.x0); }})
                .attr('height', function(d) {{ return Math.max(0, d.y1 - d.y0); }})
                .attr('fill', function(d) {{ return treatmentColors[d.parent.data.name] || '#ccc'; }})
                .attr('opacity', 0.8)
                .attr('stroke', 'white')
                .append('title')
                .text(function(d) {{
                    var data = d.data.data || {{}};
                    return (d.data.compound || d.data.name) + '\\nm/z: ' + (data.mz || 'N/A') + '\\nValue: ' + (d.value ? d.value.toExponential(1) : '0');
                }});

            // Add labels to larger rectangles
            svg.selectAll('text')
                .data(root.leaves().filter(function(d) {{ return (d.x1 - d.x0) > 25 && (d.y1 - d.y0) > 12; }}))
                .enter()
                .append('text')
                .attr('x', function(d) {{ return d.x0 + 2; }})
                .attr('y', function(d) {{ return d.y0 + 10; }})
                .attr('font-size', '8px')
                .attr('fill', 'white')
                .text(function(d) {{ return d.data.name; }});

            document.getElementById('viz-info').innerHTML = 'Treemap: area = abundance, color = dominant treatment. Hover for details.';
        }}

        // Initialize when priority tab is shown
        document.querySelector('[onclick*=\"priority\"]').addEventListener('click', function() {{
            setTimeout(function() {{
                updateToggleButtons();
                updateComparison();
                updateVisualization();
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
    print(f"\nFiltering summary:")
    print(f"  Original peaks: {total:,}")
    print(f"  After blank filter: {len(kept_blank):,} ({blank_stats['both_discard']:,} contamination removed)")
    print(f"  After 80% filter: {len(kept_80):,} ({100*len(kept_80)/total:.1f}% of original)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
