"""Typed records for the TankPit fleet publisher.

Every record crossing the fleet manager boundary is decoded through a
``require_*`` validator before use, so an upstream change surfaces as a
precise error naming the field rather than as a wrong number on a public
page. Decoders raise :class:`TankpitDecodeError` and never substitute a
default: a payload that does not match is an error, not something to
paper over.

The shapes here were captured from a running fleet manager
(``v0.1.0-bc45e3e1``) rather than read off the source, after a
hand-authored sample file was found to disagree with the live API in six
separate ways -- ``boot`` typed as a number, two invented ``role``
values the API rejects outright, a missing ``swarm`` doctrine, two
missing HUD counters, hex colours where the bot emits ``rgb(...)``, and
an ``available`` key inside a HUD frame that the manager never sends.
"""

from typing import Literal, TypedDict

# The fleet manager binds loopback only; the publisher runs beside it.
FLEET_BASE_URL = "http://127.0.0.1:27300"

# Engagement doctrines the manager accepts, from ``GET /doctrines``.
FLEET_DOCTRINES = ("skirmish", "swarm", "duelist", "passive")

# Fleet roles the manager accepts, from the 400 it returns on a bad one.
FLEET_ROLES = ("fighter", "gatherer")


class TankpitDecodeError(ValueError):
    """Raised when a fleet manager payload does not match the expected shape."""


def require_object(payload: object, context: str) -> dict[str, object]:
    """Read a required JSON object.

    Args:
        payload: Value decoded from JSON.
        context: Human-readable name of what was being decoded.

    Returns:
        The value as a string-keyed mapping.

    Raises:
        TankpitDecodeError: If the value is not a JSON object.
    """
    if not isinstance(payload, dict):
        raise TankpitDecodeError(f"{context}: expected an object, got {type(payload).__name__}")
    result: dict[str, object] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise TankpitDecodeError(f"{context}: object keys must be strings, got {type(key).__name__}")
        result[key] = value
    return result


def require_str(payload: dict[str, object], field: str, context: str) -> str:
    """Read a required string field.

    Args:
        payload: Decoded JSON object.
        field: Field name to read.
        context: Human-readable name of what was being decoded.

    Returns:
        The field value.

    Raises:
        TankpitDecodeError: If the field is absent or not a string.
    """
    value = payload.get(field)
    if not isinstance(value, str):
        raise TankpitDecodeError(f"{context}: {field!r} must be a string, got {type(value).__name__}")
    return value


def require_int(payload: dict[str, object], field: str, context: str) -> int:
    """Read a required integer field.

    Booleans are rejected even though Python treats them as integers.

    Args:
        payload: Decoded JSON object.
        field: Field name to read.
        context: Human-readable name of what was being decoded.

    Returns:
        The field value.

    Raises:
        TankpitDecodeError: If the field is absent or not an integer.
    """
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TankpitDecodeError(f"{context}: {field!r} must be an integer, got {type(value).__name__}")
    return value


def require_bool(payload: dict[str, object], field: str, context: str) -> bool:
    """Read a required boolean field.

    Args:
        payload: Decoded JSON object.
        field: Field name to read.
        context: Human-readable name of what was being decoded.

    Returns:
        The field value.

    Raises:
        TankpitDecodeError: If the field is absent or not a boolean.
    """
    value = payload.get(field)
    if not isinstance(value, bool):
        raise TankpitDecodeError(f"{context}: {field!r} must be a boolean, got {type(value).__name__}")
    return value


def require_optional_int(payload: dict[str, object], field: str, context: str) -> int | None:
    """Read a required field holding either an integer or null.

    ``returncode`` is null while a bot is alive and an exit code once it
    is not, so absence of a value is meaningful here rather than missing.

    Args:
        payload: Decoded JSON object.
        field: Field name to read.
        context: Human-readable name of what was being decoded.

    Returns:
        The field value, or ``None`` when the payload holds null.

    Raises:
        TankpitDecodeError: If the field is absent or is neither an integer nor null.
    """
    if field not in payload:
        raise TankpitDecodeError(f"{context}: {field!r} is required")
    value = payload[field]
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TankpitDecodeError(
            f"{context}: {field!r} must be an integer or null, got {type(value).__name__}"
        )
    return value


