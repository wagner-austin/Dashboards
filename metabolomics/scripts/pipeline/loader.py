"""Data loading stage for the metabolomics pipeline.

Loads raw data from Excel and formula assignments.
This is the first stage of the pipeline.

Extracted from generate.py lines 355-367.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from scripts.config import load_config
from scripts.pipeline.types import PipelineState, StageResult


def load_formulas(formula_path: Path) -> dict[str, str]:
    """Load formula assignments from processed Excel file.

    Extracted from generate.py lines 330-353.

    Args:
        formula_path: Path to Emily_Data_WITH_FORMULAS.xlsx

    Returns:
        Dict mapping compound names to assigned formulas.

    Raises:
        FileNotFoundError: If formula file doesn't exist.
    """
    formula_lookup: dict[str, str] = {}

    if not formula_path.exists():
        return formula_lookup

    df_formulas = pl.read_excel(formula_path, infer_schema_length=None)
    if "Compound" in df_formulas.columns and "Assigned_Formula" in df_formulas.columns:
        for row in df_formulas.iter_rows(named=True):
            compound = row.get("Compound")
            formula = row.get("Assigned_Formula")
            if compound is not None and formula is not None:
                formula_lookup[str(compound)] = str(formula)

    return formula_lookup


def load_data(
    state: PipelineState | None = None,
    config_path: Path | None = None,
    data_path: Path | None = None,
) -> PipelineState:
    """Load raw data from Excel.

    This is the first pipeline stage. It:
    1. Loads config.json
    2. Reads the Excel file
    3. Loads formula assignments

    Extracted from generate.py lines 355-367.

    Args:
        state: Existing pipeline state (or None to create new).
        config_path: Path to config.json (defaults to project root).
        data_path: Path to Excel file (defaults to config value).

    Returns:
        Updated PipelineState with df_raw and formula_lookup populated.

    Raises:
        FileNotFoundError: If data file doesn't exist.
    """
    if state is None:
        state = PipelineState()

    # Load config
    config = load_config(config_path)
    state.config = config

    # Determine data path
    if data_path is None:
        project_root = Path(__file__).parent.parent.parent
        data_path = project_root / config["input"]["file"]

    # Load Excel data
    print(f"Loading data from {data_path}...")
    df = pl.read_excel(
        data_path,
        sheet_name=config["input"]["sheet"],
        infer_schema_length=None,
    )

    state.df_raw = df
    print(f"  Loaded {df.height:,} rows, {df.width} columns")

    # Load formula assignments
    project_root = Path(__file__).parent.parent.parent
    formula_file = config["input"]["formula_file"]
    formula_path = project_root / formula_file if formula_file else None
    if formula_path is not None and formula_path.exists():
        state.formula_lookup = load_formulas(formula_path)
        print(f"  Loaded {len(state.formula_lookup):,} formula assignments")
    else:
        state.formula_lookup = {}
        print("  No formula assignments loaded")

    # Record stage completion
    state.add_stage_result(
        StageResult(
            stage_name="load",
            success=True,
            message=f"Loaded {df.height:,} peaks from {data_path.name}",
            input_count=0,
            output_count=df.height,
        )
    )

    return state
