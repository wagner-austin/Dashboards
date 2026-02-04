# MFAssignR Molecular Formula Assignment
library(MFAssignR)
library(readxl)
library(dplyr)

# Patch RStudio restart bug
.rs.restartR <- function() { invisible(NULL) }

cat("=== Loading Data ===\n")
df <- read_excel("Emily_Data_Pruned_Labeled.xlsx")
cat("Loaded", nrow(df), "rows\n")

cat("\n=== Preparing Input ===\n")
input_df <- df %>%
  select(`m/z`, `Maximum Abundance`, `Retention time (min)`) %>%
  rename(mass = `m/z`, Abundance = `Maximum Abundance`, RT = `Retention time (min)`) %>%
  filter(!is.na(mass), !is.na(Abundance), Abundance > 0) %>%
  arrange(mass)
cat("Input rows:", nrow(input_df), "\n")

cat("\n=== KMDNoise ===\n")
noise_result <- KMDNoise(input_df)
noise_level <- noise_result$Noise
cat("Noise level:", noise_level, "\n")
sn_threshold <- noise_level * 6
cat("S/N threshold (6x):", sn_threshold, "\n")

cat("\n=== IsoFiltR ===\n")
filtered_df <- input_df %>% filter(Abundance > sn_threshold)
cat("Peaks above threshold:", nrow(filtered_df), "\n")
iso_result <- IsoFiltR(filtered_df, SN = 6)
cat("Monoisotopic:", nrow(iso_result$Mono), "\n")
cat("Isotopes:", nrow(iso_result$Iso), "\n")

cat("\n=== MFAssignCHO ===\n")
cho_result <- MFAssignCHO(
  iso_result$Mono,
  isopeaks = iso_result$Iso,
  ionMode = "pos",
  lowMW = 100,
  highMW = 1000,
  ppm_err = 3,
  SN = 6
)
cat("CHO Assigned:", nrow(cho_result$Unambig), "\n")
cat("Unassigned:", nrow(cho_result$None), "\n")

cat("\n=== MFAssign (full with N, S, P) ===\n")
full_result <- MFAssign(
  iso_result$Mono,
  isopeaks = iso_result$Iso,
  ionMode = "pos",
  lowMW = 100,
  highMW = 1000,
  ppm_err = 3,
  SN = 6,
  Nx = 4,
  Sx = 2,
  Px = 2
)
cat("Full Assigned:", nrow(full_result$Unambig), "\n")
cat("Ambiguous:", nrow(full_result$Ambig), "\n")
cat("Unassigned:", nrow(full_result$None), "\n")

# Save results
write.csv(full_result$Unambig, "formulas_assigned.csv", row.names = FALSE)
write.csv(full_result$None, "formulas_unassigned.csv", row.names = FALSE)

# Summary
cat("\n=== SUMMARY ===\n")
assigned <- full_result$Unambig
cat("Total peaks:", nrow(input_df), "\n")
cat("Above S/N:", nrow(filtered_df), "\n")
cat("Monoisotopic:", nrow(iso_result$Mono), "\n")
cat("Formulas assigned:", nrow(assigned), "(", round(100*nrow(assigned)/nrow(iso_result$Mono), 1), "%)\n")
cat("\nBy composition:\n")
cat("  CHO only:", sum(assigned$N == 0 & assigned$S == 0 & assigned$P == 0), "\n")
cat("  With N:", sum(assigned$N > 0), "\n")
cat("  With S:", sum(assigned$S > 0), "\n")
cat("  With P:", sum(assigned$P > 0), "\n")

cat("\nSaved: formulas_assigned.csv, formulas_unassigned.csv\n")
