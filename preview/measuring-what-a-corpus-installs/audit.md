# Audit: measuring-what-a-corpus-installs

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale`, `overclaim`, `unsourced`, `framing`. Re-run whenever a cited page's
`fact_checked` moves.

Audited 2026-09-14. Source pages: `me/extraction-ablation` (fact_checked
2026-08-17 when the article shipped, with a 2026-09-12 correction to the scale
arm; corrected again and now 2026-09-14), which cites
`personal/wiki-corpus-extraction-ablation` (2026-08-27) and its per-item outcome
files; `personal/marker-effect-across-four-scales` (2026-09-09). The personal
wiki is private. The training service is public.

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| seven-arm ablation on two published interventions, against real cited prose | me § The result; personal § The arms | arms A through G in the outcome files | supported |
| one survived, one inert under every specified condition, a third contrast decisively negative | me § The result table | recomputed contrasts: D−C +2.94, C−B +0.36, E−C −0.22, F−G +0.06, B−A −6.14 | supported |
| three of five results are nulls | same | markers, cooldown, loss-masking | supported |
| perplexity cannot grade a corpus intervention | me § The instrument; the Allen-Zhu and Li page | source page `allen-zhu-2024-knowledge-storage-extraction` | supported |
| 2,627 four-way cloze items masking numeric values | me § The instrument | every arm vector has 2,627 keys | supported |
| unexposed model scores 52.3% against 25.0% chance | me § The instrument | the floor arm is not in the two A-to-G files; the me-wiki and personal pages carry it | supported by the page; not recomputed this pass |
| seven arms, three seeds, exact McNemar per seed, not pooled | me § The result | personal § Result, the contrast table with per-seed p | supported |
| Python, PyTorch, GPT-2, Slurm | personal § Result (`hf_lm` backend); hpc3 runs | | supported |

## The floor is the finding nobody publishes

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| 52.3% and 25.0%; an intervention lifting raw accuracy to sixty has done almost nothing | me § The instrument | | supported; the sixty is illustrative framing |
| a floor established after the results is chosen with knowledge of the answer | framing | | framing |

## What survived and what did not

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| table: dilution −6.14 decisive; permuted copies +2.94 decisive; marker +0.36 noise; cooldown −0.22 null; loss-masking +0.06 null with seeds disagreeing | me § The result table | recomputed from `outcomes-A-E-seeds-42-44.json` and `outcomes-F-G-seeds-42-44.json`: A 83.80, B 77.66, C 78.01, D 80.95, E 77.79, F 77.82 (masked), G 77.76; contrasts match to two decimals; per-seed p from the personal page | supported |
| inert under all three specified conditions | me § The result | markers, cooldown, loss-masking each null | supported |

## The error I corrected in my own analysis

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| an earlier version reported markers real on a one-sample t of 14.0 over three per-seed differences | me § The error I caught | | supported, as the page's own retraction |
| the arms share one item set so per-seed differences are correlated; paired test over 2,627 items finds nothing | same; personal § Result | recomputed C−B per seed: +0.38, +0.38, +0.31; the personal page's McNemar p of 0.59, 0.60, 0.69 | supported |

## What the controls turned up

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| the splitter divides by file and its single-file branch returned the same file as train, validation and test | me § The defect; API `3ce75c2f0` body, "returned files, files, files" | | supported |
| every arm's corpus is a single file; 91 fixtures deep | same; the fix commit body, "91 corpus fixtures across the suite" | | supported |
| published results unaffected: no arm uses validation loss; the cloze set is the only cross-arm metric | me § The defect | | supported |
| pinned with a test declaring it known; "a fix turns the test red" (previous text) | me § The defect, previous text | `3ce75c2f0`, 2026-08-20; `test_corpus_and_dataset_edges.py:107`, "The headline fix" | **stale, fixed**: the fix landed three days after the page; the article had described the defect as open |
| the excerpt | `test_corpus_and_dataset_edges.py:107-114`, one sentence elided and marked | diffed against `d89684561` | supported |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| a four-rung arm ran to 1.5B; marker contrast negative there | me § Where it points; personal `marker-effect-across-four-scales` § The marker contrast, paired by seed | mean −0.5588, all three seeds negative, p ≈ 0.008 per the page | supported |
| not evidence the effect emerges at scale; the instrument sharpens by a factor of thirteen | same; sd 1.1235 to 0.0870 | 1.1235 / 0.0870 = 12.9 | supported |
| augmentation reported as a lower bound; 6.21% of prose sentences admit a deterministic rewrite | me § Why this belongs; personal § line 102, "Of the 18,110 prose sentences" | | supported |
| no public repository for the corpus | me § Why this belongs | the personal wiki is private | supported |
| the split defect was described as open until 2026-09-14 | this audit | | supported |

## Sources block

Probed 200 on 2026-09-14: `services/Model-Trainer` and `dataset_builder.py` at
`d89684561`, commits `1278c605` and `3ce75c2f0`, the test file, and the two
arXiv abstracts, whose ids were read from the personal wiki's source records
(`DOI: 10.48550/arXiv.2501.01956`, `10.48550/arXiv.2309.14316`).
