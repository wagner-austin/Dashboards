# Metabolomics Dashboard

Interactive visualization tool for analyzing metabolomics data across treatment groups (Drought, Ambient, Watered) and tissue types (Leaf, Root).

## Data Processing

### Two-Step Filtering
1. **Blank Subtraction** - Removes contamination peaks where sample signal < 3x blank signal (per [pmp/Bioconductor](https://bioconductor.org/packages/release/bioc/html/pmp.html)), with Welch's t-test and [Benjamini-Hochberg FDR correction](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)
   - Leaf samples filtered against leaf blanks (Blk1, Blk2)
   - Root samples filtered against root blanks (ebtruong_blank1-4)
2. **80% Cumulative Threshold** - Keeps only peaks that contribute to the top 80% of signal in any sample

### Molecular Formula Assignment (MFAssignR)

After filtering, molecular formulas are assigned using [MFAssignR](https://github.com/skschum/MFAssignR) ([Schum et al. 2020](https://doi.org/10.1016/j.envres.2020.110114)), a peer-reviewed R package for ultrahigh resolution mass spectrometry.

The pipeline runs in `run_mfassignr.Rmd`:

1. **KMDNoise** - Estimates noise floor via Kendrick Mass Defect analysis
2. **IsoFiltR** - Separates monoisotopic peaks from isotope partners (13C, 34S)
3. **MFAssignCHO** - Preliminary CHO-only assignment for recalibration
4. **Recal** - Internal mass recalibration using homologous series (mzRange=80 Da, 6 auto-selected series)
5. **MFAssign** - Full formula assignment (C, H, O, N≤5, S≤2, P≤3) within 3 ppm, validated against [Koch et al. 2007](https://doi.org/10.1021/ac061949s) and [Kind & Fiehn 2007](https://doi.org/10.1186/1471-2105-8-105) elemental ratio rules

Doubly charged ions (z=2) are processed separately using MFAssignCHO (CHO-only) due to a [known MFAssignR limitation](https://github.com/skschum/MFAssignR/issues) with MFAssign_RMD at z=2.

Output: `formulas_assigned.csv` → merged into `Emily_Data_WITH_FORMULAS.xlsx` via `merge_formulas.R`.

### Source Data
- File: `Emily_Data_Pruned_Labeled.xlsx`
- Sheet: "Normalized"
- 23 samples total (12 Leaf, 11 Root)

## Compare Treatments Tab

### Treatment Toggle Buttons
Select 1, 2, or 3 treatments to compare:
- **1 treatment**: Shows peaks unique to that treatment (not in the other two)
- **2 treatments**: Shows peaks in either treatment (union)
- **3 treatments**: Shows all peaks

### Visualizations

#### Bubble Chart
- Each bubble = one compound
- **Size** = max abundance across **selected treatments only**
  - Changes when you toggle treatments on/off
- **Color** = dominant treatment across **all 3 treatments** (consistent regardless of selection)
  - Red = highest in Drought
  - Blue = highest in Ambient
  - Green = highest in Watered
- **Labels** = m/z values shown on larger bubbles
- Hover for full details (compound name, m/z, RT, abundance in each treatment)

#### Treemap
- Rectangles grouped by dominant treatment
- **Size** = max abundance across **selected treatments only**
- **Color** = dominant treatment (same as bubble chart)
- Labels on larger rectangles

#### Fold Change Bars
- Only available when exactly 2 treatments are selected
- Shows top 20 peaks with >2x fold change between the two treatments
- Bar direction indicates which treatment has higher abundance
- Bar length indicates magnitude of difference

### Data Table
Below the visualizations, a scrollable table shows:
- Compound name
- m/z (mass-to-charge ratio)
- RT (retention time in minutes)
- CV% (coefficient of variation, color-coded: green <30%, yellow 30-60%, red >60%)
- Abundance for each selected treatment with occurrence counts (e.g., "3/4" = detected in 3 of 4 samples)

## Other Tabs

### Overview
Summary statistics and per-sample filtering results.

### Priority Peaks
Same as Compare Treatments (legacy name).

### Treatment Overlap
Venn-style breakdown showing:
- Peaks unique to each treatment
- Peaks shared between pairs
- Peaks in all three treatments

### Methods
Detailed explanation of the filtering process, MFAssignR pipeline, parameters, and cited references.

### Filtered Data
Full DataTable with export to CSV/Excel.

### Understanding Peaks
Explains compound naming convention (e.g., `3.90_564.1489n` = RT 3.90 min, m/z 564.1489).

## Technical Notes

- Uses D3.js for visualizations
- Uses DataTables for interactive tables
- All data embedded in HTML (no server required after generation)
- Regenerate dashboard: `poetry run python generate.py`
- Rerun formula assignment: open `run_mfassignr.Rmd` in RStudio and knit (requires `stage1_state.RData` from `run_stage1.R`)
- Rerun merge: `Rscript merge_formulas.R` (requires `formulas_assigned.csv` and `Emily_Data_Pruned_Labeled.xlsx`)
