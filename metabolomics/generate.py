"""Generate HTML report with embedded interactive data tables."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

import polars as pl


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
    data_path = Path(
        r"C:\Users\austi\PROJECTS\Tree Data\Metabolomics\Emily_Jaycee_CombinedData.xlsx"
    )

    print("Loading data...")
    all_cols = pl.read_excel(
        data_path, sheet_name="Normalized", infer_schema_length=0
    ).columns
    data_cols = [c for c in all_cols if not c.startswith("__UNNAMED__")]
    df = pl.read_excel(
        data_path,
        sheet_name="Normalized",
        columns=data_cols,
        infer_schema_length=None,
    )

    # Emily's samples only (Jaycee's removed due to signal intensity differences)
    SAMPLE_COLS = [
        # Emily's leaves
        "BL", "CL", "EL", "GL", "IL", "JL", "LL", "ML", "OL", "PL", "RL", "TL",
        # Emily's roots
        "AR", "DR", "ER", "GR", "HR", "IR", "JR", "MR", "RR", "SR", "TR",
    ]

    # Emily's blanks for blank subtraction
    BLANK_COLS = [
        "250220_ebtruong_blank1", "250220_ebtruong_blank2",
        "250220_ebtruong_blank3", "250220_ebtruong_blank4"
    ]

    print("Running filtering...")

    total = df["Compound"].n_unique()

    # Step 1: Blank filtering - remove peaks that are primarily blank contamination
    print("Step 1: Blank filtering...")
    kept_blank, blank_stats = filter_blanks(df, SAMPLE_COLS, BLANK_COLS, threshold=3.0)
    df_blank_filtered = df.filter(pl.col("Compound").is_in(list(kept_blank)))
    print(f"  After blank filtering: {len(kept_blank):,} peaks (removed {blank_stats['both_discard']:,} contamination peaks)")

    # Step 2: 80% cumulative filtering on blank-filtered data
    print("Step 2: 80% cumulative filtering...")
    kept_80: set[str] = set()
    sample_data_80: list[tuple[str, str, int, float]] = []

    for col in SAMPLE_COLS:
        k80, n80, pct80 = filter_cumulative(df_blank_filtered, col, 0.80)
        kept_80.update(k80)
        tissue = "Leaf" if col.endswith("L") else "Root"
        sample_data_80.append((col, tissue, n80, pct80 * 100))

    # Create final filtered DataFrame
    print("Creating filtered dataset...")
    df_80 = df_blank_filtered.filter(pl.col("Compound").is_in(list(kept_80))).select(["Compound"] + SAMPLE_COLS)

    # Convert to JSON
    print("Converting to JSON...")
    json_80 = df_to_json(df_80, SAMPLE_COLS)

    # Calculate stats
    leaf_80 = [x for x in sample_data_80 if x[1] == "Leaf"]
    root_80 = [x for x in sample_data_80 if x[1] == "Root"]

    print("Generating HTML...")

    # Build column definitions for DataTables
    col_defs = [{"data": "Compound", "title": "Compound"}]
    for col in SAMPLE_COLS:
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
    </style>
</head>
<body>
    <div class="header-container">
        <div class="header">
            <h1>Metabolomics Filtering Analysis</h1>
        </div>

        <div class="tabs">
        <button class="tab active" onclick="showTab('overview')">Overview</button>
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
            <li><strong>File:</strong> Emily_Jaycee_CombinedData.xlsx</li>
            <li><strong>Sheet:</strong> Normalized</li>
            <li><strong>Samples:</strong> 23 total (12 Leaf, 11 Root) - Emily's samples only</li>
            <li><strong>Blanks:</strong> 4 blanks (250220_ebtruong_blank1-4)</li>
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
                <strong>Blanks used:</strong> 250220_ebtruong_blank1, blank2, blank3, blank4
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
