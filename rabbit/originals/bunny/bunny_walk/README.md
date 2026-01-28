# Bunny Walk

Walking bunny animation (pixel art style).

## Frames

4 frames (frame_0 to frame_3).

| Frame | Delay |
|-------|-------|
| 0     | 0.09s |
| 1     | 0.09s |
| 2     | 0.09s |
| 3     | 0.09s |

## Image Preprocessing

None required - already pixel art with good tonal range.

## GIF Generation

```bash
cd originals/bunny/bunny_walk
python -c "
from PIL import Image
import glob, re

files = sorted(glob.glob('frame_*.png'))
frames = [Image.open(f).convert('RGBA') for f in files]
durations = [int(float(re.search(r'delay-(\d+\.?\d*)s', f).group(1)) * 1000) for f in files]

frames[0].save('bunny.gif', save_all=True, append_images=frames[1:],
    duration=durations, loop=0, transparency=0, disposal=2)
"
```

## ASCII Conversion

```bash
python tools/gif_to_ascii.py originals/bunny/bunny_walk/bunny.gif --contrast 1.5 --invert --widths 40 --output bunny/walk/
```

| Setting  | Value |
|----------|-------|
| Contrast | 1.5   |
| Invert   | Yes   |
| Width    | 40    |

## Notes

This is the original pixel art bunny with built-in shading. It produces good ASCII output without preprocessing because it already has tonal variation.
