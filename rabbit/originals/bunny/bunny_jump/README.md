# Bunny Jump

Jumping bunny animation.

## Source

`Bunny_Jump.mp4` - 26 frames at 30fps

## Frames

26 frames (frame_01 to frame_26), uniform timing.

| Frame | Delay |
|-------|-------|
| 1-26  | 0.03s |

## GIF Generation

```bash
# Created from MP4
python -c "
from PIL import Image
import cv2

cap = cv2.VideoCapture('Bunny_Jump.mp4')
frames = []
while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frames.append(Image.fromarray(frame_rgb))
cap.release()

frames[0].save('bunny_jump.gif', save_all=True, append_images=frames[1:],
    duration=33, loop=0)
"
```

## ASCII Conversion

```bash
python tools/gif_to_ascii.py originals/bunny/bunny_jump/Bunny_Jump.mp4 --contrast 1.5 --invert --widths 60 --frames 26 --output bunny/jump/
```

Note: Frames are cropped 25% from each side before conversion.

| Setting  | Value |
|----------|-------|
| Contrast | 1.5   |
| Invert   | Yes   |
| Width    | 60    |
| Crop     | 25% sides |
