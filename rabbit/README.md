# Rabbit ASCII Animation Engine

Full-viewport ASCII art animation with a bunny character, scrolling world, and animated tree.

## Quick Start

```bash
# Install dependencies
poetry install
npm install

# Generate sprites and build
poetry run python -m scripts.generate_sprites
npm run build

# Serve and open in browser
npx serve .
```

## Architecture

```
rabbit/
├── src/                    # TypeScript source
│   ├── main.ts             # Entry point, game loop, input handling
│   ├── types.ts            # Shared type definitions
│   ├── engine/             # Animation engine components
│   │   ├── Animation.ts    # Animation state machine
│   │   ├── Layer.ts        # Layer management
│   │   ├── Renderer.ts     # Buffer-based ASCII rendering
│   │   └── Sprite.ts       # Sprite with size variants
│   └── sprites/            # Generated sprite modules (do not edit)
├── dist/                   # Compiled JS output
├── tools/                  # Python utilities
│   └── gif_to_ascii.py     # GIF/image to ASCII converter
├── scripts/                # Build scripts
│   └── generate_sprites.py # Reads config.json, generates all sprites
├── originals/              # Source GIFs
├── config.json             # Sprite definitions and settings
└── index.html              # Minimal HTML loader
```

## Animation System

All animations use independent timers via `createAnimationTimer()`:

| Animation | Interval | Notes |
|-----------|----------|-------|
| Walk | 120ms | Cycles through 4 frames |
| Tree | 250ms | Ping-pong through 10 frames |
| Jump | 58ms | Plays 17 frames once per press |
| Render | 30 FPS | Draws current state |

Timers run independently from the render loop - no frame skipping, no drift.

## Controls

- **Arrow keys / WASD**: Change direction (world scrolls)
- **Spacebar**: Jump
- **R**: Reset tree position

## Config Format

`config.json` defines sprites and settings:

```json
{
  "sprites": {
    "bunny": {
      "animations": {
        "walk": {
          "source": "originals/bunny/bunny_walk/bunny.gif",
          "widths": [30, 50, 80],
          "contrast": 1.8,
          "invert": true,
          "crop": "0,0,0,2",
          "directions": ["left", "right"]
        }
      }
    },
    "tree": {
      "source": "originals/tree/tree.gif",
      "widths": [60, 120, 180],
      "contrast": 1.5,
      "invert": true
    }
  },
  "settings": {
    "fps": 30
  }
}
```

### Sprite Options

- **source**: Path to GIF/image
- **widths**: Array of character widths to generate
- **contrast**: Image contrast (1.0 = normal)
- **invert**: Invert colors before conversion
- **crop**: `"left,top,right,bottom"` in pixels or percentages
- **directions**: `["left", "right"]` for mirrored versions

## Development

```bash
# Run all checks
make check

# Individual commands
make lint      # ESLint + mypy + ruff
make test      # Vitest + pytest with coverage
make build     # Generate sprites + compile TS
```

## Generating Sprites

Sprites are auto-generated from GIFs:

```bash
# Regenerate all sprites from config.json
poetry run python -m scripts.generate_sprites

# Manual single conversion
poetry run python -m tools.gif_to_ascii input.gif --width 50 --contrast 1.8 --invert
```

## Gradient

ASCII characters used (dark to light): ` .:-+#@`
