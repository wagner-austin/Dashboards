"""Decoder tests for the TankPit publisher.

Every case runs against payloads captured from a live fleet manager. The
error cases assert the message names the offending field, because that
message is the whole point of decoding at the boundary.
"""

import json

import pytest
from tankpit.models import (
    BotHud,
    TankpitDecodeError,
    decode_fleet_bot,
    decode_fleet_roster,
    decode_hud,
    require_bool,
    require_int,
    require_list,
    require_object,
    require_optional_int,
    require_str,
)

from tests.tankpit_payloads import (
    DEAD_BOT_ROSTER_TEXT,
    EMPTY_ROSTER_TEXT,
    HUD_ABSENT_TEXT,
    HUD_PRESENT_TEXT,
    LIVE_BOT_ROSTER_TEXT,
)


def test_require_object_accepts_a_string_keyed_mapping() -> None:
    assert require_object({"a": 1}, "ctx") == {"a": 1}


def test_require_object_rejects_a_non_object() -> None:
    with pytest.raises(TankpitDecodeError, match="ctx: expected an object, got list"):
        require_object([], "ctx")


def test_require_object_rejects_non_string_keys() -> None:
    with pytest.raises(TankpitDecodeError, match="ctx: object keys must be strings, got int"):
        require_object({1: "a"}, "ctx")


def test_require_str_reads_a_string() -> None:
    assert require_str({"f": "v"}, "f", "ctx") == "v"


def test_require_str_rejects_a_non_string() -> None:
    with pytest.raises(TankpitDecodeError, match="ctx: 'f' must be a string, got int"):
        require_str({"f": 1}, "f", "ctx")


def test_require_int_reads_an_integer() -> None:
    assert require_int({"f": 7}, "f", "ctx") == 7


def test_require_int_rejects_a_boolean() -> None:
    with pytest.raises(TankpitDecodeError, match="ctx: 'f' must be an integer, got bool"):
        require_int({"f": True}, "f", "ctx")


def test_require_int_rejects_a_non_integer() -> None:
    with pytest.raises(TankpitDecodeError, match="ctx: 'f' must be an integer, got str"):
        require_int({"f": "1"}, "f", "ctx")


def test_require_bool_reads_a_boolean() -> None:
    assert require_bool({"f": False}, "f", "ctx") is False


def test_require_bool_rejects_a_non_boolean() -> None:
    with pytest.raises(TankpitDecodeError, match="ctx: 'f' must be a boolean, got int"):
        require_bool({"f": 0}, "f", "ctx")


def test_require_optional_int_reads_an_integer() -> None:
    assert require_optional_int({"f": 3}, "f", "ctx") == 3


def test_require_optional_int_reads_null_as_none() -> None:
    assert require_optional_int({"f": None}, "f", "ctx") is None


def test_require_optional_int_requires_the_field_to_be_present() -> None:
    with pytest.raises(TankpitDecodeError, match="ctx: 'f' is required"):
        require_optional_int({}, "f", "ctx")


def test_require_optional_int_rejects_a_boolean() -> None:
    with pytest.raises(TankpitDecodeError, match="ctx: 'f' must be an integer or null, got bool"):
        require_optional_int({"f": True}, "f", "ctx")


def test_require_optional_int_rejects_a_non_integer() -> None:
    with pytest.raises(TankpitDecodeError, match="ctx: 'f' must be an integer or null, got str"):
        require_optional_int({"f": "3"}, "f", "ctx")


def test_require_list_reads_an_array() -> None:
    assert require_list({"f": [1]}, "f", "ctx") == [1]


def test_require_list_rejects_a_non_array() -> None:
    with pytest.raises(TankpitDecodeError, match="ctx: 'f' must be an array, got dict"):
        require_list({"f": {}}, "f", "ctx")


def test_empty_roster_decodes_with_boot_kept_as_a_string() -> None:
    roster = decode_fleet_roster(json.loads(EMPTY_ROSTER_TEXT))
    assert roster == {"boot": "1788341122781", "draining": False, "bots": []}


