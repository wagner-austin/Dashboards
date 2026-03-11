# MFAssignR Stage 1: Run through RecalList, then STOP for user input
.rs.restartR <- function() invisible(NULL)

library(MFAssignR)
library(readxl)
library(dplyr)

cat("=== STAGE 1: Data -> KMDNoise -> IsoFiltR -> MFAssignCHO -> RecalList ===\n\n")

# Load data
df_raw <- read_excel("Emily_Data_Pruned_Labeled.xlsx")
cat("Loaded", nrow(df_raw), "rows\n")

# Prepare for MFAssignR
Data_all <- df_raw %>%
  select(`m/z`, `Maximum Abundance`, `Retention time (min)`, Charge) %>%
  rename(mass = `m/z`, Abundance = `Maximum Abundance`, RT = `Retention time (min)`) %>%
  filter(!is.na(mass), !is.na(Abundance), Abundance > 0) %>%
  arrange(mass)

# Split by charge
Data_z1 <- Data_all %>% filter(Charge == 1) %>% select(-Charge)
Data_z2 <- Data_all %>% filter(Charge == 2) %>% select(-Charge)
cat("z=1 peaks:", nrow(Data_z1), "\n")
cat("z=2 peaks:", nrow(Data_z2), "\n\n")

# z=1 pipeline
Data <- Data_z1

cat("--- KMDNoise ---\n")
Noise <- KMDNoise(Data)
KMDN <- Noise[["Noise"]]
cat("KMD Noise level:", KMDN, "\n\n")

noise_threshold <- 6

cat("--- IsoFiltR ---\n")
Isotopes <- IsoFiltR(Data,
                     SN = noise_threshold * KMDN,
                     Carbrat = 60, Sulfrat = 30,
                     Sulferr = 5, Carberr = 5)
Mono <- Isotopes[["Mono"]]
Iso <- Isotopes[["Iso"]]
cat("Monoisotopic:", nrow(Mono), "\n")
cat("Polyisotopic:", nrow(Iso), "\n\n")

cat("--- MFAssignCHO (package defaults) ---\n")
Assign <- MFAssignCHO(
  Mono, Iso,
  ionMode = "pos",
  SN = noise_threshold * KMDN,
  ppm_err = 3, NMScut = "on",
  DeNovo = 1000, lowMW = 100, highMW = 1000,
  H_Cmin = 0.3, H_Cmax = 3, O_Cmax = 1.2,
  DBEOmax = 13, DBEOmin = -13
)
Unambig1 <- Assign[["Unambig"]] %>%
  arrange(desc(abundance)) %>%
  distinct(formula, .keep_all = TRUE)
cat("Unambiguous CHO:", nrow(Unambig1), "\n")
cat("Unassigned:", nrow(Assign[["None"]]), "\n\n")

cat("--- RecalList ---\n")
cat("Pick 2-4 series from this table for recalibration.\n")
cat("Rules: low Peak_Score, low Peak_Distance, broad mass range.\n\n")
RL <- RecalList(df = Unambig1)
print(as.data.frame(RL), right = FALSE)

# Save state for stage 2
save(Data, Data_z1, Data_z2, KMDN, noise_threshold,
     Mono, Iso, Unambig1, RL,
     file = "stage1_state.RData")
cat("\nState saved. Pick your series and run stage 2.\n")
