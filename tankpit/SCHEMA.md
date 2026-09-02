# `fleet.json` — the contract between the bot fleet and this page

This page renders one file and nothing else. Whatever writes `fleet.json`
owns this contract; the page never talks to the fleet, never proxies, and
never reaches the machine the bots run on.

Written before the publisher exists, deliberately. The page is the thing
whose shape is hard to agree on in the abstract, so it was built first
against hand-written data and the schema fell out of it. A publisher that
emits this needs no further negotiation.

## Where the fields come from

Most of the roster is `GET /bots` on the fleet manager (port 27300),
which returns `FleetBotDict` — `instance`, `account`, `role`, `room`,
`troop`, `doctrine`, `pid`, `alive`, `returncode`, `kills`, `seconds`,
`started_ms`. No new instrumentation is required for those.

**`pid` is deliberately NOT in this schema.** It is an operational detail
about the host and has no business on a public page.

## The one field that must not be copied straight across

`FleetBotDict.kills` is documented as *"Kill bound the child was spawned
with (0 unbounded)"*. **It is a limit, not a score.** A dashboard that
renders it as "kills" shows every freshly-spawned bot already holding its
maximum, which is wrong in the most flattering possible direction.

So this schema splits them:

| Field | Meaning | Source |
|---|---|---|
| `kills_bound` | the ceiling the bot was spawned with; `0` = unbounded | `FleetBotDict.kills` |
| `kills_scored` | kills actually made this session | telemetry, **not** `/bots` |

`seconds_bound` is the same shape and the same trap — a duration limit,
not an elapsed time. Elapsed is computed by the page from `started_ms`.

`kills_scored`, `rank`, `fuel`, `extras` and `state` come from the
per-bot telemetry / events stream rather than the roster call, so a
publisher has to merge two sources. If any of them is unavailable, emit
`null` rather than `0` — zero is a real value for all five, and imputing
it invents a fact.

## Top level

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | Bump on any breaking change. The page refuses a version it does not know rather than rendering a guess. |
| `generated_at` | ISO 8601 UTC | The page derives staleness from this, so it must be the write time, not the poll time. |
| `fleet.status` | `"live"` \| `"idle"` | `idle` means the manager is up with no bots, or is down. |
| `fleet.room` | string | Always `"Practice"` for the public demo. Rendered so a reader can see it, because the room is the safety property. |
| `fleet.manager_boot_id` | int | Changes when the manager restarts; lets the page notice a restart rather than showing continuity that did not happen. |
| `fleet.bots_max` | int | The concurrent cap. Shown so the page can render "3 of 5" honestly. |

## Per bot

| Field | Type | Notes |
|---|---|---|
| `instance` | string | Artifact namespace; the stable id. |
| `account` | string | Demo account name. Never a ranked account. |
| `doctrine` | `skirmish` \| `swarm` \| `duelist` \| `passive` | Spawn-only — see below. |
| `troop` | string | Tank colour. |
| `role` | string | Fleet role. |
| `alive` | bool | |
| `returncode` | int \| null | `null` while alive. |
| `started_ms` | int | Wall-clock spawn. Elapsed is computed from this. |
| `kills_bound` / `seconds_bound` | int | Limits. `0` = unbounded. |
| `kills_scored` / `rank` / `fuel` / `extras` | int \| null | Live values. `null` when unknown. |
| `state` | string | Short human-readable activity, e.g. `foraging`, `engaging`, `ended`. |
| `hud` | object | **Required.** The per-tick HUD dict — byte-for-byte what `GET /bots/{i}/hud` returns. See below. |

## `hud` — the decoded state, not a screenshot

`hud` is the same dict the operator's fleet page feeds to its cards, and
this page renders it with the same markup and CSS. Publishers must pass
it through unchanged; reshaping it here would make the two renderings
disagree about what a key means.

An earlier draft of this page published **JPEG screenshots** instead.
That was wrong and worth recording: a screenshot shows the game, and the
game is not the achievement — the decode is. The HUD shows `do`, `why`
and `tgt`, i.e. the bot stating its own reason for its current action,
which a screenshot cannot.

Keys, matching `service/fleet_page.py::paintHud` exactly:

| Key | Notes |
|---|---|
| `available` | `false` means the bot has no tick to report yet; the card dims and every other key is ignored. |
| `state_text` | Chip at top right, e.g. `ENGAGED`. |
| `mode_text` / `mode_color` / `mode_band` | The coloured band; colours come from the bot, not this page. |
| `pos_text` / `fuel_text` | Rendered verbatim. |
| `fuel_pct` / `fuel_color` | Drive the meter's width and colour. |
| `s0`–`s4` and `s0c`–`s4c` | Stock counts and their colours: AR, DU, MI, HO, RA. |
| `do_text` | Current action. |
| `sent_text` / `sent_color` | The one-glyph sent indicator. |
| `why_text` | **The bot's stated reason.** The most interesting field on the page. |
| `tgt_text` / `act_text` | Target and act. |
| `kills` / `hits` / `misses` / `rejects` | Footer counters — session totals, unlike `kills_bound`. |

### The markup is generated, not copied

`hud.js` carries `HUD_CSS` and `HUD_BODY`, extracted from
`browser/overlay_hud.py` by `regen-hud.py` and re-scoped with the same
three transforms `fleet_page.py::_CARD_CSS` applies — class selector,
`position:relative` so cards tile instead of stacking in one corner, and
the FLAG button hidden because a flag belongs to whoever is watching the
live window.

It is vendored because a static site cannot read a Python string, not
because a second copy is wanted. The generator records the source's
sha256, and `python tankpit/regen-hud.py --check` exits non-zero when
the copy is stale. A transform target that stops matching is a hard
error, not a silent skip.

## Doctrine is spawn-only

`TANKPIT_DOCTRINE` is resolved once at process start
(`fleetshare/role.py`), and `POST /mode` accepts only `manual_mode`. So a
doctrine change is **stop + respawn**, not a live toggle. The page must
present it that way — a control that silently restarts a bot while
looking like a setting is a lie about what happened.

## Frames

Published as files beside this one, not proxied. One viewer and a hundred
viewers cost the same, and no visitor request ever reaches the machine
running the bots. A stale frame is better than a live proxy: it fails by
being old rather than by exposing a control surface.
