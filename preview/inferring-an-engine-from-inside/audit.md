# Audit: inferring-an-engine-from-inside

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale`, `overclaim`, `unsourced`, `framing`. Re-run whenever the cited page's
`fact_checked` moves.

Audited 2026-09-14 against API `d89684561`. Source page: `me/rustedwarfarebot`
(fact_checked 2026-09-11 when the article shipped; corrected and now
2026-09-14). The project's own wiki under `clients/RustedWarfareBot/wiki` is
public. The project's working tree carried 38 uncommitted files from another
session at audit time; every count here is from the committed tree.

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| obfuscated Java binary, class names change between releases | § The obfuscation problem | `wiki/pages/*.md` carry `game_version: "1.15 (code 176, build #28)"` | supported |
| inject code into the running JVM, real state and real orders, no pixels, no synthetic input | § Access | `agent/`, `-nodisplay` in the Makefile's launch line | supported |
| bit-identical per seed within one environment | § Reproducibility, rewritten; project `policy-determinism.md` "Re-certified 2026-08-31, with its scope stated" | the page's own wording | **overclaim, fixed**: the article had said "bit-identical per seed" with no scope; the certified property is same seed AND same environment |
| certified 12 of 12 pairs over 250 samples each | same | `policy-determinism.md:175-176` | supported |
| 201 authored doctrines, 235 sweep definitions committed; 554 generated candidates refused | § Experiments, rewritten; footnote 1 | `git ls-tree -r --name-only HEAD .../doctrines \| wc -l` = 201; sweeps `.txt` = 235; `git ls-files --others --ignored --exclude-standard doctrines \| wc -l` = 554; `.gitignore:20-29` | **overclaim, fixed**: the article said "729 doctrine files and 247 sweeps on disk"; 554 of the 729 were ignored search output |
| Java agent, bytecode patching, Python, Postgres-backed match queue | § Access; § The rest, the match service | `agent/`, `src/rw_bot/`, footnote 3 | supported |
| own wiki of 5 hubs and 56 pages | § The rest; footnote 2 | `ls -1 wiki/pages/*.md` = 56 and committed count = 56; hubs 5 | **stale, fixed**: 55 on 2026-09-11 |

## Inside the runtime, not looking at the screen

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| agent dispatches orders and serializes state out; Python plans | § Access | `agent/`, `src/rw_bot/harness/` | supported |
| boots headless, no framebuffer, no scraping, no synthetic input | § Access, `-nodisplay` | `Makefile:125-131`, `.decompiled/.../Main.java:229` handles `-nodisplay` | supported |
| not measuring a vision pipeline by accident | framing | | framing |

## The obfuscation problem, gated rather than noted

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| every engine claim carries the game version | § The obfuscation problem | `game_version` frontmatter on the project wiki pages | supported |
| build patches the real jar and lets the JVM verifier check it | same, `make agent-selftest` | `Makefile:190-194`, "JVM verifier as oracle" | supported |
| the verifier is someone else's | framing on the same | | framing |

## The control that makes the rest mean anything

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| seeded generators, lockstep handoff, pinned frame delta; world digest in the trace | § Reproducibility; footnote 4 | `replication.py:1-20`; `campaign_match.py:99` `PINNED_DELTA_MS = 3` | supported |
| digest computed per sample from every visible entity's identity and position; the frame of divergence names the leak | same | `replication.py` docstring, quoted in the excerpt | supported |
| the excerpt | `replication.py:7-11` | diffed against `d89684561` | supported |
| 24-member panel, Docker and cluster; divergence across environments from frame 300; pinned delta is a new regime | § Reproducibility; `policy-determinism.md` "Where it stands" and "Re-certified" | the page's own paragraphs | supported |
| doctrine file has no optional fields; sweeps freeze a snapshot per batch | § Experiments | `src/rw_bot/` doctrine loader; the sweep driver | supported by the page; not re-read in code this pass |
| keeping the refutations is deliberate | § Experiments | | framing, from the page |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| a second public wiki versioned against the jar | § The rest; footnote 2 | `clients/RustedWarfareBot/wiki` | supported |
| 729 was a working-tree count summing authored and generated | § Experiments, the 2026-09-14 correction | `find doctrines -type f` on the worktree = 755 today; 201 + 554 | supported |
| the win-rate target is a goal, not a result | § The rest, first bullet | | supported |
| paused green in August, active again; the page said paused for three weeks | § The rest, footnote 3 | 274 commits since 2026-08-20 per that footnote; 366 since by `git log --since=2026-08-20` today | supported |

## Sources block

Every link probed 200 on 2026-09-14, all at `d89684561`: the project tree,
`agent/`, `doctrines/`, `sweeps/`, `.gitignore`, `wiki/pages/policy-determinism.md`,
`src/rw_bot/harness/campaign_match.py`, `src/rw_bot/harness/replication.py`,
`Makefile`, `wiki/`.
