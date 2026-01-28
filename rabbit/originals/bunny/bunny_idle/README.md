# Bunny Idle

Sitting/resting bunny animation.

## Frames

3 frames (frame_3 to frame_5), ping-pong animation = 4 total frames in GIF.

| Frame | Delay |
|-------|-------|
| 3     | 0.4s  |
| 4     | 0.4s  |
| 5     | 0.4s  |

## Image Preprocessing

**Manual edit** in photo editor with these settings:
- temp: 100
- tint: -15
- brightness: -84
- contrast: 23
- highlights: 33
- shadows: 35
- whites: 8
- blacks: 18
- vibrance: 29
- sharpness: 10
- clarity: 100
- vignette: 58

## GIF Generation

Ping-pong enabled (forward + reverse).

```bash
cd originals/bunny/bunny_idle
python -c "
from PIL import Image
import glob, re

files = sorted(glob.glob('frame_*.png'))
frames = [Image.open(f).convert('RGBA') for f in files]
durations = [int(float(re.search(r'delay-(\d+\.?\d*)s', f).group(1)) * 1000) for f in files]

pingpong_frames = frames + frames[-2:0:-1]
pingpong_durations = durations + durations[-2:0:-1]

pingpong_frames[0].save('bunny_idle.gif', save_all=True, append_images=pingpong_frames[1:],
    duration=pingpong_durations, loop=0, transparency=0, disposal=2)
"
```

## ASCII Conversion

```bash
python tools/gif_to_ascii.py originals/bunny/bunny_idle/bunny_idle.gif --contrast 2.5 --invert --widths 40 --output bunny/idle/
```

| Setting  | Value |
|----------|-------|
| Contrast | 2.5   |
| Invert   | Yes   |
| Width    | 40    |
