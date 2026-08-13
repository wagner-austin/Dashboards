# Rabbit ASCII Animation Engine

A 3D ASCII art engine that renders an interactive world entirely as text. A bunny walks, jumps, and hops through an infinite forest of animated trees -- all drawn with characters like `# + - .` in a monospace font, updated 60 times per second.

## Quick Start

```bash
# Install dependencies
poetry install
npm install

# Generate sprites and build
poetry run python -m scripts.generate_sprites
npm run build

# Serve and open in browser
make dev
```

## Architecture

```
rabbit/
├── src/
│   ├── main.ts              # Entry point, game loop orchestration
│   ├── types.ts             # Shared type definitions
│   ├── rendering/           # Frame rendering pipeline
│   │   ├── SceneRenderer.ts # Per-frame scene composition
│   │   ├── Viewport.ts      # Character grid measurement and buffer
│   │   ├── Ground.ts        # Tiled ASCII ground pattern
│   │   └── draw.ts          # Sprite drawing and crossfade transitions
│   ├── world/               # 3D projection system
│   │   └── Projection.ts    # Camera, perspective math, depth wrapping
│   ├── entities/            # Game objects
│   │   ├── Bunny.ts         # Bunny state machine and animation timers
│   │   ├── SceneSprite.ts   # Generic scene object (trees, grass)
│   │   └── EntityTransition.ts # Size transition and visibility fading
│   ├── layers/              # Layer management and depth sorting
│   │   ├── types.ts         # Layer, scene, and render candidate types
│   │   ├── validation.ts    # Config parsing and auto-layer generation
│   │   ├── renderer.ts      # 3D projected layer rendering with Z-wrapping
│   │   └── widths.ts        # Depth-to-width mapping with power curve
│   ├── input/               # Input layer (see "Input Architecture")
│   │   ├── intent.ts        # MovementIntent value type (leaf, no imports)
│   │   ├── state.ts         # InputState; effective intent lives here
│   │   ├── arbiter.ts       # Source priority; sole writer of the intent
│   │   ├── reducer.ts       # Intent change -> bunny state machine
│   │   ├── Autopilot.ts     # Pure wander state machine (idle autorun)
│   │   ├── controller.ts    # Frame driver around the autopilot
│   │   ├── activity.ts      # Seconds since the user last acted
│   │   ├── movement.ts      # Camera integration from effective intent
│   │   ├── Keyboard.ts      # Keyboard source
│   │   ├── Touch.ts         # Invisible virtual joystick (8-way + tap)
│   │   ├── handlers.ts      # Shared input-to-animation handlers
│   │   ├── validation.ts    # Autorun config decoding
│   │   └── factory.ts       # Assembles and wires the layer
│   ├── loaders/             # Asset loading
│   │   ├── progressive.ts   # Ordered sprite loading (ground → grass → bunny → trees)
│   │   ├── sprites.ts       # Animation timer factory and sprite loaders
│   │   └── layers.ts        # Layer instance creation from config
│   ├── audio/               # Audio system
│   │   ├── AudioPlayer.ts   # Web Audio API player with crossfade
│   │   ├── TrackSelector.ts # Track selection by time/location
│   │   ├── controller.ts    # Deferred init and track switching
│   │   └── validation.ts    # Audio config validation
│   ├── io/                  # Browser I/O and initialization
│   │   ├── autostart.ts     # DOM-ready bootstrap
│   │   ├── browser.ts       # Browser-specific dependencies
│   │   └── sprites.ts       # Dynamic sprite module loading
│   ├── sprites/             # Generated sprite modules (do not edit)
│   │   ├── bunny/           # 8 animations × left/right variants
│   │   ├── tree1/           # 14 size variants (w15–w350)
│   │   ├── tree2/           # 14 size variants (w15–w350)
│   │   └── grass/           # Foreground tiling sprite
│   └── utils/               # Math utilities
├── tools/                   # Python utilities
│   └── gif_to_ascii.py      # GIF/video/image to ASCII converter
├── scripts/                 # Build scripts
│   └── generate_sprites.py  # Reads config.json, generates all sprite modules
├── originals/               # Source GIFs and videos
├── audio/                   # Music tracks
├── config.json              # Sprite definitions, layers, and settings
└── index.html               # Minimal HTML loader
```

## How It Works

Each frame, the engine:

1. Creates a blank 2D grid of space characters sized to fill the viewport
2. Projects all scene objects from world space to screen position using perspective math
3. Stamps characters into the grid layer by layer, back to front (spaces are transparent)
4. Joins every row into a single string and sets it as the page text

The browser displays it in a monospace font, so every character lines up on a grid. At 60fps it looks like smooth animation.

## 3D Projection

Objects exist in a world with horizontal position (X) and depth (Z). The projection system converts world coordinates to screen position:

