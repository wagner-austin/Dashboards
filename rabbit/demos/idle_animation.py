"""ASCII bunny IDLE animation - vanilla Python."""
import msvcrt
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bunny.idle.w30_frames import FRAMES

print("\033[?25l\033[2J\033[H", end="")  # hide cursor, clear, home
i = 0
direction = 1  # ping-pong
while True:
    h = os.get_terminal_size().lines
    lines = FRAMES[i].split("\n")
    y = (h - len(lines)) // 2
    for j, line in enumerate(lines):
        print(f"\033[{y+j};6H{line:45}", end="")
    print(f"\033[{h};1HIDLE - Press 'q' to quit", end="", flush=True)

    t = time.time()
    while time.time() - t < 0.4:  # slower for idle
        if msvcrt.kbhit() and msvcrt.getch().lower() == b'q':
            print("\033[?25h\033[2J\033[H", end="")
            sys.exit()
        time.sleep(0.01)

    # ping-pong animation
    i += direction
    if i >= len(FRAMES) - 1 or i <= 0:
        direction *= -1
