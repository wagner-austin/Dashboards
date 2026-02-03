# Bunny Jump

Jumping bunny animation.

## Source

`Bunny_Jump.mp4` - 26 frames at 30fps, reduced to 17 frames.

## Frames

17 frames, 58ms interval in engine (plays once per spacebar press).

## Config

Defined in `config.json`:

```json
{
  "source": "originals/bunny/bunny_jump/bunny_jump.gif",
  "widths": [30, 50, 80],
  "contrast": 3.5,
  "invert": true,
  "crop": "25%,0,25%,8",
  "directions": ["left", "right"]
}
```

## Generation

```bash
poetry run python -m scripts.generate_sprites
```

| Setting  | Value |
|----------|-------|
| Contrast | 3.5   |
| Invert   | Yes   |
| Widths   | 30, 50, 80 |
| Crop     | 25% sides, 8px bottom |

## Notes

Higher contrast needed due to video source. Cropped to remove empty space around bunny.
