"""Interactive walk + jump animation - spacebar to jump."""
import sys, os, time, msvcrt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from frames.bunny.w40_frames import FRAMES as WALK_FRAMES
from bunny.jump.w40_frames import FRAMES as JUMP_FRAMES

# Target height - all frames padded to this
TARGET_HEIGHT = 32

def normalize_frames(frames, width, preserve_bottom=False):
    """Pad frames to TARGET_HEIGHT with empty lines at top, ground at bottom."""
    normalized = []
    for frame in frames:
        lines = frame.split('\n')
        if not preserve_bottom:
            while lines and lines[-1].strip() == '':
                lines.pop()
        padding_needed = TARGET_HEIGHT - len(lines)
        empty_line = ' ' * width
        if padding_needed > 0:
            padded = [empty_line] * padding_needed + lines
        else:
            padded = lines
        normalized.append('\n'.join(padded))
    return normalized

WALK_NORM = normalize_frames(WALK_FRAMES, 42)
JUMP_NORM = normalize_frames(JUMP_FRAMES, 42)  # strip bottom too so ground aligns

GRADIENT = " .+-#"

def char_to_weight(c):
    return GRADIENT.index(c) if c in GRADIENT else 0

def weight_to_char(w):
    w = max(0, min(4, round(w)))
    return GRADIENT[w]

def blend_frames(frame_a, frame_b, t):
    """Blend two frames. t=0 is all A, t=1 is all B."""
    lines_a = frame_a.split('\n')
    lines_b = frame_b.split('\n')
    max_lines = max(len(lines_a), len(lines_b))
    max_width = max(max(len(l) for l in lines_a) if lines_a else 0,
                    max(len(l) for l in lines_b) if lines_b else 0)

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
        print(f"\033[{y+j};1H\033[K", end="")
        print(f"\033[{y+j};10H{line}", end="")
    print(f"\033[1;1H{label} - Press SPACE to jump, 'q' to quit   ", end="", flush=True)

def check_input():
    """Check for key presses. Returns 'jump', 'quit', or None."""
    if msvcrt.kbhit():
        key = msvcrt.getch()
        if key == b' ':
            return 'jump'
        elif key.lower() == b'q':
            return 'quit'
    return None

def wait(duration):
    """Wait while checking for input."""
    t = time.time()
    while time.time() - t < duration:
        result = check_input()
        if result == 'quit':
            print("\033[?25h\033[2J\033[H", end="")
            sys.exit()
        if result == 'jump':
            return 'jump'
        time.sleep(0.01)
    return None

def transition_to_jump(walk_frame_idx):
    """Blend from current walk frame to first jump frame."""
    for i in range(3):
        t = (i + 1) / 3
        blended = blend_frames(WALK_NORM[walk_frame_idx], JUMP_NORM[0], t)
        draw_frame(blended, "...")
        time.sleep(0.04)

def transition_to_walk(jump_frame_idx):
    """Blend from last jump frame to first walk frame."""
    for i in range(3):
        t = (i + 1) / 3
        blended = blend_frames(JUMP_NORM[-1], WALK_NORM[0], t)
        draw_frame(blended, "...")
        time.sleep(0.04)

def play_jump():
    """Play the full jump animation (no interrupts)."""
    for frame in JUMP_NORM:
        draw_frame(frame, "JUMP")
        time.sleep(0.05)

print("\033[?25l\033[2J", end="")  # hide cursor, clear screen

walk_idx = 0
state = 'walk'  # 'walk' or 'jumping'

while True:
    if state == 'walk':
        draw_frame(WALK_NORM[walk_idx], "WALK")
        result = wait(0.09)

        if result == 'jump':
            # Transition to jump
            transition_to_jump(walk_idx)
            play_jump()
            transition_to_walk(-1)
            walk_idx = 0  # restart walk from beginning
        else:
            walk_idx = (walk_idx + 1) % len(WALK_NORM)