- **Size**: `scale = focalLength / distance` -- closer objects are bigger
- **Vertical position**: Far objects sit near the horizon, close objects near the bottom
- **Parallax**: Close objects shift more when the camera moves, distant objects barely move
- **Draw order**: Everything sorts back-to-front so near objects cover far ones

Each tree has 14 pre-generated ASCII versions from 15 to 350 characters wide. The projection picks which size to display based on distance. When a tree changes size, the engine crossfades between sprites by morphing from the edges inward, with each character stepping through a weighted density gradient (`# + - .` heavy to light) so transitions look smooth instead of popping.

## Bunny State Machine

The bunny uses a discriminated union with 5 animation states:

| State | Description |
|-------|-------------|
| Idle | Standing still, looping idle animation |
| Walk | Walking left/right, camera scrolls |
| Jump | One-shot jump animation (spacebar) |
| Hop | Looping hop into/out of depth (W/S) |
| Transition | Intermediary animations between states |

Transitions are first-class -- walk-to-idle, idle-to-walk, walk-to-turn-away, walk-to-turn-toward -- with pending actions so inputs during transitions queue correctly.

Each animation runs on an independent timer, decoupled from the render loop.
The intervals come from `settings.animation` in `config.json` — see Movement
Speed below. Scene sprites animate on their own fixed 400ms timer.

## Controls

- **A/D or Left/Right arrows**: Walk (camera scrolls with bunny)
- **W/S or Up/Down arrows**: Hop into/out of depth (moves camera along Z axis)
- **Spacebar**: Jump
- **N**: Switch music track
- **R**: Reset camera position
- **Touch**: Invisible joystick (drag for 8-way movement, tap to jump)

Leave the page alone and the bunny takes over by itself — see Autorun below.

## Input Architecture

Three sources can drive the bunny: keyboard, touch, and the autopilot. They are
joined by two explicit state machines and a typed boundary between them.

```
Keyboard ─┐
Touch  ───┼──> MovementIntent ──> Arbiter ──> reducer ──> Bunny state machine
Autopilot ┘                     (sole writer)            (idle/walk/jump/hop)
```

- **Intent** (`intent.ts`) is what a source *wants*: a horizontal axis, a
  vertical axis, both immutable. Sources produce intent and nothing else.
- **The arbiter** (`arbiter.ts`) resolves competing intents by priority — a
  non-neutral user intent always beats the autopilot — and is the only writer of
  `state.intent`. A fourth source cannot introduce a second writer.
- **The reducer** (`reducer.ts`) turns an intent *change* into state machine
  calls. It has no idea which source won, so every source produces identical
  animation behaviour for identical intent.
- **The autopilot** (`Autopilot.ts`) is the upper of the two state machines. It
  decides what the bunny should want; the bunny's own machine decides how that
  is performed. `stepAutopilot` is pure — same state, input, config, and draws
  in, same state out — so the wander logic is tested with real arithmetic rather
  than timers.

## Autorun

When nobody has touched the keyboard or screen for `idleDelay` seconds, the
autopilot engages and wanders: walking legs in one direction, occasional hops
into depth, occasional jumps, and pauses to idle in between. Any real key press
or touch takes control back immediately, and the autopilot stands down until
the page goes quiet again.

The autopilot is a four-state machine:

| Phase | Meaning |
|-------|---------|
| Dormant | Standing down; the user is present |
| Pause | Idling between movement legs |
| Walk | Walking a leg left or right |
| Hop | Hopping a leg into or out of depth |

Tuned in `config.json`. Every field is optional; an omitted block decodes to
these defaults.

```json
{
  "autorun": {
    "enabled": true,
    "idleDelay": 5,
    "minLeg": 2,
    "maxLeg": 7,
    "minPause": 3,
    "maxPause": 9,
    "turnChance": 0.5,
    "hopChance": 0.25,
    "jumpChance": 0.35
  }
}
```

| Field | Meaning |
|-------|---------|
| enabled | Whether the autopilot may engage at all |
| idleDelay | Seconds of no user input before it takes over |
| minLeg / maxLeg | Shortest and longest movement leg, in seconds |
| minPause / maxPause | Shortest and longest idle pause, in seconds |
| turnChance | Probability (0-1) a new walk leg reverses direction |
| hopChance | Probability (0-1) a leg is a depth hop instead of a walk |
| jumpChance | Probability (0-1) a walk leg jumps somewhere along its length |

Set `"enabled": false` to switch it off entirely. Note that browsers only start
audio after a real user gesture, so a page left completely untouched animates
silently.

## Progressive Loading

Sprites load in priority order so the scene is interactive as fast as possible:

1. **Ground** -- instant (pure ASCII pattern, no loading)
2. **Grass** -- foreground tiling sprite
3. **Bunny** -- all animation frames (unlocks movement controls)
4. **Trees** -- smallest widths first (w15 → w350)

