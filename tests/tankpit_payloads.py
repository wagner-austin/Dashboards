"""Payloads captured from a running fleet manager.

These are verbatim bodies recorded from ``v0.1.0-bc45e3e1`` on
2026-09-02, not hand-authored samples. They are stored as raw text so
tests exercise JSON parsing and decoding on the same bytes the manager
actually sends.

The HUD frame is a real tick written by a headed run on the operator's
machine, taken from ``runs/bot/hud.json``.
"""

# GET /bots with no instances -- a manager that has just booted.
EMPTY_ROSTER_TEXT = '{\n "boot": "1788341122781",\n "draining": false,\n "bots": []\n}'

# GET /bots after one spawn whose child died on browser launch. Kept
# because a dead row is the shape the page must still render.
DEAD_BOT_ROSTER_TEXT = """{
 "boot": "1788341122781",
 "draining": false,
 "bots": [
  {
   "instance": "probe-1",
   "account": "Artax",
   "role": "fighter",
   "room": "Practice",
   "troop": "orange",
   "doctrine": "skirmish",
   "pid": 7,
   "alive": false,
   "returncode": 1,
   "kills": 0,
   "seconds": 300,
   "started_ms": 1788341194558
  }
 ]
}"""

# The same roster while the child was still running: returncode is null.
LIVE_BOT_ROSTER_TEXT = """{
 "boot": "1788341122781",
 "draining": false,
 "bots": [
  {
   "instance": "probe-1",
   "account": "Artax",
   "role": "fighter",
   "room": "Practice",
   "troop": "orange",
   "doctrine": "skirmish",
   "pid": 7,
   "alive": true,
   "returncode": null,
   "kills": 0,
   "seconds": 300,
   "started_ms": 1788341194558
  }
 ]
}"""

# GET /bots/{instance}/hud for a bot that has written no frame yet.
HUD_ABSENT_TEXT = '{\n "available": false\n}'

# A real tick frame, served verbatim by the manager. Note it carries no
# "available" key at all -- that is how the two shapes are told apart.
HUD_PRESENT_TEXT = (
    '{"state_text":"COLLECTING","mode_text":"COLLECT \\u00b7 PICKUP",'
    '"mode_color":"rgb(57, 255, 20)","mode_band":"rgba(57, 255, 20, 0.20)",'
    '"pos_text":"146,110","fuel_text":"934/1100","fuel_pct":84,'
    '"fuel_color":"rgb(200, 0, 200)","s0":25,"s1":25,"s2":25,"s3":25,"s4":7,'
    '"s0c":"rgb(57, 255, 20)","s1c":"rgb(57, 255, 20)","s2c":"rgb(57, 255, 20)",'
    '"s3c":"rgb(57, 255, 20)","s4c":"rgb(255, 20, 147)",'
    '"do_text":"pickup_fuel \\u2192 (149,109)","sent_text":"\\u25cf",'
    '"sent_color":"rgb(57, 255, 20)","why_text":"COLLECT: fuel_collect(volume=380)",'
    '"tgt_text":"\\u2014","act_text":"collect","kills":0,"hits":0,"misses":0,'
    '"rejects":0,"dealt":0,"taken":0}'
)
