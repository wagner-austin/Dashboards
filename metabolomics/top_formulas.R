formulas <- read.csv("formulas_assigned.csv")
top <- head(sort(table(formulas$formula), decreasing=TRUE), 20)
cat("Top 20 formulas:\n")
print(top)

cat("\nSample formulas by class:\n")
cat("\nCHO only:\n")
cho <- formulas[formulas$N == 0 & formulas$S == 0 & formulas$P == 0, ]
print(head(unique(cho$formula), 10))

cat("\nWith Nitrogen:\n")
n <- formulas[formulas$N > 0 & formulas$P == 0, ]
print(head(unique(n$formula), 10))

cat("\nWith Phosphorus:\n")
p <- formulas[formulas$P > 0, ]
print(head(unique(p$formula), 10))
