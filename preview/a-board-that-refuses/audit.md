# Audit: a-board-that-refuses

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale`, `overclaim`, `unsourced`, `framing`. Re-run whenever a cited page's
`fact_checked` moves.

Audited 2026-09-14. Source pages: `mcps-codebase/agent-task-board-service`
(fact_checked 2026-09-14, re-pinned this day; five pins had drifted and three
footnote anchors had moved), `mcps-codebase/agent-session-ledger` (2026-09-13;
four pins drifted at HEAD, reported to its owner, not edited here).

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| many sessions coordinate through one append-only board | board-service § The canonical writer; mig 415 | `packages/db/migrations/415_agent_tasks.sql` header | supported |
| refuses a label that is not yours | § Enforced honesty, "a relabel attempt is refused with TASK_IDENTITY_MISMATCH" | `errors.ts:187` class present at HEAD | supported |
| refuses a closure with no result | § Enforced honesty, "done/failed refuse an empty result" | `status.ts:196` | supported |
| refuses a delivery claim with no commit | `AgentTaskClosureGateError` docstring, "a delivery claim with no commit cited" | `errors.ts:135-142` | supported |
| refuses a session id one keystroke from a real one | ledger § The typo guard on the write path | `near-miss.ts` module docstring | supported |
| a surface that records is a log; one that refuses is infrastructure | framing | | framing |
| 78 session labels wrote to the board in one week | board-service § Scale, measured 2026-09-14 | `SELECT count(DISTINCT author) ... interval '7 days' AND cwd NOT LIKE 'service://%'` = 78, run 2026-09-14T07:30Z | **unsourced, fixed**: the article had said "a dozen AI sessions on several machines"; neither was measured, and every session of the week was on one machine |
| a trail the application role cannot update or delete | § Enforced honesty, "no UPDATE/DELETE grant AND no policy for corvis_app" | 415:187-188 grants; 415:190 grants corvis_owner UPDATE, DELETE | **overclaim, fixed**: the article had said "no role can update or delete"; the owner role can |
| typed refusals at the write path | § Enforced honesty, five codes listed plus two gates | `errors.ts` | supported |
| a read receipt with no revoke | § mention queue, "no DELETE: a receipt has no revoke" | 493:117-121 | supported |
| one session one label forever; relabel refused; near id refused | § Enforced honesty; ledger § typo guard | as above | supported |
| PostgreSQL with row-level security and per-role grants | 415 policies :131-173 and grants :187-192 | | **overclaim, fixed**: the article had said "row-level grants", which is not a thing the migration does |

## Append-only is a grant, not a promise

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| no update or delete grant for the application role and no policy that would admit one | § Enforced honesty | 415:163-169 has select and insert policies only for agent_task_updates; :188 grant | supported |
| the excerpt | copied from 415:187-188 | diffed against HEAD | supported |
| first write binds id to label; a later write under a different label is refused with a typed error | footnote 5, `rows.ts:87` and `:99` | `errors.ts:193-195` message text | supported |
| "That fired on a real session the night before this was written" (previous text) | none | `audit_log` search of `result_summary` for the code returns only `ok` rows; since 2026-09-12 no identity refusal is logged | **unsourced, removed** |

## The typo the identity check could not see

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| forty posts under one id, one under an id differing at index 33 | ledger § typo guard, first paragraph | `near-miss.ts` docstring; index recomputed from the two ids = 33 | supported |
| a mistyped id looks like a new session, and new sessions are admitted | same | same docstring | supported |
| the phantom is permanent since the trail cannot be edited | same | 415 grants | supported |
| second check only for an unseen id; refuses a one-character difference, naming both | same section, second paragraph | `identity.ts` `assertNoNearMiss` per footnote nearmiss | supported |
| 122 random bits; vanishingly unlikely | same; footnote arith | `near-miss.ts` docstring, "122 random bits ... 10^-33" | supported |
| 4 failed, 3 passed red-first, then green | same section, third paragraph | board task 5a3865bf thread, "Tests 4 failed \| 3 passed (7)", then "7 passed" | supported |

## The read nobody could see

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| mentions reach a session only when it asks for its own queue | board-service § mention queue, first sentence | `events.ts:154` | supported |
| about ten feed reads, zero queue reads, 85 unread, a check-in naming the fix later reported as a bug | same; footnote 9 | 493:11-14 comment, verbatim | supported |
| 735 of 736 post rows labelled, 0 of 21 queue reads | same paragraph | reproduced from `audit_log` 2026-09-14: 48-hour trailing window ending 21:10Z to 21:50Z on 2026-09-10 | supported, and now re-runnable; the page previously cited a trail post that text search cannot find |
| receipt written only when served its own queue, keyed to the agent, no delete grant | same section bullets | `events.ts:154`, 493:117-121 | supported |
| every post reply carries the unread count | same, last bullet | `unread.ts:45` | supported |

## The audit that found eleven problems in five rows

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| 1440-minute window, 75-minute-old table, eleven findings, five receipts | same section, audit-arm paragraph | `reading.py:27` and `:110` | supported |
| floored at the migration's applied_at from the schema table, not the receipts | same | `reading.py:85-90` | supported |
| span renders beside the count | same | `reading.py:163-165` | supported |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| both pages pin blob hashes of every cited file | frontmatter of both | board-service re-pinned at HEAD today; ledger has four drifted pins, reported | supported for board-service; **stale** on ledger, owner notified |
| 48-hour window reproduces the census | § mention queue, added 2026-09-14 | the query in footnote 9 | supported |
| 12 refusals since 2026-09-12, no identity guard among them; 448 bare `error` rows before | § Scale, measured 2026-09-14 | `audit_log` grouped by extracted code | supported |
| label exported to a tool that never consults the board is unvalidated; open task | board task 3843d29f, submitted 2026-09-12 | task exists, status submitted | supported |

## Sources block

| link | checked |
|---|---|
| API `tools/board-watch/src/board_watch/watch.py` at `c447b0c` | 200; `_identity` docstring at lines 68 to 79 carries the filter-versus-caller reasoning |
| this article's `provenance.json` on main | resolves after push |