The render loop starts immediately. Entities hold mutable references to a sprite registry, so new sizes appear automatically as they load.

## Infinite World

Both X and Z axes wrap seamlessly:

- Walk far enough sideways and you loop around (`WORLD_WIDTH = 800`)
- Hop far enough forward/backward and depth wraps at the visible range boundary
- Trees generate wrapped Z copies at visibility-depth intervals for seamless coverage
- ~46 trees across 23 auto-generated depth layers (2 per layer, seeded random placement)

## Audio

Web Audio API with deferred initialization (created on first user interaction to satisfy browser autoplay policies):

- Looping background music with crossfade between tracks
- Track switching via N key
- Configurable master volume and per-track volume

## Config Format

`config.json` defines sprites, layers, and settings:

```json
{
  "sprites": {
    "bunny": {
      "animations": {
        "walk": {
          "source": "originals/bunny/bunny_walk_animation/bunny.gif",
          "widths": [50],
          "contrast": 1.8,
          "invert": true,
          "crop": "0,0,0,2",
          "directions": ["left", "right"]
        }
      }
    },
    "tree1": {
      "source": "originals/trees/tree1/tree.gif",
      "widths": [15, 20, 25, 30, 40, 55, 75, 100, 130, 160, 200, 250, 320, 350],
      "contrast": 1.5,
      "invert": true
    }
  },
  "layers": [
    {"name": "sky", "type": "static", "layer": 35},
    {"name": "grass-front", "sprites": ["grass"], "layer": 6, "tile": true}
  ],
  "autoLayers": {
    "sprites": ["tree1", "tree2"],
    "minLayer": 8,
    "maxLayer": 30,
    "treesPerLayer": 2,
    "seed": 42
  },
  "settings": {
    "fps": 60,
    "scrollSpeed": 90,
    "depthSpeed": 30,
    "animation": {
      "walk": 120,
      "idle": 500,
      "jump": 58,
      "transition": 85,
      "hop": 150
    }
  },
  "audio": {
    "enabled": true,
    "masterVolume": 0.5,
    "tracks": [
      {"id": "lofi", "path": "audio/lofi.mp3", "volume": 1.0, "loop": true, "tags": {}}
    ]
  }
}
```

### Sprite Options

- **source**: Path to GIF, video, or image
- **widths**: Array of character widths to generate
- **contrast**: Contrast multiplier (1.0 = normal)
- **brightness**: Brightness multiplier (1.0 = normal)
- **invert**: Invert colors before conversion
- **crop**: `"left,top,right,bottom"` in pixels or percentages
- **directions**: `["left", "right"]` for mirrored variants
- **gradient**: Character set (`"minimalist"`, `"standard"`, `"detailed"`)

## Sprite Pipeline

Sprites are generated from source GIFs/videos by a Python pipeline:

1. `gif_to_ascii.py` extracts frames, applies image adjustments (contrast, brightness, crop, invert), and converts each frame to ASCII using a character gradient
2. `generate_sprites.py` reads `config.json` and batch-generates TypeScript modules for every sprite at every width and direction
3. Each module exports a `frames` array of template literal strings

```bash
# Regenerate all sprites from config.json
poetry run python -m scripts.generate_sprites

# Manual single conversion
poetry run python -m tools.gif_to_ascii input.gif --width 50 --contrast 1.8 --invert
```

### Character Gradients

| Name | Characters | Use |
|------|-----------|-----|
| minimalist | ` . - + #` | Trees, bunny, most sprites |
| standard | ` . : - = + * # % @` | Higher detail |
| detailed | 70+ characters | Maximum detail |

## Movement Speed

The camera has exactly one mover, `input/movement.ts`, driven by config:

| Setting | Meaning |
|---------|---------|
| scrollSpeed | Horizontal pan speed, world units per second |
| depthSpeed | Depth speed while hopping, world units per second |

Movement speed and animation speed are independent, so slowing the world down
does not make the bunny's legs move in slow motion, and vice versa.

Animation frame intervals live under `settings.animation`, in milliseconds.
They are durations, not rates: a larger number holds each frame longer and
plays that animation more slowly.

| Interval | Animation |
|----------|-----------|
| walk | Walk cycle |
| idle | Idle loop |
| jump | One-shot jump |
| transition | Turns and walk-to-idle changeovers |
| hop | Depth hop loop |

A jump keeps whatever horizontal movement was in effect, so jumping mid-stride
carries forward through the arc rather than stopping in mid-air. That applies
to the autopilot too: it schedules its jump inside a walk leg, not at the end
of one.

## Development

```bash
# Run all checks (lint + test)
make check

# Individual commands
make lint      # ESLint + mypy + ruff + tsc --noEmit
make test      # Vitest + pytest with coverage
make build     # Generate sprites + compile TS
make dev       # Build + start dev server on :5173
make clean     # Remove dist/, node_modules/, .venv/
```
