# Bunny Jump

Jumping bunny animation.

## Frames

19 frames (frame_01 to frame_19), no ping-pong.

| Frame | Delay |
|-------|-------|
| 1-9   | 0.05s |
| 10    | 0.08s |
| 11    | 0.07s |
| 12    | 0.06s |
| 13-19 | 0.05s |

## Image Preprocessing

**Automated** Python script (see main README for full code):

```python
# Warmth
r = r.point(lambda x: min(255, int(x * 1.1)))
b = b.point(lambda x: int(x * 0.85))

# Adjustments
brightness = 0.5
contrast = 1.3
color = 1.4
noise = 15
unsharp_mask = (radius=2, percent=150, threshold=3)
vignette = 0.75

# Final fix
brightness = 1.6
color = 0.8
contrast = 1.1
```

## GIF Generation

No ping-pong (plays forward only, loops).

```bash
cd originals/bunny/bunny_jump
python -c "
from PIL import Image
import glob, re

files = sorted(glob.glob('frame_*.png'))
frames = [Image.open(f).convert('RGBA') for f in files]
durations = [int(float(re.search(r'delay-(\d+\.?\d*)s', f).group(1)) * 1000) for f in files]

frames[0].save('bunny_jump.gif', save_all=True, append_images=frames[1:],
    duration=durations, loop=0, transparency=0, disposal=2)
"
```

## ASCII Conversion

```bash
python tools/gif_to_ascii.py originals/bunny/bunny_jump/bunny_jump.gif --contrast 1.1 --invert --widths 40 --output bunny/jump/
```

| Setting  | Value |
|----------|-------|
| Contrast | 1.1   |
| Invert   | Yes   |
| Width    | 40    |
