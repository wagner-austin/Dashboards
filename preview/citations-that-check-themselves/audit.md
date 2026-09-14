# Audit: citations-that-check-themselves

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale` (wiki was right once and was corrected before this article was
republished), `overclaim`, `unsourced`, `framing` (author's connective prose,
no factual content). Re-run whenever a cited page's `fact_checked` moves.

Audited 2026-09-14. Source pages: `mcps-codebase/wiki-check-audit-chain`
(fact_checked 2026-09-14), `mcps-codebase/wiki-structure-guards` (2026-09-14),
`me/public-dashboards` (2026-09-14), `me/hpc3-cli` (2026-09-11).

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| 18 research wikis share one audit engine | audit-chain § Registered-wiki triangle, "18 registered wikis" | `grep -cE '^\s*slug: "' mcp-shared/src/source-registry/wikis.ts` = 18 at `e8228062` | **stale, fixed**: article and page both said seventeen; `chat` registered 2026-09-12 (`8cf98b03`) |
| each declares which kind of proof its citations owe | audit-chain § Five source-contract kinds, "Every wiki declares one contract kind in its audit.config.ts" | `WIKI_SOURCE_CONTRACT_KINDS` in `packages/wiki-check/src/pure/source-contract/kinds.ts`, pin `6d88d5b0` matches HEAD | supported |
| a claim that cannot be checked that way fails the write | audit-chain § Two severity tiers, "Blocking (in-transaction rejection) — the write fails with every finding named" | `wiki-mcp/src/write-core.ts` pin `dbdf6d0c` matches HEAD | supported |
| notes rot silently; a citation that pointed at something real is indistinguishable later | framing | | framing |
| 5 source-contract kinds | audit-chain § Five source-contract kinds, list of five | `kinds.ts` lines 51 to 55 name five | supported |
| a separate guard checks the container rather than the claims | structure-guards § title and § Two design decisions | `packages/wiki-check/tests/registered-wikis.corpus.test.ts` pin `7f8962f9` matches HEAD | supported |
| one wiki of papers, 2 captured, one vault, 10 codebase, 4 pinning nothing | audit-chain § Registered-wiki triangle digits | `grep -oE 'sourceContractKind: "[a-z0-9-]+"' \| sort \| uniq -c` on wikis.ts: 10 / 4 / 2 / 1 / 1 | **stale, fixed**: article said nine codebase wikis; page said three codebase and one external-urls |
| TypeScript, PostgreSQL, hybrid dense + BM25, MCP tools | audit-chain § title and § Consumption pattern; MCPs CLAUDE.md § Wiki first (dense HNSW fused with BM25) | `packages/wiki-search/src/fusion.ts` exists | supported |
| same rules run on the filesystem, in the write transaction, through a tool | audit-chain § opening list, "Three surfaces, one implementation" | the three consumers are pinned on the page and match HEAD | supported |

## One contract per kind of evidence

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| table row PDF archive: local PDF, SHA-256, vault document id | audit-chain § Five source-contract kinds, `pdf-corvis` bullet | `canonical-contracts.ts` pin `138fd2da` matches HEAD | supported |
| row Captured HTML: saved page, hash, URL, capture date | same section, `html-sha256` bullet | same | supported |
| row Document vault: query must resolve to at least one hit | same section, `vault-corvis` bullet | same | supported |
| row Code paths: source paths plus blob hash per file | same section, `code-paths` bullet | `model-trainer-composition-ceiling.md` frontmatter in API at `c447b0c` carries `source_git_blobs`; each pin re-hashed against that commit and matches | supported |
| row External URLs: nothing, explicitly, no local archive, live URLs and repo paths | same section, `external-urls` bullet, "pins nothing, because there is no local archive. Sources are live external URLs and repo paths" | the four are me, offline-ai, bookshelf, chau | **overclaim, fixed**: the article had called all four "autobiographical or personal collections", which the wiki does not say |
| every footnote must name a page, section, URL, line anchor or commit | same bullet, "every footnote names a page, section, URL, path.ts:120 anchor or commit sha" | | supported |
| the code excerpt | copied from `API/wiki/pages/model-trainer-composition-ceiling.md` at `c447b0c`, lines 8 to 17, two of four paths and pins | `git rev-parse c447b0c:<path>` equals each shown pin | supported |

## The rule that made this page possible

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| change a cited file and the pin stops matching | audit-chain § Five source-contract kinds, "source_git_blobs recording each cited path's blob hash so downstream drift surfaces" | `git-blob-hash-pin` rule named on the page | supported |
| every figure on this site is bound to a wiki page and section, re-resolved before deploy | `Dashboards/scripts/provenance_gate.py` module docstring; this manifest | `make check` in Dashboards runs the gate | supported |
| first 14 articles, 14 of 20 source pages wrong, every one high confidence | public-dashboards § Research write-ups, the table and the paragraph naming the six not in it | the fourteen manifests bind to twenty distinct pages; the table's fixing commits; each page's frontmatter read `confidence: high` before its fix | **stale, fixed twice**: the article said four when written and eight at the start of the audit pass; the pass itself found six more |
| one described an actively running project as mothballed | me/rustedwarfarebot, correction note under its status section; commit `99c7af0` body "described an active project as mothballed" | 274 commits since 2026-08-20 per that commit | supported |
| one said "eight commands" while naming seven, against a real 15 | me/hpc3-cli § Shape and its footnote, "while naming seven, against a real 15" | `7151d84` | supported |
| callout: the guard caught a moved page leaving 858/857, 70/69, 37/38, 11/12 | structure-guards § A page that moved between two wikis | MCPs run `34637586320` log-failed output, read 2026-09-14, four lines verbatim | **unsourced, fixed**: the incident was recorded on no wiki page until 2026-09-14 |

## Why an agent needs this more than a person does

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| a model summarising a corpus produces something plausible whether or not the corpus supports it | framing (the argument for the gate) | | framing |
| the same rules run in the write transaction, on the filesystem, through the tool; a failing claim does not land | audit-chain § opening list and § Two severity tiers | pins match HEAD | supported |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| the codebase wiki pins the blob hashes of the audit engine it describes | audit-chain frontmatter `source_git_blobs` | every pin re-checked against HEAD 2026-09-14; two had drifted (`packages/wiki-check/src` tree, `wikis.ts`) and were re-pinned | **stale, fixed** |
| 77 rules on 2026-09-14 | audit-chain § Two severity tiers | `CHECK_RULES` in `packages/wiki-check/src/checks/types.ts` has 77 entries; blob `d7960050` unchanged since the 2026-09-11 reading | supported |
| grew by 11 between two readings without the audit noticing | same section; footnote 4, 66 on 2026-08-14 to 77 on 2026-09-11 | | supported |
| none of this checks whether a claim is true | framing, and the page's own scope statement | | framing |

## Sources block

| link | checked |
|---|---|
| API/wiki tree at `c447b0c` | 200 on 2026-09-14; `git rev-parse origin/main` = `c447b0c4` |
| API wiki page blob at `c447b0c` | 200 |
| Dashboards `scripts/provenance_gate.py` at `ebe6085` | 200 |
| this article's `provenance.json` on main | resolves after push |
