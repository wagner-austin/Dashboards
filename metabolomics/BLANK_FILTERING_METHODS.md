# Blank Filtering Methods in Metabolomics

## Overview

This document reviews published methods for blank subtraction in mass spectrometry-based metabolomics, with citations to peer-reviewed sources and regulatory guidelines.

## The Problem

In untargeted metabolomics, **blank samples** (solvent-only or matrix-only controls) capture background contamination from:
- Solvents and reagents
- Plasticizers from labware
- Instrument carryover
- Environmental contamination

Peaks appearing in both blanks and biological samples may be contamination rather than true biological signals. The challenge is distinguishing real metabolites from artifacts.

---

## Published Methods

### 1. BLANKA Algorithm (Conservative Removal)

**Citation:** Cleary JL, Luu GT, Pierce EC, Dutton RJ, Sanchez LM. "BLANKA: an algorithm for blank subtraction in mass spectrometry of complex biological samples." *Journal of the American Society for Mass Spectrometry*. 2019;30(8):1426-1434.

**Link:** https://pmc.ncbi.nlm.nih.gov/articles/PMC6675636/

**Method:**
- Removes peaks that match blank peaks by m/z and retention time
- Uses tolerance windows for matching (user-defined)
- Conservative approach: removes matched peaks regardless of intensity
- Recommends **4:1 signal-to-noise ratio** as minimum cutoff

**Best for:** Studies where eliminating false positives is critical; complex matrices with high background.

---

### 2. Peak Matrix Processing (pmp) - Fold Change Method

**Citation:** Jankevics A, Lloyd GR, Weber RJM. "pmp: Peak Matrix Processing and signal batch correction for metabolomics datasets." *Bioconductor*.

**Link:** https://bioconductor.org/packages/release/bioc/html/pmp.html

**Method:**
- Compares median intensity in samples vs median intensity in blanks
- Default threshold: **20-fold change** (sample must be 20x higher than blank)
- Features below threshold are removed

**Best for:** Metabolomics pipelines requiring reproducible, software-implemented filtering.

---

### 3. ICH Q2(R1) Guidelines (Signal-to-Noise Standards)

**Citation:** International Council for Harmonisation. "Q2(R1) Validation of Analytical Procedures: Text and Methodology." ICH Harmonised Guideline. 1994/1996. Adopted by FDA November 2005.

**Links:**
- https://www.fda.gov/media/152208/download (FDA-adopted PDF, verified accessible)
- https://www.ema.europa.eu/en/ich-q2r2-validation-analytical-procedures-scientific-guideline (EMA overview)

**Exact quotes from the document:**

On **Detection Limit (LOD)**, Section 6.2, page 7:
> "This approach can only be applied to analytical procedures which exhibit baseline noise. Determination of the signal-to-noise ratio is performed by comparing measured signals from samples with known low concentrations of analyte with those of blank samples and establishing the minimum concentration at which the analyte can be reliably detected. **A signal-to-noise ratio between 3 or 2:1 is generally considered acceptable for estimating the detection limit.**"

On **Quantitation Limit (LOQ)**, Section 7.2, page 8:
> "This approach can only be applied to analytical procedures that exhibit baseline noise. Determination of the signal-to-noise ratio is performed by comparing measured signals from samples with known low concentrations of analyte with those of blank samples and by establishing the minimum concentration at which the analyte can be reliably quantified. **A typical signal-to-noise ratio is 10:1.**"

**Alternative formulas:**
- LOD = 3.3 × σ / S (where σ = standard deviation of blank, S = slope of calibration curve)
- LOQ = 10 × σ / S

**⚠️ CRITICAL DISTINCTION:**
The ICH signal-to-noise ratio compares:
- **Signal:** Response from a sample with known LOW concentration of analyte
- **Noise:** Baseline noise or standard deviation of blank responses

This is **NOT the same** as comparing sample intensity to blank intensity for contamination filtering. The ICH method establishes the minimum detectable/quantifiable concentration, not whether a peak is contamination.

**Best for:** Establishing detection and quantification limits for method validation; regulatory submissions.

---

### 4. Univariate Statistical Analysis Guidelines

**Citation:** Vinaixa M, Samino S, Saez I, Duran J, Guinovart JJ, Yanes O. "A Guideline to Univariate Statistical Analysis for LC/MS-Based Untargeted Metabolomics-Derived Data." *Metabolites*. 2012;2(4):775-795.

**Link:** https://pmc.ncbi.nlm.nih.gov/articles/PMC3901240/

**Method for differential analysis (not blank subtraction):**
- **Fold change threshold:** 1.5x minimum (2x for stringent filtering)
- **Statistical test:** t-test (parametric) or Mann-Whitney (non-parametric)
- **Multiple testing correction:** FDR (Benjamini-Hochberg) at q < 0.05
- **CV filtering:** Remove features with CV > 20% in QC samples

**Best for:** Comparing treatment groups; identifying differential metabolites.

---

## Comparison of Thresholds

