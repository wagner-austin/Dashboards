"""ASCII bunny WALK animation - vanilla Python."""
import sys, os, time, msvcrt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from frames.bunny.w40_frames import FRAMES

print("\033[?25l\033[2J\033[H", end="")  # hide cursor, clear, home
i = 0
while True:
    h = os.get_terminal_size().lines
    lines = FRAMES[i].split("\n")
    y = (h - len(lines)) // 2
    for j, line in enumerate(lines):
        print(f"\033[{y+j};6H{line:45}", end="")
    print(f"\033[{h};1HWALK - Press 'q' to quit", end="", flush=True)

    t = time.time()
    while time.time() - t < 0.09:  # fast for walk
        if msvcrt.kbhit() and msvcrt.getch().lower() == b'q':
            print("\033[?25h\033[2J\033[H", end="")
            sys.exit()
        time.sleep(0.01)

    # loop animation
    i = (i + 1) % len(FRAMES)
