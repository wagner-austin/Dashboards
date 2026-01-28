# Bunny Animations

## Folders

- **bunny_idle** - Sitting/resting animation (3 frames)
- **bunny_alert** - Alert/attentive animation (6 frames)
- **bunny_jump** - Jumping animation (19 frames)

## GIF Generation Settings

- **Ping-pong**: Yes for idle/alert, No for jump
- **Loop**: Infinite
- **Disposal**: 2 (restore to background)
- **Transparency**: 0
- **Convert**: RGBA

## Frame Delays

Delays are encoded in filenames (e.g., `frame_0_delay-0.4s.png` = 400ms).

### bunny_idle
| Frame | Delay |
|-------|-------|
| 3-5   | 0.4s  |

### bunny_alert
| Frame | Delay |
|-------|-------|
| 0     | 0.2s  |
| 1     | 0.1s  |
| 2     | 0.2s  |
| 3-5   | 0.4s  |

### bunny_jump
| Frame | Delay |
|-------|-------|
| 1-9   | 0.05s |
| 10    | 0.08s |
| 11    | 0.07s |
| 12    | 0.06s |
| 13-19 | 0.05s |

## Image Preprocessing (for ASCII conversion)

Apply these adjustments to white bunny PNGs before generating GIFs:

```python
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import math

def add_vignette(img, strength=0.75):
    width, height = img.size
    mask = Image.new('L', (width, height), 255)
    cx, cy = width // 2, height // 2
    max_dist = math.sqrt(cx**2 + cy**2)
    for y in range(height):
        for x in range(width):
            dist = math.sqrt((x - cx)**2 + (y - cy)**2)
            factor = 1 - (dist / max_dist) * strength
            mask.putpixel((x, y), int(255 * max(0, factor)))
    r, g, b, a = img.split()
    r = Image.composite(r, Image.new('L', img.size, 0), mask)
    g = Image.composite(g, Image.new('L', img.size, 0), mask)
    b = Image.composite(b, Image.new('L', img.size, 0), mask)
    return Image.merge('RGBA', (r, g, b, a))

def add_noise(img, amount=15):
    arr = np.array(img)
    noise = np.random.randint(-amount, amount, arr.shape[:2] + (1,))
    noise = np.repeat(noise, arr.shape[2], axis=2)
    arr = np.clip(arr.astype(int) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def process_frame(path):
    img = Image.open(path).convert('RGBA')
    r, g, b, a = img.split()
    rgb = Image.merge('RGB', (r, g, b))

    # Warmth (more red, less blue)
    r, g, b = rgb.split()
    r = r.point(lambda x: min(255, int(x * 1.1)))
    b = b.point(lambda x: int(x * 0.85))
    rgb = Image.merge('RGB', (r, g, b))

    # Adjustments
    rgb = ImageEnhance.Brightness(rgb).enhance(0.5)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.3)
    rgb = ImageEnhance.Color(rgb).enhance(1.4)
    rgb = add_noise(rgb, amount=15)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    result = rgb.convert('RGBA')
    result.putalpha(a)
    result = add_vignette(result, strength=0.75)

    # Final brightness/color fix
    r, g, b, a = result.split()
    rgb = Image.merge('RGB', (r, g, b))
    rgb = ImageEnhance.Brightness(rgb).enhance(1.6)
    rgb = ImageEnhance.Color(rgb).enhance(0.8)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.1)
    result = rgb.convert('RGBA')
    result.putalpha(a)

    return result
```

## ASCII Conversion Settings

| Animation   | Contrast | Invert | Width | Preprocessing |
|-------------|----------|--------|-------|---------------|
| bunny_idle  | 2.5      | Yes    | 40    | Manual edit   |
| bunny_alert | 2.3      | Yes    | 40    | Manual edit   |
| bunny_jump  | 1.1      | Yes    | 40    | Automated     |

```bash
# bunny_idle
python tools/gif_to_ascii.py originals/bunny/bunny_idle/bunny_idle.gif --contrast 2.5 --invert --widths 40 --output bunny/idle/

# bunny_alert
python tools/gif_to_ascii.py originals/bunny/bunny_alert/bunny_alert.gif --contrast 2.3 --invert --widths 40 --output bunny/alert/

# bunny_jump
python tools/gif_to_ascii.py originals/bunny/bunny_jump/bunny_jump.gif --contrast 1.1 --invert --widths 40 --output bunny/jump/
```

## Manual Image Edit Settings (for idle/alert)

Applied in photo editor before GIF generation:
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

## Regenerating GIFs

```python
from PIL import Image
import glob
import re

files = sorted(glob.glob('frame_*.png'))
frames = []
durations = []

for f in files:
    img = Image.open(f).convert('RGBA')
    frames.append(img)
    match = re.search(r'delay-(\d+\.?\d*)s', f)
    delay_ms = int(float(match.group(1)) * 1000)
    durations.append(delay_ms)

# For ping-pong (idle/alert):
pingpong_frames = frames + frames[-2:0:-1]
pingpong_durations = durations + durations[-2:0:-1]

pingpong_frames[0].save(
    'output.gif',
    save_all=True,
    append_images=pingpong_frames[1:],
    duration=pingpong_durations,
    loop=0,
    transparency=0,
    disposal=2
)
```