def require_list(payload: dict[str, object], field: str, context: str) -> list[object]:
    """Read a required array field.

    Args:
        payload: Decoded JSON object.
        field: Field name to read.
        context: Human-readable name of what was being decoded.

    Returns:
        The field value.

    Raises:
        TankpitDecodeError: If the field is absent or not an array.
    """
    value = payload.get(field)
    if not isinstance(value, list):
        raise TankpitDecodeError(f"{context}: {field!r} must be an array, got {type(value).__name__}")
    return value


class FleetBot(TypedDict):
    """One managed bot, as reported by ``GET /bots``.

    Mirrors the manager's own ``FleetBotDict``. There is deliberately no
    port field: fleet children run the bot entry point, which serves no
    HTTP, so no per-bot video or frame endpoint exists to address.

    Attributes:
        instance: Instance name, unique within the fleet.
        account: TankPit account the child was spawned with.
        role: Fleet role, one of :data:`FLEET_ROLES`.
        room: Room the child joined.
        troop: Tank colour the child was spawned with.
        doctrine: Engagement doctrine, one of :data:`FLEET_DOCTRINES`.
        pid: Child process id.
        alive: Whether the process was running at report time.
        returncode: Exit code once dead; ``None`` while alive.
        kills: Kill bound the child was spawned with; 0 is unbounded.
        seconds: Seconds bound the child was spawned with; 0 is unbounded.
        started_ms: Wall-clock spawn time in milliseconds.
    """

    instance: str
    account: str
    role: str
    room: str
    troop: str
    doctrine: str
    pid: int
    alive: bool
    returncode: int | None
    kills: int
    seconds: int
    started_ms: int


class FleetRoster(TypedDict):
    """The fleet as a whole, from ``GET /bots``.

    Attributes:
        boot: Manager boot id. A string upstream, kept a string here.
        draining: Whether a shutdown drain has been requested.
        bots: Every managed instance, alive or dead.
    """

    boot: str
    draining: bool
    bots: list[FleetBot]


class BotHud(TypedDict):
    """One tick's HUD frame, served verbatim from the bot's ``hud.json``.

    The bot writes this every tick and the manager returns the file
    unchanged, so this is the same card the operator sees locally. Colours
    arrive as CSS ``rgb(...)`` strings, not hex.

    Attributes:
        state_text: Coarse state label, e.g. ``COLLECTING``.
        mode_text: Current mode, e.g. ``COLLECT - PICKUP``.
        mode_color: CSS colour for the mode label.
        mode_band: CSS colour for the mode band behind the label.
        pos_text: Tile position as ``x,y``.
        fuel_text: Fuel as ``current/max``.
        fuel_pct: Fuel as a percentage of maximum.
        fuel_color: CSS colour for the fuel bar.
        s0: Sensor slot 0 reading.
        s1: Sensor slot 1 reading.
        s2: Sensor slot 2 reading.
        s3: Sensor slot 3 reading.
        s4: Sensor slot 4 reading.
        s0c: CSS colour for sensor slot 0.
        s1c: CSS colour for sensor slot 1.
        s2c: CSS colour for sensor slot 2.
        s3c: CSS colour for sensor slot 3.
        s4c: CSS colour for sensor slot 4.
        do_text: The action the bot is taking this tick.
        sent_text: Glyph showing whether the action was sent.
        sent_color: CSS colour for that glyph.
        why_text: The bot's stated reason for the action.
        tgt_text: Current target, or an em dash when there is none.
        act_text: Short action category.
        kills: Kills scored this run.
        hits: Shots that connected.
        misses: Shots that did not.
        rejects: Actions the server refused.
        dealt: Damage dealt this run.
        taken: Damage taken this run.
    """

    state_text: str
    mode_text: str
    mode_color: str
    mode_band: str
    pos_text: str
    fuel_text: str
    fuel_pct: int
    fuel_color: str
    s0: int
    s1: int
    s2: int
    s3: int
    s4: int
    s0c: str
    s1c: str
    s2c: str
    s3c: str
    s4c: str
    do_text: str
    sent_text: str
    sent_color: str
    why_text: str
    tgt_text: str
    act_text: str
    kills: int
    hits: int
    misses: int
    rejects: int
    dealt: int
    taken: int


