# `fleet.json` — the contract between the bot fleet and this page

This page renders one file and nothing else. `tankpit/` writes that file;
the page never talks to the fleet, never proxies, and never reaches the
machine the bots run on.

**Schema version 3.** Version 3 admits `view.kind == "stream"`; a
version 2 page requires `none` and refuses anything else, so a document
carrying a stream is not a version 2 document.

Every field is decoded from a live fleet
manager response. Version 1 was hand-authored ahead of the publisher, on
the theory that the page was the hard thing to agree on and a schema
would fall out of it. The schema that fell out disagreed with the running
manager in six ways, each caught the first time the publisher was pointed
at port 27300:

| v1 said | The manager actually sends |
|---|---|
| `manager_boot_id` as an int | `boot`, a **string** |
| `role: "line"`, `role: "scout"` | only `fighter` / `gatherer` — a spawn with `line` is rejected 400 |
| three doctrines | four; `swarm` was missing |
| hex colours (`#5ecb71`) | CSS `rgb(57, 255, 20)` strings |
| HUD without `dealt` / `taken` | both present on every frame |
| `hud.available: true` beside the fields | a present frame carries **no** `available` key at all |

The lesson is recorded rather than quietly fixed: a contract written
against imagination is a guess with a table around it. Payloads captured
from the running manager now live in `tests/tankpit_payloads.py` and the
decoders are tested against those bytes.

## Where the fields come from

The roster is `GET /bots` on the fleet manager (port 27300), which
returns `FleetBotDict` — `instance`, `account`, `role`, `room`, `troop`,
`doctrine`, `pid`, `alive`, `returncode`, `kills`, `seconds`,
`started_ms`. The HUD is `GET /bots/{instance}/hud`, one call per bot.

**`pid` is deliberately NOT in this schema.** It is an operational detail
about the host and has no business on a public page.

**There is no `/stats` data here.** The endpoint exists and answers
`{"available": false}` until a run writes a digest; its populated shape
has never been captured, so nothing is modelled from it. The v1 fields
that would have come from it — `kills_scored`, `rank`, `fuel`, `extras`,
`state` — are **gone** rather than emitted as `null` forever. Live kills
come from the HUD frame, which is real.

## The one field that must not be copied straight across

`FleetBotDict.kills` is documented as *"Kill bound the child was spawned
with (0 unbounded)"*. **It is a limit, not a score.** A dashboard that
renders it as "kills" shows every freshly-spawned bot already holding its
maximum, which is wrong in the most flattering possible direction.

So the publisher renames it on the way out:

| Field | Meaning | Source |
|---|---|---|
| `kills_bound` | the ceiling the bot was spawned with; `0` = unbounded | `FleetBotDict.kills` |
| `hud.frame.kills` | kills actually made this session | the HUD frame |

`seconds_bound` is the same shape and the same trap — a duration limit,
not an elapsed time. Elapsed is computed by the page from `started_ms`.

## Top level

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | Bump on any breaking change. The page refuses a version it does not know rather than rendering a guess. |
| `generated_at` | ISO 8601 UTC, `Z` | Write time, not poll time; the page derives staleness from it. |
| `boot` | string | The manager's boot id, verbatim. Changes on restart, so the page can notice a restart rather than showing continuity that did not happen. |
| `draining` | bool | The manager has been asked to shut its bots down. |
| `control.enabled` | `false` | Always. The manager's mutating routes are loopback-only. |
| `control.reason` | string | Why control is unavailable. Shown instead of dead buttons. |
| `bots` | array | Every managed instance, **alive or dead**. A finished run is part of what the fleet did. |

## Per bot

| Field | Type | Notes |
|---|---|---|
| `instance` | string | Artifact namespace; the stable id. |
| `account` | string | Demo account name. Never a ranked account. |
| `role` | `fighter` \| `gatherer` | Fleet role. |
| `room` | string | Per bot, not fleet-wide — nothing stops two bots sitting in different rooms. |
| `doctrine` | `skirmish` \| `swarm` \| `duelist` \| `passive` | Spawn-only — see below. |
| `troop` | string | Tank colour. |
| `alive` | bool | |
| `returncode` | int \| null | `null` while alive. A non-zero code is rendered as `exit N`, not flattened to "ended": a crash and a completed bounded session are different outcomes. |
| `started_ms` | int | Wall-clock spawn. Elapsed is computed from this. |
| `kills_bound` / `seconds_bound` | int | Limits. `0` = unbounded. |
| `hud` | object | **Required.** Two states, below. |
| `view` | object | **Required.** `{"kind": "none"}` or `{"kind": "stream", "url": …}` — see Frames. |

