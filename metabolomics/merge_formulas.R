# Merge MFAssignR formulas back to original compound data
library(readxl)
library(dplyr)

cat("Loading data...\n")
orig <- read_excel("Emily_Data_Pruned_Labeled.xlsx")
formulas <- read.csv("formulas_assigned.csv")

cat("Original data:", nrow(orig), "rows\n")
cat("Formulas:", nrow(formulas), "rows\n")

# Round m/z and RT for matching
orig <- orig %>% mutate(
  mz_round = round(`m/z`, 4),
  rt_round = round(`Retention time (min)`, 2)
)
formulas <- formulas %>% mutate(
  mz_round = round(exp_mass, 4),
  rt_round = round(RT, 2)
)

# Select key formula columns
formula_cols <- formulas %>% select(
  mz_round, rt_round,
  MF_formula = formula,
  MF_C = C, MF_H = H, MF_O = O, MF_N = N, MF_S = S, MF_P = P,
  MF_err_ppm = err_ppm,
  MF_DBE = DBE,
  MF_class = class
)

# Join
merged <- left_join(orig, formula_cols, by = c("mz_round", "rt_round"))

# Remove temp columns
merged <- merged %>% select(-mz_round, -rt_round)

matched <- sum(!is.na(merged$MF_formula))
cat("\nMatched:", matched, "compounds with formulas\n")
cat("Unmatched:", nrow(merged) - matched, "\n")

# Save
write.csv(merged, "Emily_Data_WITH_FORMULAS.csv", row.names = FALSE)
cat("\nSaved to Emily_Data_WITH_FORMULAS.csv\n")

# Show examples
cat("\n=== Example Matches ===\n")
examples <- merged %>%
  filter(!is.na(MF_formula)) %>%
  select(Compound, `m/z`, MF_formula, MF_err_ppm, MF_class) %>%
  head(15)
print(examples, width = 100)

# Validation summary
cat("\n=== Validation Metrics ===\n")
assigned <- merged %>% filter(!is.na(MF_formula))
cat("Mass error (ppm):\n")
cat("  Mean:", round(mean(abs(assigned$MF_err_ppm)), 2), "\n")
cat("  Max:", round(max(abs(assigned$MF_err_ppm)), 2), "\n")
cat("  <1 ppm:", sum(abs(assigned$MF_err_ppm) < 1), "(", round(100*sum(abs(assigned$MF_err_ppm) < 1)/nrow(assigned), 1), "%)\n")
cat("  <2 ppm:", sum(abs(assigned$MF_err_ppm) < 2), "(", round(100*sum(abs(assigned$MF_err_ppm) < 2)/nrow(assigned), 1), "%)\n")
cat("  <3 ppm:", sum(abs(assigned$MF_err_ppm) < 3), "(", round(100*sum(abs(assigned$MF_err_ppm) < 3)/nrow(assigned), 1), "%)\n")

cat("\nFormula classes:\n")
print(table(assigned$MF_class))