def test_dead_bot_roster_decodes_with_its_exit_code() -> None:
    roster = decode_fleet_roster(json.loads(DEAD_BOT_ROSTER_TEXT))
    assert roster["bots"] == [
        {
            "instance": "probe-1",
            "account": "Artax",
            "role": "fighter",
            "room": "Practice",
            "troop": "orange",
            "doctrine": "skirmish",
            "pid": 7,
            "alive": False,
            "returncode": 1,
            "kills": 0,
            "seconds": 300,
            "started_ms": 1788341194558,
        }
    ]


def test_live_bot_roster_decodes_with_a_null_returncode() -> None:
    roster = decode_fleet_roster(json.loads(LIVE_BOT_ROSTER_TEXT))
    assert roster["bots"][0]["alive"] is True
    assert roster["bots"][0]["returncode"] is None


def test_a_roster_row_missing_a_field_names_that_field() -> None:
    with pytest.raises(TankpitDecodeError, match="fleet bot: 'troop' must be a string, got NoneType"):
        decode_fleet_bot(
            {
                "instance": "a",
                "account": "b",
                "role": "fighter",
                "room": "Practice",
                "doctrine": "skirmish",
                "pid": 1,
                "alive": True,
                "returncode": None,
                "kills": 0,
                "seconds": 0,
                "started_ms": 0,
            }
        )


def test_a_roster_naming_its_boot_a_number_is_rejected() -> None:
    with pytest.raises(TankpitDecodeError, match="fleet roster: 'boot' must be a string, got int"):
        decode_fleet_roster({"boot": 1788341122781, "draining": False, "bots": []})


def test_absent_hud_decodes_to_none() -> None:
    assert decode_hud(json.loads(HUD_ABSENT_TEXT)) is None


def test_present_hud_decodes_every_field_of_a_real_tick() -> None:
    hud = decode_hud(json.loads(HUD_PRESENT_TEXT))
    expected = BotHud(
        state_text="COLLECTING",
        mode_text="COLLECT · PICKUP",
        mode_color="rgb(57, 255, 20)",
        mode_band="rgba(57, 255, 20, 0.20)",
        pos_text="146,110",
        fuel_text="934/1100",
        fuel_pct=84,
        fuel_color="rgb(200, 0, 200)",
        s0=25,
        s1=25,
        s2=25,
        s3=25,
        s4=7,
        s0c="rgb(57, 255, 20)",
        s1c="rgb(57, 255, 20)",
        s2c="rgb(57, 255, 20)",
        s3c="rgb(57, 255, 20)",
        s4c="rgb(255, 20, 147)",
        do_text="pickup_fuel → (149,109)",
        sent_text="●",
        sent_color="rgb(57, 255, 20)",
        why_text="COLLECT: fuel_collect(volume=380)",
        tgt_text="—",
        act_text="collect",
        kills=0,
        hits=0,
        misses=0,
        rejects=0,
        dealt=0,
        taken=0,
    )
    assert hud == expected


def test_present_hud_carries_the_counters_the_hand_written_sample_lacked() -> None:
    hud = decode_hud(json.loads(HUD_PRESENT_TEXT))
    if hud is None:
        raise AssertionError("the captured frame decodes to a HUD, not to absent")
    assert (hud["dealt"], hud["taken"]) == (0, 0)


def test_a_hud_claiming_available_true_is_rejected() -> None:
    with pytest.raises(TankpitDecodeError, match="only ever sent as false"):
        decode_hud({"available": True})


def test_a_malformed_hud_frame_names_the_offending_field() -> None:
    frame = json.loads(HUD_PRESENT_TEXT)
    frame["fuel_pct"] = "84"
    with pytest.raises(TankpitDecodeError, match="bot hud: 'fuel_pct' must be an integer, got str"):
        decode_hud(frame)
