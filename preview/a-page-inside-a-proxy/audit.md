# Audit: a-page-inside-a-proxy

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale`, `overclaim`, `unsourced`, `framing`. Re-run whenever the cited page's
`fact_checked` moves.

Audited 2026-09-14. Source page: `mcps-codebase/corvis-dashboard-human-surface`
(fact_checked 2026-09-11 when the article was written; five pins had drifted and
five cited files were unpinned; corrected and re-pinned 2026-09-14, now
fact_checked 2026-09-14). The article was written by another session on
2026-09-13 with bare `<h2>` headings and no panels; restructured to the site
template in this pass, with no change to the argument.

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| a proxy that only spoke to machines now renders a page for a person on its own hostname | page title and § Why a distinct origin | `cloudflared/config.yml` ingress entry for `corvis.austinwagner.org`; live probe 2026-09-14 answers 302 to Keycloak | supported |
| every safety question has one implementation | § It is an index and a detail page, the `selectWorkspace` paragraph | `dashboard-core.ts:253-257` | supported |
| the one question that briefly had two answers cost a 403 that named no cause | § A hostname must be declared TWICE | `auth-server.ts:226-234` comment block records the 2026-09-11 measurement | supported |
| the fix is a guard that is itself guarded | same section, "The guard is itself guarded" | `mcp-proxy/tests/allowlist-sources.architecture.test.ts` | supported |
| one route serves every view | § index and detail, "One route serves all of it" | `dashboard-routes.ts:85-92` docstring, three pages | **stale, fixed**: the article said "both views"; a third arrived in `bfdf1436` |
| one selector decides whether an account may see a workspace | same | `selectWorkspace` docstring | supported |
| three dynamic sources feed the allowlist; hostname declared in two files | § declared TWICE, first paragraph | `auth-server.ts:236-241`; `proxy-config.json:243` and `cloudflared/config.yml` | supported |
| the one list needing the canonical registry was dropped rather than paid for with a 29-service rebuild | § The view model, rewritten 2026-09-14 | `dashboard-core.ts:44-50` "NO WIKI LIST"; `bfdf1436` | **stale, fixed**: the article presented the tenant-row wiki list as a current design; the list had been removed the day the page was written |
| TypeScript, Express, Keycloak, PostgreSQL, Cloudflare Tunnel, Docker | page § shipped footnote and stack throughout | `auth-server.ts` imports, `cloudflared/` | supported |

## One question, one answer

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| index says what you belong to and how much is in each; tables one click away via a query parameter | § index and detail, first paragraph | `dashboard-html.ts:60-72` badges; `WORKSPACE_QUERY_PARAM` in routes | supported (the second badge is now a family count, not a wiki count) |
| detail view is a pure selector over the index's result, not a second lookup | § index and detail, `selectWorkspace` paragraph | `dashboard-core.ts:230-257` | supported |
| two implementations of one authorization question drift | same | framing supported by the docstring | supported |
| a foreign slug and a nonexistent slug both return 404, cannot enumerate tenants | same, last sentence | `dashboard-page.ts:266`; `dashboard-page.test.ts:326` "gives the same answer for a foreign workspace and a nonexistent one" | supported (the wiki cited the wrong file; corrected) |

## Why a separate origin

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| Web Push subscriptions are scoped to an origin and die if it moves | § Why a distinct origin; footnote origin, quoted from `cloudflared/config.yml` | the comment is in the file at the pinned blob | supported |
| existing hostname carries registered clients and OAuth callbacks | same comment | | supported |
| several hostnames already resolved to that container | footnote ingress: `mcp.`, `fiesta.`, `games.` all to `http://mcp-proxy:8000` | `cloudflared/config.yml` | supported |

## The 403 that named nothing

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| allowlist from three sources: service name, OAuth resource URL hostname, every proxied host | § declared TWICE; footnote allowlist | `auth-server.ts:199-215` comment and `:236-241` call | supported |
| a served hostname is none of those; refused before any handler | same; footnote measured | `auth-server.ts:226-234` | supported |
| 302 on `mcp.`, 403 on `corvis.` | same section table; footnote measured, 2026-09-11T04:17Z via the LB with explicit Host | the measurement is the author's, recorded in the page and in the code comment; not re-run since the fix makes it unreproducible without reverting | supported |
| the boot log said the route was registered | footnote measured, `Dashboard route registered (/dashboard)` | `auth-server.ts:520` | supported |
| cannot borrow the proxied-host mechanism, which requires a backend | footnote field, `types.ts:365` docstring | `types.ts:365` | supported |
| own config field declared beside the other sources | same | `dashboardHostnames` in `proxy-config.json:243` | supported |
| the excerpt | `auth-server.ts:236-241` | diffed against HEAD | supported |

## The guard is itself guarded

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| validator refuses a hostname routed at the proxy that no declaring field carries | footnote bound, `checkProxyHostnameDeclared`, rule 8 | `cloudflared/src/validator.ts`, pin unchanged | supported |
| deleting the declaration reproduces the incident as a lint failure | footnote reproduced, the exact message | author's measurement 2026-09-11; message text present in `validator.ts` | supported |
| a fourth source would pass silently; the argument list is pinned; a behavioural test could not catch it | footnote paired | `allowlist-sources.architecture.test.ts` docstring lines 13 and 38 | supported |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| the page pins every source file by blob hash | frontmatter | ten pins at HEAD after this pass; five files cited by line were unpinned before it | **stale, fixed** |
| the wiki list was removed the same day; the route grew a third view; the header changed shape | § view model (rewritten); `bfdf1436`; `64e07a17` | commit log for `mcp-proxy/src/dashboard-*.ts` since 2026-09-11 | supported |
| every claim re-verified against current code 2026-09-14 | this file | | supported |

## Sources block

| link | checked |
|---|---|
| `https://corvis.austinwagner.org/dashboard` | 302 to `auth.austinwagner.org` on 2026-09-14 |
| this article's `provenance.json` on main | resolves after push |
