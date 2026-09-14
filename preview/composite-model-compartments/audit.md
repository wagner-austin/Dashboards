# Audit: composite-model-compartments

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale`, `overclaim`, `unsourced`, `framing`. Re-run whenever a cited page's
`fact_checked` moves.

Audited 2026-09-14. Source pages, both in the public API monorepo:
`api-codebase/model-trainer-composition-ceiling` (fact_checked 2026-09-04;
pointer updated and `RESEARCH.md` re-pinned, now 2026-09-14) and
`api-codebase/model-trainer-companioned-training-recipe` (fact_checked
2026-09-09; `RESEARCH.md` re-pinned). Every source pin on both pages matched
HEAD `d89684561` except `docs/RESEARCH.md`, which grows with every run.

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| naive limit at two compartments | ceiling § What this binds, "the practical limit at this scale UNDER NAIVE TRAINING is two" | ceiling page intro: 62.8% at two, −45.4% at four, −7.0% at eight; `docs/RESEARCH.md:267` | supported |
| a recipe moved four-compartment retention from −45.4% to +44.6% | ceiling § What this binds; recipe § grid table row "trained p=0.5" | `docs/RESEARCH.md:307-308`, record sha256 `9e87e816…`, bit-identical across two processes | supported |
| a diverse pool has since taken it to +55.5% | recipe § The diverse pool | `docs/RESEARCH.md:409`, jobs 55772675 and 55773234 on HPC3 | **stale, fixed**: the article stopped at +44.6% |
| at 48 layers the eight-compartment penalty vanishes | recipe § The ladder verdict, "diverse n8 equals n4 to a tenth under BOTH objectives" | the page's own paragraph; run records named in its provenance | supported |
| replicated across three roster rotations; SHA-256-identical records from two processes | ceiling page intro and frontmatter provenance | provenance line "v2 record bit-identical across two processes: sha256 aa61330b…" | supported |
| GPT-2 at three depths, a 3090 Ti offline and V100s on the cluster | recipe § ladder verdict (12, 24, 48 layers); provenance lines naming V100 jobs | `docs/RESEARCH.md:404-406` | **stale, fixed**: the article had said one card offline |

## The controls caught the result before a reader did

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| first roster read +27% at eight and was leakage | ceiling § The run caught two of its own artifacts | `docs/RESEARCH.md:278-280` | supported |
| +0.18 and +0.41 cross-gain; shared vocabulary | same | same | supported |
| the sweep scores every foreign compartment alone against the primary held-out text | same; the sweep docstring | `cartridge_composition_sweep.py:24-30` | supported |
| clean rerun put eight at −7.0% | same | `docs/RESEARCH.md:267` | supported |
| the excerpt | `cartridge_composition_sweep.py:24-30`, one parenthetical elided and marked | diffed against `d89684561`; the elided "94% retention" is a figure the wiki does not carry | supported |

## Moving the limit rather than reporting it

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| the literature names the escape route: concatenation works when trained for | ceiling § What this binds, "the ICAE multi-span finding" | the personal wiki's parametric-knowledge hub | supported |
| table row: naive, −45.4% and −7.0% | ceiling page | as above | supported |
| table row: one companion at p=0.5, +44.6% and +26.5% | recipe § grid table; § diverse pool, "the single companion's 26.5%" | | supported |
| table row: three companions, +55.5% and +28.0% | recipe § The diverse pool | | supported |
| table row: GPT-2 XL, +54.8% at both counts under the LM objective | recipe § The ladder verdict | | supported |
| at eight on the small model the composed arm equals its untrained control | recipe § The diverse pool, "+0.2323 vs +0.2431" | | supported |
| eight equals four to a tenth at 48 layers; a mid-depth valley | recipe § The ladder verdict | | supported |

## What this does not settle

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| the recipe does not survive 7B as-is; the precondition fails | recipe § What this binds and what is still open | | supported |
| solo gain at 7B a mean of +0.16 across nine seeds, one negative, against +0.78 to +0.86 on every GPT-2 rung | same, "gpt2-xl's nine draws all land in +0.78..+0.86", "7B/NF4 ... a mean of only +0.16 ... one draw negative" | | supported |
| the plain 7B base already predicts each corpus at the smaller bases' cartridge level | same, "plain-base loss 4.57/4.27/4.11/3.66 down the ladder" | | supported |
| corpora versus personas is open; the literature suggests harder | the personal wiki survey `many-personas-in-one-model-feasibility` | private page; named in Sources as such | supported |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| both pages pinned to the source blobs | frontmatter of both | every pin except `RESEARCH.md` matched HEAD; `RESEARCH.md` re-pinned | supported |
| retention ratios, not a serving benchmark | ceiling page intro | | supported |
| "one model family at one scale, on a single card" (previous text) | none current | the ladder and the 7B rung | **stale, removed** |
| the wider programme had claims withdrawn for sitting below its instrument's floor | api-codebase page `a-claim-four-times-below-its-instruments-floor` | exists in `wiki/pages/` | supported |

## Sources block

Every link probed 200 on 2026-09-14: both wiki pages and `docs/RESEARCH.md`
at `aeb9ff46c`, the three sweep modules at `d89684561`.
