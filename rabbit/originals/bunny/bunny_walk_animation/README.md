# Bunny Walk

Walking bunny animation (pixel art style).

## Frames

4 frames, 120ms interval in engine.

## Config

Defined in `config.json`:

```json
{
  "source": "originals/bunny/bunny_walk/bunny.gif",
  "widths": [30, 50, 80],
  "contrast": 1.8,
  "invert": true,
  "crop": "0,0,0,2",
  "directions": ["left", "right"]
}
```

## Generation

```bash
poetry run python -m scripts.generate_sprites
```

| Setting  | Value |
|----------|-------|
| Contrast | 1.8   |
| Invert   | Yes   |
| Widths   | 30, 50, 80 |
| Crop     | 2px bottom |

## Notes

Original pixel art bunny with built-in shading. Produces good ASCII output without preprocessing.
