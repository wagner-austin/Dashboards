"""Publisher for the public TankPit fleet dashboard.

Reads the fleet manager's HTTP surface and writes ``fleet.json``, the
document ``index.html`` renders. Every field on that page comes from a
decoded upstream payload; nothing is hand-authored.
"""