| Method | Threshold | Application | Citation |
|--------|-----------|-------------|----------|
| BLANKA | Remove if present in blank | Contamination removal | Cleary et al. 2019 |
| pmp/structtoolbox | 20x fold-change | Contamination removal | Bioconductor pmp |
| ICH Q2 LOD | 3:1 S/N vs baseline | Detection limit | ICH Q2(R2) |
| ICH Q2 LOQ | 10:1 S/N vs baseline | Quantification limit | ICH Q2(R2) |
| Vinaixa et al. | 1.5-2x FC + p<0.05 FDR | Differential analysis | Vinaixa et al. 2012 |

---

## What Our Current Method Does (and Its Limitations)

### Current Implementation
```
For each peak found in both samples and blanks:
1. Calculate fold-change: sample_mean / blank_mean
2. Perform Welch's t-test (one-sided)
3. Apply Benjamini-Hochberg FDR correction
4. Keep if: fold-change ≥ 3x AND FDR-adjusted p < 0.05

Peaks only in samples (not in blanks): auto-keep (infinite fold-change)
```

### Limitations

1. **The 3x threshold is not directly citable for this purpose.**
   - ICH 3:1 refers to signal-to-noise ratio for establishing LOD (lowest detectable concentration)
   - We are using it for sample-vs-blank intensity comparison (contamination filtering)
   - These are fundamentally different applications
   - No peer-reviewed paper directly supports "3x sample/blank" for contamination removal

2. **"Infinite fold" peaks bypass validation.**
   - Peaks only in samples are auto-kept without statistical testing
   - This assumes: if not in blank, cannot be contamination
   - Reasonable assumption, but should be explicitly stated
   - Count: ~19,000 peaks auto-kept this way

3. **Limited statistical power.**
   - Only 2 leaf blanks and 4 root blanks
   - t-test requires n ≥ 2 per group; many comparisons have marginal power
   - ~6,000 peaks fell back to fold-change only due to insufficient data

4. **No CV filtering.**
   - High-variability peaks (CV > 30%) are kept
   - May introduce noise into downstream analysis
   - Vinaixa et al. (2012) recommend removing features with CV > 20%

---

## Recommended Changes

### Option A: Conservative (BLANKA-style)
Remove any peak present in blanks, regardless of intensity. Most conservative; may remove real biological signals with low-level background.

**Citation:** Cleary et al. 2019, JASMS

### Option B: pmp-style (20x fold-change)
Require 20x fold-change for peaks in both samples and blanks. Well-supported by metabolomics software.

**Citation:** Bioconductor pmp package (Jankevics, Lloyd, Weber)

### Option C: Statistical approach (t-test + FDR, no arbitrary fold-change)
Use only statistical significance (Welch's t-test, FDR-corrected p < 0.05) without an arbitrary fold-change threshold. Let the data speak for itself.

**Citation:** Benjamini & Hochberg 1995 (FDR); standard statistical practice

### ❌ NOT Recommended: 3x fold-change
The 3x threshold has no direct citation for sample-vs-blank contamination filtering. ICH 3:1 is for LOD determination, which is a different application.

---

## Conclusion

**For publication, we should either:**

1. Use a citable threshold (20x from pmp, or conservative BLANKA removal)
2. Use purely statistical criteria (t-test + FDR) without an arbitrary fold-change
3. Clearly state that the fold-change threshold is a practical choice, not derived from regulatory guidance

**The honest statement for methods section:**
> "Peaks were filtered by comparing mean intensities between biological samples and blank controls. Peaks detected only in samples (not in blanks) were retained. For peaks detected in both, we required [chosen threshold] to distinguish biological signal from background contamination. Statistical significance was assessed using Welch's t-test with Benjamini-Hochberg FDR correction (q < 0.05)."

---

## References

1. Cleary JL, Luu GT, Pierce EC, Dutton RJ, Sanchez LM. BLANKA: an algorithm for blank subtraction in mass spectrometry of complex biological samples. *J Am Soc Mass Spectrom*. 2019;30(8):1426-1434. doi:10.1007/s13361-019-02185-8

2. Jankevics A, Lloyd GR, Weber RJM. pmp: Peak Matrix Processing and signal batch correction for metabolomics datasets. R package version 1.15.1. Bioconductor. https://bioconductor.org/packages/release/bioc/html/pmp.html

3. International Council for Harmonisation. Q2(R2) Validation of Analytical Procedures. ICH Harmonised Guideline. November 2023. https://database.ich.org/sites/default/files/ICH_Q2(R2)_Guideline_2023_1130.pdf

4. Vinaixa M, Samino S, Saez I, Duran J, Guinovart JJ, Yanes O. A Guideline to Univariate Statistical Analysis for LC/MS-Based Untargeted Metabolomics-Derived Data. *Metabolites*. 2012;2(4):775-795. doi:10.3390/metabo2040775

5. Benjamini Y, Hochberg Y. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *J R Stat Soc Series B*. 1995;57(1):289-300.

---

## Document History

- **Created:** 2026-02-04
- **Purpose:** Document blank filtering methodology with proper citations for publication
