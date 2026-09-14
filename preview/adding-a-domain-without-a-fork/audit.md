# Audit: adding-a-domain-without-a-fork

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale`, `overclaim`, `unsourced`, `framing`. Re-run whenever the cited page's
`fact_checked` moves.

Audited 2026-09-14 against API `d89684561`. Source page: `me/covenant-radar`
(fact_checked 2026-09-12 when the article shipped; corrected and now
2026-09-14).

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| built a covenant risk service, generalised so a new subject is a registration | page intro; § What adding the second and third domains changed | `domains/registry.py`, `DomainProtocol` | supported |
| two more domains added without touching the shared training or explanation libraries | § What adding..., "0 files under libs/covenant_ml or libs/covenant_nn in either" | `git show --stat 71da28c30 \| grep -c libs/covenant_` = 0; same for `c3d9ad8e5` | supported |
| "without editing the shared training, explainability or streaming machinery at all" (previous text) | page intro, previous text "They did not" | `git show --numstat` on the two commits: `protocols.py` +37/-62, `streaming/generic_worker.py` +4/-6, `domains/registry.py` +40/-17, `generic_worker_entry.py` +38/-17 | **overclaim, fixed**: the streaming machinery and the protocol were edited; only the libraries were not |
| what they changed was the seam they plug into | § What adding..., rewritten | the four diffs | supported |
| weather and esports behind one protocol; covenant served directly, not a plug-in | page intro corrected 2026-09-12; footnote 3 | `ls -d domains/*/` = esports, weather; `grep -rn "class .*Domain\b" src` = two classes | supported |
| 12 backends: 7 classifiers, 5 regressors | § Twelve model backends; footnote 1 | `BackendName` Literal has 7 members at `types.py:17`; `RegressorBackendName` has 5 at `types_regression.py:128`; seven backend directories across the two libraries | supported |
| 40 real public datasets | § The rest of the machinery; footnote 2 | `ls -d data/external/*/ \| wc -l` = 40 | supported |
| Python, PyTorch, XGBoost, LightGBM, Optuna, Kafka on Confluent Cloud | § The rest of the machinery | `covenant_ml/optimizer/` (Optuna), `streaming/consumer.py` (Kafka), backend directories | supported |

## The claim, stated exactly

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| each plug-in implements one protocol and registers | page intro; `domains/__init__.py` docstring | `protocols.py:123`, `registry.py` | supported |
| table: weather 0 library files; protocol +37/-62; worker +4/-6 | § What adding...; footnote 4 | `git show --numstat 71da28c30` | supported |
| table: esports 0 library files; registry +40/-17; entry +38/-17 | same | `git show --numstat c3d9ad8e5` | supported |
| decode-and-extract became one call the domain owns | footnote 4, the worker diff | `git show 71da28c30 -- streaming/generic_worker.py` | supported |
| construction deferred so an esports-only deployment never loads weather's fitted state | footnote 4, quoting the registry docstring | `git show c3d9ad8e5 -- domains/registry.py` | supported |
| the excerpt | `domains/protocols.py:123-129` | diffed against `d89684561` | supported |

## Rules and models kept deliberately apart

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| compliance is exact rule evaluation; breach risk is the learned path; separate code paths | § Deterministic rules and learned models kept apart | section text | supported |
| conflating them would make a compliance answer probabilistic | same section's argument | | framing, from the page |

## Substitutable underneath, stable on top

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| twelve backends behind one interface, including from-scratch gradient boosting in the same harness | § Twelve model backends | `backends/cleargbm/` present in the Literal and as a directory | supported |
| permutation for anything, SHAP tree for tree models, plain and integrated gradients for neural | § Explainability adapts to the backend | `explainers/__init__.py:4-7` lists permutation (all), gradient and integrated_gradients (neural), shap_tree (tree) | supported; the article had said "gradient-based attribution" and now names both gradient explainers |
| 40 real datasets; synthetic data flatters everything | § The rest of the machinery | as above | supported; the second clause is framing |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| the page records how each count is reproduced and three traps | footnotes 1 and 2 | | supported |
| no accuracy figures claimed | this article | | supported |
| headline corrected twice: three plug-ins to two on 2026-09-12; "not at all" to the measured diffs on 2026-09-14 | me-wiki `61b3fc6` and `ad0c52b` | | supported |

## Sources block

Every link probed 200 on 2026-09-14: the service tree, `domains/`, the two
commits, `covenant_ml/types.py`, `types_regression.py`,
`explainers/__init__.py`, `data/external/`, `domains/protocols.py`, all at
`d89684561` except the commits.