def decode_fleet_bot(payload: object) -> FleetBot:
    """Decode one row of ``GET /bots``.

    Args:
        payload: One element of the response's ``bots`` array.

    Returns:
        The validated row.

    Raises:
        TankpitDecodeError: If any field is absent or of the wrong type.
    """
    row = require_object(payload, "fleet bot")
    return FleetBot(
        instance=require_str(row, "instance", "fleet bot"),
        account=require_str(row, "account", "fleet bot"),
        role=require_str(row, "role", "fleet bot"),
        room=require_str(row, "room", "fleet bot"),
        troop=require_str(row, "troop", "fleet bot"),
        doctrine=require_str(row, "doctrine", "fleet bot"),
        pid=require_int(row, "pid", "fleet bot"),
        alive=require_bool(row, "alive", "fleet bot"),
        returncode=require_optional_int(row, "returncode", "fleet bot"),
        kills=require_int(row, "kills", "fleet bot"),
        seconds=require_int(row, "seconds", "fleet bot"),
        started_ms=require_int(row, "started_ms", "fleet bot"),
    )


def decode_fleet_roster(payload: object) -> FleetRoster:
    """Decode the ``GET /bots`` response.

    Args:
        payload: The decoded JSON body.

    Returns:
        The validated roster.

    Raises:
        TankpitDecodeError: If the body or any row does not match.
    """
    body = require_object(payload, "fleet roster")
    return FleetRoster(
        boot=require_str(body, "boot", "fleet roster"),
        draining=require_bool(body, "draining", "fleet roster"),
        bots=[decode_fleet_bot(row) for row in require_list(body, "bots", "fleet roster")],
    )


def decode_hud(payload: object) -> BotHud | None:
    """Decode the ``GET /bots/{instance}/hud`` response.

    The manager answers in one of two shapes and they are told apart by
    the presence of ``available``, not by its value: a bot with no frame
    yet gets ``{"available": false}``, and a bot with one gets its
    ``hud.json`` returned verbatim, which carries no ``available`` key at
    all.

    Args:
        payload: The decoded JSON body.

    Returns:
        The validated frame, or ``None`` when the fleet reports that this
        bot has not written one yet.

    Raises:
        TankpitDecodeError: If a frame is present but does not match, or
            if ``available`` is present and not false.
    """
    body = require_object(payload, "bot hud")
    if "available" in body:
        if require_bool(body, "available", "bot hud"):
            raise TankpitDecodeError(
                "bot hud: 'available' is only ever sent as false; a present frame carries no such key"
            )
        return None
    return BotHud(
        state_text=require_str(body, "state_text", "bot hud"),
        mode_text=require_str(body, "mode_text", "bot hud"),
        mode_color=require_str(body, "mode_color", "bot hud"),
        mode_band=require_str(body, "mode_band", "bot hud"),
        pos_text=require_str(body, "pos_text", "bot hud"),
        fuel_text=require_str(body, "fuel_text", "bot hud"),
        fuel_pct=require_int(body, "fuel_pct", "bot hud"),
        fuel_color=require_str(body, "fuel_color", "bot hud"),
        s0=require_int(body, "s0", "bot hud"),
        s1=require_int(body, "s1", "bot hud"),
        s2=require_int(body, "s2", "bot hud"),
        s3=require_int(body, "s3", "bot hud"),
        s4=require_int(body, "s4", "bot hud"),
        s0c=require_str(body, "s0c", "bot hud"),
        s1c=require_str(body, "s1c", "bot hud"),
        s2c=require_str(body, "s2c", "bot hud"),
        s3c=require_str(body, "s3c", "bot hud"),
        s4c=require_str(body, "s4c", "bot hud"),
        do_text=require_str(body, "do_text", "bot hud"),
        sent_text=require_str(body, "sent_text", "bot hud"),
        sent_color=require_str(body, "sent_color", "bot hud"),
        why_text=require_str(body, "why_text", "bot hud"),
        tgt_text=require_str(body, "tgt_text", "bot hud"),
        act_text=require_str(body, "act_text", "bot hud"),
        kills=require_int(body, "kills", "bot hud"),
        hits=require_int(body, "hits", "bot hud"),
        misses=require_int(body, "misses", "bot hud"),
        rejects=require_int(body, "rejects", "bot hud"),
        dealt=require_int(body, "dealt", "bot hud"),
        taken=require_int(body, "taken", "bot hud"),
    )


