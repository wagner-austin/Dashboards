# Audit: architecture-as-code

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale`, `overclaim`, `unsourced`, `framing`. Re-run whenever the cited page's
`fact_checked` moves.

Audited 2026-09-14 against API `d89684561`. Source page: `me/api-monorepo`
(fact_checked 2026-09-11 when the article shipped; every count re-derived
2026-09-14 and unchanged, now fact_checked 2026-09-14).

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| thirteen services, twenty-two shared libraries | § Scale; footnote 1 | `find services -maxdepth 1 -mindepth 1 -type d` = 13; `find libs ...` minus `.claude` = 22 | supported |
| 47 architecture rules that fail the build | § Start here, item 3; footnote 2 | the `rules: list[Rule]` literal in `orchestrator.py` has 46 entries, plus one `rules.append(DataclassRule(config))` | supported |
| 41 Python and 6 Rust | same | 6 entries named `Rust*Rule`; 46 minus 6 plus the appended `DataclassRule` = 41 | supported |
| strict typing and full branch coverage | § Scale, "under strict mypy and full branch coverage" | `CODE_STANDARDS.md` at the repo root; the guard rules `TypingRule`, `RustCoverageRule` | supported |
| Python, FastAPI, Rust, Redis, RQ, Kafka, PostgreSQL | § Scale, "FastAPI + Redis + RQ + Kafka"; PostgreSQL from covenant-radar | `services/covenant-radar-api/pyproject.toml:27` `psycopg`; `libs/cleargbm_rs` | supported |

## Why a rule rather than a review comment

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| every rule exists because something went wrong once | framing, consistent with the rules' docstrings | | framing |
| covers both languages | footnote 2, 41 Python and 6 Rust | the six `Rust*Rule` entries | supported |
| forty-six always run; the forty-seventh registers only when a config segment is set | footnote 2 | `orchestrator.py:113-114`, `if config.dataclass_ban_segments: rules.append(...)` | supported |
| the excerpt | `orchestrator.py:64-67` and `:108-114`, forty-two entries elided and marked | diffed against `d89684561`; 46 minus the 4 shown = 42 | supported |

## The three things worth fifteen minutes

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| the README opens with a Start here section naming the three | § Start here | `README.md` at `d89684561` | supported |
| ClearGBM: numpy layer, then a Rust core with histogram building, tree construction, prediction, PyO3 | § Start here, item 1 | `libs/cleargbm`, `libs/cleargbm_rs`; the cleargbm page re-verified pyo3 0.27.2 on 2026-09-11 | supported |
| Covenant Radar: deepest service, pluggable backend registry, Kafka, hyperparameter search | § Start here, item 2, and the covenant-radar page | audited separately in `adding-a-domain-without-a-fork/audit.md` | supported |
| monorepo_guards: linted at CI time | § Start here, item 3 | | supported |
| speech in 57 languages to English; GPT-2 and character-LSTM with LoRA and QLoRA; image-model LoRA; Turkic corpus construction | § Other services worth naming | `services/grandma-api/README.md` § Input Languages (57), 57 unique codes in the table; Model-Trainer, Art-Trainer, turkic-api directories | supported |

## A service count that went down

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| there were fourteen; a document-extraction service was deleted once the platform it fed grew its own | § Scale, "went DOWN once, from 14, when doc-extract-api was deleted"; § The two game clients live here too | `git log --diff-filter=D -- services/doc-extract-api` = `b02c25d3a`, 2026-08-01, "Remove doc-extract-api, superseded by the MCPs service" | supported |
| the interesting number is how much it refuses to hold twice | framing | | framing |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| the page carries the exact command behind each count and the note that `ls` over-counts | footnotes 1 and 2 | | supported |
| rule count grew by a third in the three weeks before writing | footnote 2: 35 on 2026-08-20, 47 on 2026-09-11 | 12 / 35 = 34 percent | supported |
| re-derived by parsing the literal; a bare `Rule(` grep over-counts to 48 | footnote 2 | | supported |
| every count re-derived 2026-09-14, none moved | footnote 2, the 2026-09-14 reading | this audit | supported |

## Sources block

Every link probed 200 on 2026-09-14: the repository tree, README, `libs/monorepo_guards`,
`orchestrator.py`, `services/`, `libs/`, `libs/cleargbm`, `libs/cleargbm_rs`,
`services/grandma-api/README.md`, all at `d89684561`, and commit `b02c25d3a`.