## `hud` — the decoded state, not a screenshot

Two states, and the publisher owns the discriminant:

- `{"available": false}` — the bot has written no tick yet. The card dims.
- `{"available": true, "frame": { … }}` — `frame` is the bot's own
  `hud.json`, passed through byte-for-byte.

The nesting exists because the manager returns that file **verbatim**, and
a real frame carries no `available` key of its own. The flag is the
publisher's; the numbers are the bot's. Flattening them would put a
publisher-invented key in the same object as measured values.

An earlier draft of this page published **JPEG screenshots** instead.
That was wrong and worth recording: a screenshot shows the game, and the
game is not the achievement — the decode is. The HUD shows `do`, `why`
and `tgt`, i.e. the bot stating its own reason for its current action,
which a screenshot cannot.

Frame keys:

| Key | Notes |
|---|---|
| `state_text` | Chip at top right, e.g. `COLLECTING`. |
| `mode_text` / `mode_color` / `mode_band` | The coloured band; CSS colour strings from the bot, not this page. |
| `pos_text` / `fuel_text` | Rendered verbatim. |
| `fuel_pct` / `fuel_color` | Drive the meter's width and colour. |
| `s0`–`s4` and `s0c`–`s4c` | Stock counts and their colours: AR, DU, MI, HO, RA. |
| `do_text` | Current action. |
| `sent_text` / `sent_color` | The one-glyph sent indicator. |
| `why_text` | **The bot's stated reason.** The most interesting field on the page. |
| `tgt_text` / `act_text` | Target and act. |
| `kills` / `hits` / `misses` / `rejects` / `dealt` / `taken` | Session counters, unlike `kills_bound`. |

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

## Frames — `none` and `stream`

Fleet children now serve their own video. They are spawned onto the
**service** entry rather than `bot/entry.py`, so `/video` and `/frame`
exist per child off the frame bus that was already there, and the fleet
manager relays one at `GET /bots/{instance}/video`.

The URL this schema publishes is always the **manager's relay**, never a
child. Children bind loopback inside the manager's container and only
`27300` is published; exposing a port per bot would put the fleet's
internal surface on the network to show a picture.

`multipart/x-mixed-replace` renders natively in an `<img>`, so there is
no player and no polling. The bytes are the game's own composited
canvases — which is what makes this 1:1 rather than a redrawing that can
drift. Capture does not need a visible window: `live_view.py` composites
in-page and calls `toDataURL`, so a headless containerized bot streams
exactly what a headed one does.

### Why `none` is still the normal state of the published file

**This page is served over HTTPS, and a browser will not load an
`http://127.0.0.1` stream into an HTTPS page.** Mixed content is blocked
outright. So a loopback URL baked into the document austinwagner.org
serves would be a permanently broken image for every visitor.

The publisher therefore emits a stream **only** when told where the
viewer can reach the manager, via `TANKPIT_VIDEO_BASE`. There is no
default and the manager's own address is not used as one — guessing it
is precisely the mistake that would put the broken image on the site.

Publishing video publicly needs an HTTPS route to the fleet manager,
which is an exposure decision, not a code change. Until one exists, the
public file says `none` and says it honestly.

## Regenerating

```
poetry run python -m tankpit.cli
```

Reads `http://127.0.0.1:27300` and rewrites `fleet.json`. Fails loudly if
the manager is down or answers something other than this contract: a
stale document that still looks current is worse than a failed run.

To publish streams as well, name a root the viewer's browser can reach:

```
TANKPIT_VIDEO_BASE=http://127.0.0.1:27300 poetry run python -m tankpit.cli
```

That value is right for viewing locally over HTTP and wrong for the
public HTTPS site, which is why it is a deliberate argument rather than a
default.
