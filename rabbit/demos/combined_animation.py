"""ASCII bunny combined animation - walk between each action with aligned ground."""
import sys, os, time, msvcrt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from frames.bunny.w40_frames import FRAMES as WALK_FRAMES
from bunny.idle.w30_frames import FRAMES as IDLE_FRAMES
from bunny.alert.w30_frames import FRAMES as ALERT_FRAMES
from bunny.jump.w60_frames import FRAMES as JUMP_FRAMES

# Target height - all frames padded to this height with ground at bottom
TARGET_HEIGHT = 32

def normalize_frames(frames, width, preserve_bottom=False):
    """Pad frames to TARGET_HEIGHT with empty lines at top, ground at bottom."""
    normalized = []
    for frame in frames:
        lines = frame.split('\n')
        if not preserve_bottom:
            # Remove trailing empty lines to find actual ground
            while lines and lines[-1].strip() == '':
                lines.pop()
        # Pad top to reach target height
        padding_needed = TARGET_HEIGHT - len(lines)
        empty_line = ' ' * width
        if padding_needed > 0:
            padded = [empty_line] * padding_needed + lines
        else:
            padded = lines
        normalized.append('\n'.join(padded))
    return normalized

# Normalize all animations
WALK_NORM = normalize_frames(WALK_FRAMES, 40)
IDLE_NORM = normalize_frames(IDLE_FRAMES, 30)
ALERT_NORM = normalize_frames(ALERT_FRAMES, 30)
JUMP_NORM = normalize_frames(JUMP_FRAMES, 60, preserve_bottom=True)  # Keep air space

GRADIENT = " .+-#"

def char_to_weight(c):
    """Convert character to density weight 0-4."""
    return GRADIENT.index(c) if c in GRADIENT else 0

def weight_to_char(w):
    """Convert weight back to character."""
    w = max(0, min(4, round(w)))
    return GRADIENT[w]

def blend_frames(frame_a, frame_b, t):
    """Blend two frames. t=0 is all A, t=1 is all B."""
    lines_a = frame_a.split('\n')
    lines_b = frame_b.split('\n')
    max_lines = max(len(lines_a), len(lines_b))
    max_width = max(max(len(l) for l in lines_a), max(len(l) for l in lines_b))

    # Pad to same size
    while len(lines_a) < max_lines:
        lines_a.insert(0, ' ' * max_width)
    while len(lines_b) < max_lines:
        lines_b.insert(0, ' ' * max_width)

    result = []
    for la, lb in zip(lines_a, lines_b):
        line = []
        for i in range(max(len(la), len(lb))):
            ca = la[i] if i < len(la) else ' '
            cb = lb[i] if i < len(lb) else ' '
            wa = char_to_weight(ca)
            wb = char_to_weight(cb)
            blended = wa * (1 - t) + wb * t
            line.append(weight_to_char(blended))
        result.append(''.join(line))
    return '\n'.join(result)

def draw_frame(frame, label):
    h = os.get_terminal_size().lines
    lines = frame.split("\n")
    y = h - len(lines)
    for j, line in enumerate(lines):
        print(f"\033[{y+j};1H\033[K", end="")  # Clear entire line
        print(f"\033[{y+j};10H{line}", end="")
    print(f"\033[1;1H{label} - Press 'q' to quit   ", end="", flush=True)

def transition_blend(from_frames, to_frames, steps=3):
    """Blend from last frame of A to first frame of B using character density."""
    frame_a = from_frames[-1]
    frame_b = to_frames[0]
    for i in range(steps):
        t = (i + 1) / steps
        blended = blend_frames(frame_a, frame_b, t)
        draw_frame(blended, "...")
        wait(0.06)

import random

def transition_dissolve(from_frames, to_frames, steps=5):
    """Dissolve from last frame of A to first frame of B - no flicker."""
    frame_a = from_frames[-1]
    frame_b = to_frames[0]

    lines_a = frame_a.split('\n')
    lines_b = frame_b.split('\n')
    max_lines = max(len(lines_a), len(lines_b))
    max_width = max(max(len(l) for l in lines_a), max(len(l) for l in lines_b))

    # Pad to same size
    while len(lines_a) < max_lines:
        lines_a.insert(0, ' ' * max_width)
    while len(lines_b) < max_lines:
        lines_b.insert(0, ' ' * max_width)

    # Pre-generate random thresholds for each position (0-1)
    thresholds = []
    for row in range(max_lines):
        row_thresh = [random.random() for _ in range(max_width)]
        thresholds.append(row_thresh)

    for step in range(steps):
        t = (step + 1) / steps
        result = []
        for row, (la, lb) in enumerate(zip(lines_a, lines_b)):
            line = []
            for col in range(max_width):
                ca = la[col] if col < len(la) else ' '
                cb = lb[col] if col < len(lb) else ' '
                # Switch to B when t exceeds this position's threshold
                if t >= thresholds[row][col]:
                    line.append(cb)
                else:
                    line.append(ca)
            result.append(''.join(line))
        draw_frame('\n'.join(result), "...")
        wait(0.04)

# Switch between methods: 'blend' or 'dissolve'
TRANSITION_MODE = 'dissolve'

def transition(from_frames, to_frames):
    if TRANSITION_MODE == 'dissolve':
        transition_dissolve(from_frames, to_frames)
    else:
        transition_blend(from_frames, to_frames)

def check_quit():
    if msvcrt.kbhit() and msvcrt.getch().lower() == b'q':
        print("\033[?25h\033[2J\033[H", end="")
        sys.exit()

def wait(duration):
    t = time.time()
    while time.time() - t < duration:
        check_quit()
        time.sleep(0.01)

def play_walk(cycles=2):
    for _ in range(cycles):
        for frame in WALK_NORM:
            draw_frame(frame, "WALK")
            wait(0.09)

def play_idle():
    # Forward
    for frame in IDLE_NORM:
        draw_frame(frame, "IDLE")
        wait(0.35)
    # Backward (ping-pong)
    for frame in reversed(IDLE_NORM[1:-1]):
        draw_frame(frame, "IDLE")
        wait(0.35)

def play_alert():
    for frame in ALERT_NORM:
        draw_frame(frame, "ALERT")
        wait(0.12)

def play_jump():
    for frame in JUMP_NORM:
        draw_frame(frame, "JUMP")
        wait(0.05)

print("\033[?25l\033[2J", end="")  # hide cursor, clear screen

while True:
    play_walk(3)
    transition(WALK_NORM, IDLE_NORM)
    play_idle()
    transition(IDLE_NORM, WALK_NORM)
    play_walk(2)
    transition(WALK_NORM, ALERT_NORM)
    play_alert()
    transition(ALERT_NORM, WALK_NORM)
    play_walk(2)
    transition(WALK_NORM, JUMP_NORM)
    play_jump()
    transition(JUMP_NORM, WALK_NORM)
