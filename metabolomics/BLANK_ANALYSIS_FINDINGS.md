# Blank Analysis Findings

**Date:** January 29, 2026
**Data source:** `Emily_Jaycee_CombinedData - Copy.xlsx` (Normalized sheet)

---

## What Are Blanks?

Blanks are samples processed through the entire extraction and analysis workflow but **without plant tissue**. They capture:
- Solvent impurities
- Plasticizers from tubes/pipette tips
- Instrument background/carryover
- Any contamination NOT from the plant

## Standard Blank Filtering Approach

For each peak, compare sample signal vs blank signal:
- **KEEP** if `sample_avg >= 3 × blank_avg` (real biological signal)
- **REMOVE** if `sample_avg < 3 × blank_avg` (likely contamination)
- **KEEP** if peak only appears in samples, not in blanks

---

## Blanks Available in the Data

| Blank Column | Non-zero Peaks | Notes |
|--------------|----------------|-------|
| 250220_ebtruong_blank1 | 3,567 | Emily Truong's blank |
| 250220_ebtruong_blank2 | 1,390 | Emily Truong's blank |
| 250220_ebtruong_blank3 | 855 | Emily Truong's blank |
| 250220_ebtruong_blank4 | 1,051 | Emily Truong's blank |
| 250220_ebtruong_combine | 7,537 | Emily Truong's combined |
| BL2 | 6,623 | Possibly "Blank Leaf 2"? |
| BL3 | 7,093 | Possibly "Blank Leaf 3"? |
| BL4 | 7,184 | Possibly "Blank Leaf 4"? |
| blank1_root | 5,211 | Named as root blank |
| blank2_root | 4,165 | Named as root blank |
| blank3_root | 4,005 | Named as root blank |
| Blk1 | 4,997 | Generic blank |
| Blk2 | 1,534 | Generic blank |

---

## What We Were Told

> "Blk1 and Blk2 are leaf blanks. Any truong blanks are root blanks."

---

## What the Data Shows

We analyzed which **tissue-specific peaks** appear in each blank:
- **Leaf-only peaks** = peaks found in leaf samples but NOT root samples
- **Root-only peaks** = peaks found in root samples but NOT leaf samples

If a blank contains more leaf-only peaks, it likely picked up leaf contamination (and should be used for leaf filtering).

### Emily's Tissue Overlap Analysis

| Blank | Emily Leaf-only | Emily Root-only | Data Suggests |
|-------|-----------------|-----------------|---------------|
| 250220_ebtruong_blank1 | 242 | 140 | **LEAF** |
| 250220_ebtruong_blank2 | 73 | 60 | **LEAF** |
| 250220_ebtruong_blank3 | 27 | 47 | **ROOT** |
| 250220_ebtruong_blank4 | 29 | 68 | **ROOT** |
| 250220_ebtruong_combine | 31 | 441 | **ROOT** |
| BL2 | 589 | 339 | **LEAF** |
| BL3 | 652 | 398 | **LEAF** |
| BL4 | 679 | 396 | **LEAF** |
| blank1_root | 448 | 248 | **LEAF** (despite name!) |
| blank2_root | 306 | 187 | **LEAF** (despite name!) |
| blank3_root | 349 | 183 | **LEAF** (despite name!) |
| Blk1 | 471 | 180 | **LEAF** |
| Blk2 | 62 | 70 | **UNCLEAR** |

### Jaycee's Tissue Overlap Analysis

| Blank | Jaycee Leaf-only | Jaycee Root-only | Data Suggests |
|-------|------------------|------------------|---------------|
| blank1_root | 294 | 507 | **ROOT** |
| blank2_root | 159 | 525 | **ROOT** |
| blank3_root | 141 | 478 | **ROOT** |
| (most others) | higher | lower | **LEAF** |

---

## Discrepancies Found

| Blank | Told | Data Shows | Match? |
|-------|------|------------|--------|
| Blk1 | LEAF | LEAF | Yes |
| Blk2 | LEAF | UNCLEAR | Maybe |
| ebtruong_blank1 | ROOT | LEAF | **NO** |
| ebtruong_blank2 | ROOT | LEAF | **NO** |
| ebtruong_blank3 | ROOT | ROOT | Yes |
| ebtruong_blank4 | ROOT | ROOT | Yes |

**Key finding:** ebtruong_blank1 and ebtruong_blank2 contain more leaf-specific peaks than root-specific peaks, suggesting they may have been run with leaf samples, not root samples.

---

## Interpretation

The `blank_root` samples (blank1_root, blank2_root, blank3_root) appear to be:
- **Jaycee's ROOT blanks** (they correlate with Jaycee root samples)
- But they also contain Emily's leaf-specific peaks

This could mean:
1. These blanks were mislabeled
2. There was cross-contamination
3. The blanks were run at different times than assumed

---

## Open Questions

1. **Which blanks should we use for Emily's data?**
   - Option A: Trust what we were told (Blk1/Blk2 = leaf, all ebtruong = root)
   - Option B: Trust the data analysis (use peak overlap to assign)
   - Option C: Use all blanks together (no tissue-specific filtering)

2. **Do we need tissue-specific blank filtering at all?**
   - If all samples were processed together, maybe one set of blanks is fine
   - Tissue-specific filtering only matters if batches were separate

3. **Should we verify with the person who ran the samples?**
   - The data contradicts what we were told about ebtruong_blank1 and blank2

---

## Samples in the Study

### Emily's Samples (23 total)

**Leaf (12):** BL, CL, EL, GL, IL, JL, LL, ML, OL, PL, RL, TL
- Drought: BL, CL, EL, GL
- Ambient: IL, JL, LL, ML
- Watered: OL, PL, RL, TL

**Root (11):** AR, DR, ER, GR, HR, IR, JR, MR, RR, SR, TR
- Drought: AR, DR, ER, GR
- Ambient: HR, IR, JR, MR
- Watered: RR, SR, TR

### Jaycee's Samples

**Leaf:** AL, DL, FL, HL, KL, NL, QL, SL, UL
**Root:** BR, CR, FR, KR, LR, NR, PR, QR, UR

---

## Next Steps

- [ ] Decide on blank assignment approach
- [ ] Update generator with chosen blank configuration
- [ ] Run filtering and review results
- [ ] Optionally verify blank assignments with lab personnel
