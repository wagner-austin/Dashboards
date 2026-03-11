# Merge MFAssignR formulas back to original compound data
# Produces Emily_Data_WITH_FORMULAS.xlsx for the dashboard
library(readxl)
library(dplyr)
library(openxlsx)

cat("=== Merging MFAssignR Formulas ===\n\n")

# Load original data
orig <- read_excel("Emily_Data_Pruned_Labeled.xlsx")
cat("Original data:", nrow(orig), "rows\n")

# Load MFAssignR unambiguous assignments
formulas <- read.csv("formulas_assigned.csv")
cat("MFAssignR assignments:", nrow(formulas), "rows\n")

# Match strategy: Recalibration shifts m/z slightly, so exact rounding fails.
# RT is unchanged by recal and matches perfectly.
# Approach: for each original row, find formula with same RT and closest m/z
#           within 5 ppm tolerance.

# Select key formula columns and rename to match dashboard loader
formula_cols <- formulas %>% transmute(
  form_mz = exp_mass,
  form_rt = round(RT, 2),
  Assigned_Formula = formula,
  MF_C = C, MF_H = H, MF_O = O, MF_N = N, MF_S = S, MF_P = P,
  MF_err_ppm = AE_ppm,
  MF_DBE = DBE,
  MF_class = class,
  MF_group = group
)

orig <- orig %>% mutate(
  orig_mz = `m/z`,
  orig_rt = round(`Retention time (min)`, 2),
  .row_id = row_number()
)

# Join on RT, then keep closest m/z within 5 ppm.
# Two-step approach to avoid dropping rows whose RT matches a formula but m/z doesn't.
candidates <- inner_join(
  orig %>% select(.row_id, orig_mz, orig_rt),
  formula_cols,
  by = c("orig_rt" = "form_rt"),
  relationship = "many-to-many"
) %>%
  mutate(mz_diff_ppm = abs(orig_mz - form_mz) / orig_mz * 1e6) %>%
  filter(mz_diff_ppm < 5) %>%
  group_by(.row_id) %>%
  slice_min(mz_diff_ppm, n = 1, with_ties = FALSE) %>%
  ungroup() %>%
  select(-orig_mz, -orig_rt, -form_mz, -mz_diff_ppm)

# Left join back: every original row preserved, formulas attached where matched
merged <- left_join(orig, candidates, by = ".row_id") %>%
  select(-orig_mz, -orig_rt, -.row_id)

matched <- sum(!is.na(merged$Assigned_Formula))
cat("\nMatched:", matched, "compounds with MFAssignR formulas\n")
cat("Unmatched:", nrow(merged) - matched, "\n")
cat("Match rate:", round(100 * matched / nrow(merged), 1), "%\n")

# Save as XLSX (dashboard reads xlsx, not csv)
write.xlsx(merged, "Emily_Data_WITH_FORMULAS.xlsx", overwrite = TRUE)
cat("\nSaved to Emily_Data_WITH_FORMULAS.xlsx\n")

# Also save CSV backup
write.csv(merged, "Emily_Data_WITH_FORMULAS.csv", row.names = FALSE)
cat("Saved backup to Emily_Data_WITH_FORMULAS.csv\n")

# Validation summary
cat("\n=== Validation ===\n")
assigned <- merged %>% filter(!is.na(Assigned_Formula))
if (nrow(assigned) > 0) {
  cat("Mass error (ppm):\n")
  cat("  Mean:", round(mean(abs(assigned$MF_err_ppm)), 3), "\n")
  cat("  Median:", round(median(abs(assigned$MF_err_ppm)), 3), "\n")
  cat("  Max:", round(max(abs(assigned$MF_err_ppm)), 3), "\n")
  cat("  <1 ppm:", sum(abs(assigned$MF_err_ppm) < 1), "(",
      round(100 * sum(abs(assigned$MF_err_ppm) < 1) / nrow(assigned), 1), "%)\n")
  cat("  <2 ppm:", sum(abs(assigned$MF_err_ppm) < 2), "(",
      round(100 * sum(abs(assigned$MF_err_ppm) < 2) / nrow(assigned), 1), "%)\n")
  cat("  <3 ppm:", sum(abs(assigned$MF_err_ppm) < 3), "(",
      round(100 * sum(abs(assigned$MF_err_ppm) < 3) / nrow(assigned), 1), "%)\n")

  cat("\nFormula classes:\n")
  print(table(assigned$MF_class))

  cat("\nFormula groups:\n")
  print(table(assigned$MF_group))
}