class PublishedView(TypedDict):
    """The game-view pane for one bot, as published.

    ``kind`` is ``none`` for every bot today and that is a fact about the
    fleet, not a placeholder: ``/video`` and ``/frame`` are built only in
    the standalone single-bot service, while fleet children run the bot
    entry point and serve no HTTP at all. There is therefore no frame to
    address, and nothing per-tick is written to the shared ``runs`` mount
    either. When a fleet child gains that surface, the producing function
    lands here beside :func:`absent_view` with its own tests.

    Attributes:
        kind: Always ``none`` while no fleet child publishes frames.
    """

    kind: Literal["none"]


class PublishedHudAbsent(TypedDict):
    """The HUD card for a bot that has not written a frame.

    Attributes:
        available: Always false.
    """

    available: Literal[False]


class PublishedHudPresent(TypedDict):
    """The HUD card for a bot that has written a frame.

    Carries the bot's own frame verbatim under ``frame``, so the public
    card and the operator's local card are drawn from identical numbers.

    Attributes:
        available: Always true.
        frame: The bot's decoded HUD frame.
    """

    available: Literal[True]
    frame: BotHud


class PublishedBot(TypedDict):
    """One bot as the dashboard consumes it.

    Attributes:
        instance: Instance name, unique within the fleet.
        account: TankPit account the child was spawned with.
        role: Fleet role.
        room: Room the child joined.
        troop: Tank colour.
        doctrine: Engagement doctrine.
        alive: Whether the process was running at report time.
        returncode: Exit code once dead; ``None`` while alive.
        kills_bound: Kill bound; 0 is unbounded.
        seconds_bound: Seconds bound; 0 is unbounded.
        started_ms: Wall-clock spawn time in milliseconds.
        hud: The bot's HUD card, present or absent.
        view: The bot's game-view pane.
    """

    instance: str
    account: str
    role: str
    room: str
    troop: str
    doctrine: str
    alive: bool
    returncode: int | None
    kills_bound: int
    seconds_bound: int
    started_ms: int
    hud: PublishedHudAbsent | PublishedHudPresent
    view: PublishedView


class PublishedControl(TypedDict):
    """Whether the page may spawn, stop, or re-doctrine bots.

    Always disabled: the manager's mutating routes are bound to loopback
    and are not exposed, so a public page cannot reach them. The reason
    travels with the flag so the page states why rather than showing dead
    buttons.

    Attributes:
        enabled: Always false.
        reason: Why control is unavailable.
    """

    enabled: Literal[False]
    reason: str


class PublishedFleet(TypedDict):
    """The whole document written to ``fleet.json``.

    Attributes:
        schema_version: Contract version the page checks.
        generated_at: UTC ISO-8601 timestamp of this publish.
        boot: Manager boot id, so a restart is visible as an identity change.
        draining: Whether a shutdown drain has been requested.
        control: Whether the page may mutate the fleet.
        bots: Every managed instance, alive or dead.
    """

    schema_version: int
    generated_at: str
    boot: str
    draining: bool
    control: PublishedControl
    bots: list[PublishedBot]
