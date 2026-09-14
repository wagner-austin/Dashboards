# Audit: lightgbm-contributions

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale`, `overclaim`, `unsourced`, `framing`. Re-run whenever the cited page's
`fact_checked` moves.

Audited 2026-09-14 directly against the GitHub API. Source page:
`me/lightgbm-contributions` (fact_checked 2026-08-26 when the article shipped;
re-verified, extended and now 2026-09-14).

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| nine pull requests reviewed and merged, including a C++ networking bug in distributed training | § The contributions; § Two more open | `gh api --paginate 'search/issues?q=is:pr+author:wagner-austin+repo:lightgbm-org/LightGBM'`: twelve items, nine with `merged_at`; #7137 is `[c++] fix socket timeout on POSIX systems` | supported |
| then at microsoft/LightGBM, now its own organisation | footnote 1, the 301 from the old path | `api.github.com/repos/microsoft/LightGBM` redirects | supported |
| 9 merged between January and March 2026 | footnote 2, the `merged_at` list | 2026-01-05 (#7115) to 2026-03-01 (#7131) | supported |
| 12 authored: 9 merged, 2 open, 1 closed | § Two more open | the same query: #7138 and #7178 open, #7139 closed unmerged | supported |
| C++ and Python: networking, test coverage, typed scikit-learn predict path | § The contributions table | titles of the twelve | supported |

## What the patches did

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| 7137: socket timeout broken on POSIX because setsockopt was given the wrong type | table row; footnote 2 | PR body, "On POSIX systems, setsockopt(SO_RCVTIMEO) requires a struct timeval, not an int ... silently fails with EINVAL" | supported |
| 7131, 7133, 7130 rows | table rows | PR titles | supported |
| 7115 through 7118: TypeGuard, return types on the predict methods, DTypeLike, Literal | table row, corrected 2026-09-14 | titles of #7115, #7116, #7117, #7118 | supported |
| 7119: positional arguments for np.arange in the predictor | table row, added 2026-09-14 | title of #7119, "use positional args for np.arange in _InnerPredictor" | **overclaim, fixed**: the article and page had folded it into the annotations range |
| the old call failed with EINVAL and the timeout was never set; 11 lines added and 2 removed in the wrapper | § The contributions, the 2026-09-14 paragraph; footnote 2 | `gh api repos/lightgbm-org/LightGBM/pulls/7137/files`: `socket_wrapper.hpp` +11/−2, `linkers_socket.cpp` +1/−1 | supported |
| the excerpt | the `SetTimeout` hunk of `socket_wrapper.hpp` in #7137 | copied from the files listing's `patch`; merge commit `80ab6d3ce2e71959a827cb41771bb887c6f09116` | supported; the constant 1000 inside it is a unit conversion, declared as a non-figure |

## Nine of twelve, and where the three went

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| all three unmerged are C++ in the distributed-training path | § Two more open | titles of #7138, #7139, #7178 all begin `[c++]` and name distributed connections | supported |
| 7139 closed; 7178 the same fix reopened; 7138 open in the same area | same | states and titles from the API | supported |
| nine of twelve with the failures in the hardest area is the more useful number | framing, from the page | | framing |

## Why a merged patch is different evidence

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| review by maintainers with no reason to be generous | framing | `merged_by.login` is a maintainer on all nine | framing |
| checkable in ten seconds | the merged-PR query | probed 200 | supported |
| companion evidence: ClearGBM benchmarked against LightGBM in one harness | § The pairing worth naming; the cleargbm page | audited in `gradient-boosting-twice/audit.md` | supported |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| the page carries the query and the date it was last re-run, 2026-09-14, every count unchanged | footnotes 1 and 2 | | supported |
| the old API path answers a permanent redirect with no body and a naive script reports zero | footnote 1 | | supported, as the page's own recorded incident |
| 7119 was folded into the annotations row until 2026-09-14 | this audit | | supported |

## Sources block

Every link probed 200 on 2026-09-14: the author query, the merged filter, #7137,
its files view, #7139, #7178, #7138.
