# Audit: research-cluster-submission

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale`, `overclaim`, `unsourced`, `framing`. Re-run whenever the cited page's
`fact_checked` moves.

Audited 2026-09-14 against API `d89684561`. Source page: `me/hpc3-cli`
(fact_checked 2026-09-11 when the article shipped; corrected and now
2026-09-14). The package's own wiki under `tools/hpc3/wiki` is public and is
where the cluster measurements are recorded; the me-wiki page cites it.

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| 8 research projects run through one tool | hpc3-cli § Shape, "8 research projects submit through it" | `tools/hpc3/runs/hpc3*.json` `projects` keys: cleargbm, code-style, floor, mi, mi-cu128, rusted, tankpit, turkic-lstm | supported |
| will not let a job be built if it would fail | § The problem it encodes, "a job that would break one cannot be constructed" | preflight and budget rules below | supported |
| can answer which job produced which artifact | § Provenance, `hpc3-trace --match` | `src/hpc3/cli/trace.py:32-50` | supported |
| 102 distinct users holding jobs | § The problem it encodes | `tools/hpc3/README.md:5` | supported, a single observation |
| 17,432 source lines, 19,849 test lines, 15 commands | § Shape and footnote 1 | `find src -name '*.py' -exec cat {} + \| wc -l` = 17432; tests 19849; `[tool.poetry.scripts]` entries = 15, at `d89684561` | **stale, fixed**: 16,924 / 19,278 on 2026-09-11 |
| Python, Slurm, containerised environments pinned by digest | § Provenance, "the environment is the pinned one" | `src/hpc3/core/image_*.py`, `contracts/job.py` | supported |

## Five conditions that look like health

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| five conditions; three at first; fourth and fifth built the same day | § The five conditions, opening paragraph | `core/triage.py` docstring names four, `cli/triage.py:25` adds oversized; `678d58807` and `328b44cc9`, both 2026-08-28 | **stale, fixed**: article and page said three; both checks had existed seventeen days |
| blocked: 261 of 621 on DependencyNeverSatisfied, indistinguishable in squeue | § five conditions, blocked bullet; hpc3 wiki `triage-conditions` | `core/triage.py:6-8` docstring carries the figure | supported |
| unaccounted: no cluster-side query can find these | same, unaccounted bullet | `core/triage.py:9-11` | supported |
| unclaimed: mirror of unaccounted; 21 builds unrecorded; twenty-second found first run | same, unclaimed bullet; hpc3 wiki `image-ledger-lessons:21-26` and `triage-conditions` § The mirror check nobody had | `core/triage.py:29-33` docstring, "twenty-one of them ran without leaving a ledger row" | supported |
| silent: log age against the cluster's own clock | same, silent bullet | `core/logs.py:8` and `:38-39` | supported |
| oversized: waits for a backfill hole it never needed; 720 declared, 27 taken | same, oversized bullet; hpc3 wiki `triage-conditions` paragraph "What oversized caught the day it was written" | `core/rightsize.py`; the wiki paragraph | supported |
| the excerpt | `core/logs.py:38-39` | diffed against `d89684561` | supported |

## Rules that run

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| preflight non-skippable; sbatch test by path; same rendered file submitted | § Rules that run, first bullet | `contracts/preflight.py:10` docstring; grep for a skip flag in `src` returns nothing | supported |
| QOS bounds concurrency, nothing bounds the total, free partitions do not bill | § Rules that run, second bullet; hpc3 wiki `budget-model` | `budget-model.md:18-22` | supported |
| 24-GPU three-day sweep is 1,728 GPU-hours | same | 24 × 72 = 1,728 | supported |
| enforced before submission and while running | same, the two error codes | `BUDGET_PROJECTION_EXCEEDED` and `BUDGET_CONSUMPTION_EXCEEDED` both present in `src` | supported |
| neither is a warning the user can dismiss | framing on the two rules | | framing |

## Which job produced this file

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| four claims enforced: pinned environment, published bytes, declared determinism, traceable result | § Provenance | `contracts/job.py`, `contracts/ledger.py` carry determinism fields; `cli/trace.py` | supported |
| ledger is an index from job to image to artifact | same | `core/ledger.py` | supported |
| a null that cannot be traced is a file, not a finding | framing | | framing |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| 102 and 261-of-621 are single observations | § Known limits of the article, from the README's and triage docstring's phrasing "when this package was measured" | | supported |
| line counts moved by several hundred lines in three days | footnote 1: 508 and 571 | | supported |
| said three conditions until 2026-09-14; the others had existed seventeen days | this audit | 2026-08-28 to 2026-09-14 | supported |

## Sources block

Every link is to `wagner-austin/API` at `d89684561`, probed 200 on 2026-09-14:
`tools/hpc3`, `README.md`, `pyproject.toml`, `wiki/pages/triage-conditions.md`,
`wiki/pages/image-ledger-lessons.md`, `wiki/pages/budget-model.md`,
`src/hpc3/core/triage.py`, `src/hpc3/core/logs.py`,
`src/hpc3/contracts/preflight.py`.
