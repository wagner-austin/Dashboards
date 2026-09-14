# Audit: reproducible-gpu-inference

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale`, `overclaim`, `unsourced`, `framing`. Re-run whenever a cited page's
`fact_checked` moves.

Audited 2026-09-14. Source pages, both in the private personal research wiki
under the pdf-corvis contract: `a-loss-agrees-where-the-computation-does-not`
(fact_checked 2026-09-01; card count corrected and now 2026-09-14) and
`cross-gpu-agreement-is-recoverable-by-disabling-split-k` (2026-08-29). The
code the measurements ran is public in the API monorepo.

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| byte-identical output on 8 GPU models across 6 families, two operating systems, two toolchains | a-loss § A new toolchain and a Blackwell card, the scoreboard sentence | the page's 2026-09-01 sentence counts seven; the 09-04 battery adds one; the roster (footnotes 21 and 22) names V100, A30, A100, L40S, RTX 3090 Ti, RTX 3070 Ti Laptop, GTX 1630, RTX PRO 6000; families sm_70, 75, 80, 86, 89, 120 | **stale and overclaim, both fixed**: the page said nine cards (its own roster gives eight); the article said five families (the page said six) |
| PyTorch determinism settings make one card reproduce itself, not two cards agree | both pages' framing | | supported |
| 2,627 of 2,627 per-item scores bit-identical on every pair; one file, one SHA-256, six cards, two OS | a-loss § The four-card record closes the corpus, "Six cards now carry that one hash" | | supported |
| free within measurement noise from 128 rows up | split-k § Where the cost actually goes away | | supported |
| the eight cards named in Stack | the two rosters | | supported |

## What was actually wrong

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| the disagreement looked like a size threshold; that reading was wrong | split-k page intro and § Isolating one matmul | | supported |
| six of eight shapes produced three different tensors on three cards, including shapes with bit-identical losses | split-k § Isolating one matmul, line 49 | footnote 1: `gemm_benchmark.py`, 2026-08-26, HPC3, three cards | supported |
| the threshold was where a present disagreement grew big enough to move the last bit | split-k page's framing of the same | | supported |

## Three interventions, and what each was worth

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| remove split-K: isolated matmuls 2 of 8 to 8 of 8; attention untouched | split-k § The intervention; § But the whole model is not eight matmuls | the fenced line "default 2/8 -> split-K removed 8/8" | supported |
| pin the math backend: 198 of 900 score comparisons exact | a-loss § A real workload, four cards | | supported |
| own the reduction order: 2,627 of 2,627, every pair; one Turing card since closed | a-loss § A real workload; § The sm_75 residual is caught, named, and closed | | supported |
| the excerpt | `clients/OrderedKernels/src/ordered_kernels/kernels.py:12-22`, one clause elided and marked | diffed against `d89684561` | supported |
| GTX 1630 broke identity at 147 of 150; the three divergent items were not the long ones; the value product at 15- and 16-token sequences | a-loss § Two more machines; § The sm_75 residual; footnote 21 | | supported |

## What it costs

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| 0% to 13% per matmul at a realistic batch, several negative | split-k § What it costs, measured, the table and "Costs of 0–13%, several of them negative" | | supported |
| an earlier version reported up to +84% at a single 64-token sequence | same section, the short-sequence table | | supported |
| the cost collapses between 64 and 128 rows and never returns | split-k § Where the cost actually goes away, line 142 | | supported |

## What the result does not establish

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| a no-divergence run bounds a rate; Clopper-Pearson 0.114% on the tightest row, 0.072% pooled; one divergence in 2,627 is 0.0381%; no row excludes it | a-loss § A new toolchain, "What that zero excludes" | 1 / 2627 = 0.0381% | supported |
| bit-identity across a corpus says nothing about a fresh pair of runs; observed once | a-loss § The four-card record | | supported |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| timing figures are per-GEMM | split-k § Scope; a-loss § Scope, "The cost is per attention CALL" | | supported |
| the isolated-matmul campaign records its container as content-addressed but carries no digest | split-k footnote 1 | | supported |
| the card and family miscounts | this audit | | supported |

## Sources block

Every link probed 200 on 2026-09-14, all at `d89684561`: `clients/OrderedKernels`,
`kernels.py`, `gemm_benchmark.py`, `probe_trace.py`, `deterministic_gemm.py`.
