# Audit: a-model-that-checks-itself

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale`, `overclaim`, `unsourced`, `framing`. Re-run whenever the cited page's
`fact_checked` moves.

Audited 2026-09-14 against API `d89684561` (TankpitBot's last commit
`d2bb1e4dc`, 2026-09-09). Source page: `me/tankpitbot` (fact_checked 2026-09-12
when the article shipped; corrected twice this day, now 2026-09-14). The
project's own wiki under `clients/TankpitBot/wiki` is public and is where the
session records and decoder inventory live.

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| reverse-engineered a private protocol with no documentation | tankpitbot § Access and § Knowledge | project wiki `xor-cipher.md`, `decode-coverage.md` | supported |
| caught three of its own conclusions being wrong, including the ending of its best result | § What it actually does, three refutation paragraphs | `wiki/log.md:4738-4760` | supported |
| encrypted wire, key table derived per session from a value the server injects | § Access, "XOR codec with both a static key and a per-session magic key" | `xor-cipher.md:19-37`, `tankpit.magic` | supported |
| "a subtype byte that is scrambled per session so it cannot be trusted" (previous text) | § Knowledge, previous text | `decoders/tank.py:421-431` docstring says subtype-first dispatch; `xor-cipher.md` describes a frame cipher, not a scrambled field; `decode-coverage.md` § Container Subtypes | **overclaim, removed**: on the me-wiki since 2026-08-12, unsupported by the project |
| 32 message types, each pinned to a signature | § Knowledge; footnote 1 | `MSG_MIN_LENGTHS` entries counted 32 at HEAD | supported |
| 84 kills, 0 deaths, 149 minutes, ended because a fresh map held no affordable enemy | § What it actually does, first paragraph | `wiki/log.md:4738`, artifact `bot-20260825-212920` | supported |
| Python, Playwright, CDP, hierarchical state machine, simulated server | § Access and § Experimenting and acting | `src/tankpit_bot/browser/`, `sim/` (11,008 lines at HEAD) | supported |
| 7,007 tests, full statement and branch coverage, no mocks | § What it actually does, "Gate throughout"; footnote 4 | `poetry run pytest --co -q` = 7007 collected; `pyproject.toml:133,145`; `README.md:55` | **stale, fixed**: the article said 6,879, a def-count whose command was never recorded and which no counting variant reproduces on the unchanged tree |
| a partial mutation sweep on top, not a standing check | § Test discipline, rewritten | `wiki/log.md:4094`, `:4115`, `:4242`; no make target runs it | **overclaim, fixed**: the article had "mutation testing on top" under Gate |

## One decoder per wire byte

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| traffic captured through the browser's own socket; synthetic events do not work | § Access, first bullet | `README.md`, `src/tankpit_bot/browser/` | supported |
| XOR with a static key and a per-session magic key, both directions reversed | § Access, second bullet | `xor-cipher.md:19-37`, `protocol/codec.py` | supported |
| one dispatcher: subtype-first, structural for shapes with no unique subtype byte | § Knowledge, rewritten 2026-09-14 | `decoders/tank.py:421-438` | supported |
| six length-based fallbacks deleted after 150 sessions and 48,304 bodies showed zero fires | same | `decode-coverage.md` § Container Subtypes, "deleted 2026-06-20 after a corpus sweep of 150 sessions / 48,304 0x2E bodies proved zero production fires"; footnote 13 names the re-derivation scripts | supported |
| the excerpt | `decoders/tank.py:421-430`, two parenthetical lists elided and marked | diffed against `d89684561` | supported |

## Three conclusions the instrument refuted

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| operator said 27 enemies always; record showed every enemy rejected as stale map data, one ten tiles away; map open completed in 12 ms via an orphan flag | § What it actually does, second paragraph | `wiki/log.md:4747`, "total_enemies=27, accepted 0, every rejection stale_map_data", "red-9 TEN tiles away", "completed in 12 ms" | supported |
| my "dying wire" explanation refuted; last frame 5.7 s after dispatch, 3.7 s after the bot quit; latency, not the wire | third paragraph | `wiki/log.md:4751`, "landing 5.7 s after dispatch and 3.7 s AFTER the phantom exit" | supported |
| every movement stall was fuel-starved latency crossing a fixed deadline; larger run matched 102 to 102 | fourth paragraph, corrected 2026-09-14 | `wiki/log.md:4722`, "102↔102, 11≈12" | **overclaim, fixed**: article and page had said the counts matched exactly without saying which run; the smaller run was 11 against 12 |
| one mechanism, three disguises | framing, drawn from the log's own wording "same disease" | | framing |

## Measurements that fail the build

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| beliefs carry provenance and confidence | § Truth-keeping, `facts/` | `src/tankpit_bot/facts/` | supported |
| validators price the model against the capture archive; encode(decode(x)) == x for every archived message | § Truth-keeping, `validate/` | `src/tankpit_bot/validate/` | supported |
| invariants raise where violated | § Truth-keeping, `contracts/` | `src/tankpit_bot/contracts/` | supported |
| one executable symbol per machine-checked physics claim, verified against its claim on every build, re-derived from the archive by a separate audit | § Truth-keeping, `physics/`, corrected 2026-09-14; footnote 6 | `scripts/physics_claims.py`, six claim kinds none of which reads `runs/`; `Makefile:121` `check: lint \| test`; `Makefile:392` `audit` runs `tankpit-audit` | **overclaim, fixed**: article and page had "re-derived from the run archive on every build"; the project README line 48 still says so and is noted on the wiki page |
| optimisation probed 10/10, built and gated, second probe dropped 7 of 10, reverted the same night | § What it actually does, fifth paragraph | `wiki/log.md:4760` | supported |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| project wiki of 6 hubs and 83 pages; README defers to it | § Test discipline; footnote 2 | `ls wiki/hubs` = 6, `ls wiki/pages` = 83 at HEAD | supported |
| session figures are one session | footnote 3 | | supported |
| mutation sweep: 37 of 483 once, 6 survivors killed, not on every build | § Test discipline; footnote 4 | `wiki/log.md:4094`, `:4115`, `:4242` | supported |
| the scrambled-subtype claim stood from the source page's first day and survived two re-measurements | me-wiki history: `59f77cd` (2026-08-12) introduced it; re-measured 2026-08-26 and 2026-09-12 | `git log -S'XOR-scrambled'` | supported |

## Sources block

Every link is to `wagner-austin/API` at `d89684561`, probed 200 on 2026-09-14:
`clients/TankpitBot`, `sniffer/constants.py`, `protocol/decoders/tank.py`,
`wiki/pages/xor-cipher.md`, `wiki/pages/decode-coverage.md`, `wiki/log.md`,
`pyproject.toml`.
