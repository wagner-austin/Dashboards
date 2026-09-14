# Audit: gradient-boosting-twice

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale`, `overclaim`, `unsourced`, `framing`. Re-run whenever the cited page's
`fact_checked` moves.

Audited 2026-09-14 against API `d89684561`. Source page: `me/cleargbm`
(fact_checked 2026-09-11 when the article shipped; corrected and now
2026-09-14).

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| implemented from scratch in numpy, ported the compute to Rust, deleted the numpy version | § What it is; § The retirement | commit `f7c61172`, "Rust-only compute path, no Python fallback" | supported |
| 6,910 lines of source and 7,677 of tests deleted | § The retirement, corrected 2026-09-14; footnote 1 | `git show --numstat f7c61172 -- libs/cleargbm/src` sums to 303 added, 6,910 deleted; over `tests`, 185 added, 7,677 deleted | **overclaim, fixed**: the article said "roughly 10k lines"; the page said "~10k lines"; neither count is 10k |
| the algorithm behind most machine learning on spreadsheet-shaped data | § The retirement, plain version | framing, from the page | framing |
| Rust core doing histogram building, tree construction and prediction, PyO3 0.27.2 | § What it is | `libs/cleargbm_rs/Cargo.toml:21` `pyo3 = { version = "0.27.2" }` | supported |
| suite went 555 to 182 at 100% coverage | § The retirement; footnote 1 | `def test_` definitions in `libs/cleargbm/tests` at `f7c61172^` = 555, at `f7c61172` = 182 | supported, now re-derived from the commit |
| Rust, PyO3, numpy, mypy strict | § The retirement, the façade | `_rust.py` docstring | supported |

## The sequence is the point, not the Rust

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| binning, split gain and the leaf update are where the algorithm lives | § Why it is worth fifteen minutes | | framing, from the page |
| the numpy version was an executable specification the Rust core had to agree with | same | `_hooks_*` and `_rust_adapters` deleted in `f7c61172` were the comparison layer | supported |

## Then the oracle was deleted

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| two implementations that can drift; a fallback path that hides a broken build | § Why it is worth fifteen minutes, "Then it was deleted" | | framing, from the page |
| native library is a hard dependency; raises at import if absent | § The retirement, "ImportError at import time if it is absent" | `_rust.py:9-11` | supported |
| a typed façade pins every native callable to a protocol | § The retirement, "`_rust.py` pins every native callable to a Protocol" | `_rust.py:1-7` | supported |
| the excerpt | `_rust.py:8-11` | diffed against `d89684561` | supported |

## It competes in someone else's harness

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| two of the 12 backends, a classifier and a regressor, same interface as XGBoost and LightGBM, selectable per request | § It is not a toy, corrected 2026-09-14 | `BackendName` has `cleargbm`; `RegressorBackendName` has `cleargbm_reg`, added in `5ad9b57e3` on 2026-08-22; `backends/cleargbm/{backend,regressor}.py` | **stale, fixed**: the article said "one of the model backends" and the page "one of the eleven"; two of twelve since 2026-08-22 |
| evaluated on the same datasets through the same machinery | § It is not a toy | the covenant-radar audit | supported |
| nine merged patches into LightGBM | § The related credential; the lightgbm-contributions page | audited in `lightgbm-contributions/audit.md` | see that audit |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| the page pins the retirement to its commit and separates it from a packaging change four weeks later | footnote 1, `f7c61172` and `ea7835d2` | 2026-07-21 to 2026-08-17 is 27 days | supported |
| a typed Python API surface remains and has grown by about half since mid-August | footnote 1: 2,380 on 2026-08-17, 3,641 on 2026-09-11 | `find libs/cleargbm/src -name '*.py' -exec cat {} + \| wc -l` = 3641 on 2026-09-14; 3641 / 2380 = 1.53 | **understated, fixed**: the article had said "about a third", which the page's own footnote phrase "rotted by a third" had been read backwards; 2,380 is a third less than 3,641, and 3,641 is half more than 2,380 |
| no benchmark claimed | this article | | supported |

## Sources block

Every link probed 200 on 2026-09-14: `libs/cleargbm`, `libs/cleargbm_rs`,
`Cargo.toml`, commit `f7c61172`, `_rust.py`, `ensemble.py`,
`covenant_ml/backends/cleargbm`, all at `d89684561` except the commit.
