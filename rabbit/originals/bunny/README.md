# Bunny Animations

## Folders

Active animations (used in config.json):

- **bunny_idle_animation** - Sitting/resting loop (3 frames)
- **bunny_walk_animation** - Walking loop (4 frames)
- **bunny_jump_animation** - Jump arc, one-shot (17 frames)
- **bunny_walk_to_idle_transition** - Deceleration transition (3 frames)
- **bunny_walk_to_turn_away_transition** - Turn away from camera (2 frames)
- **bunny_walk_to_turn_toward_transition** - Turn toward camera (2 frames)
- **bunny_hop_away_animation** - Hopping into depth loop (4 frames)
- **bunny_hop_toward_animation** - Hopping out of depth loop (4 frames)

Unused (legacy or reference):

- **bunny_idle** - Original idle frames
- **bunny_sit_alert** - Alert/attentive pose
- **bunny_sit_eat_animation** - Eating animation
- **bunny_stand_alert_animation** - Standing alert

## GIF Generation Settings

- **Ping-pong**: Yes for idle, No for walk/jump/hop/transitions
- **Loop**: Infinite
- **Disposal**: 2 (restore to background)
- **Transparency**: 0
- **Convert**: RGBA

GIFs can be regenerated from frame PNGs using `scripts/frames_to_gif.py`.

## Frame Delays

Delays are encoded in filenames (e.g., `frame_0_delay-0.4s.png` = 400ms).

### bunny_idle_animation
| Frame | Delay |
|-------|-------|
| 0-2   | 0.4s  |

### bunny_walk_animation
| Frame | Delay |
|-------|-------|
| 0-3   | 0.09s |

### bunny_jump_animation
| Frame | Delay |
|-------|-------|
| 3-20  | 0.03s |
| 21    | 0.02s |

### bunny_walk_to_idle_transition
| Frame | Delay |
|-------|-------|
| 0-2   | 0.3s  |

### bunny_walk_to_turn_away_transition
| Frame | Delay |
|-------|-------|
| 0-1   | 0.4s  |

### bunny_walk_to_turn_toward_transition
| Frame | Delay |
|-------|-------|
| 0-1   | 0.4s  |

### bunny_hop_away_animation
| Frame | Delay |
|-------|-------|
| 0-3   | 0.4s  |

### bunny_hop_toward_animation
| Frame | Delay |
|-------|-------|
| 0-3   | 0.4s  |

## ASCII Conversion Settings

All sprites are generated via `config.json` and `scripts/generate_sprites.py`.

| Animation | Contrast | Invert | Width | Crop | Directions |
|-----------|----------|--------|-------|------|------------|
| walk | 1.8 | Yes | 50 | 0,0,0,2 | left, right |
| jump | 3.3 | Yes | 50 | 25%,0,25%,0 | left, right |
| idle | 1.4 | Yes | 40 | -- | left, right |
| walk_to_idle | 1.4 | Yes | 40 | -- | left, right |
| walk_to_turn_away | 1.4 | Yes | 40 | -- | -- |
| walk_to_turn_toward | 1.4 | Yes | 40 | -- | -- |
| hop_away | 1.4 | Yes | 40 | -- | -- |
| hop_toward | 1.4 | Yes | 40 | -- | -- |

## Image Preprocessing

The idle frames were manually edited in a photo editor before GIF generation with these settings:

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

Additional programmatic adjustments were applied (warmth shift, brightness, contrast, noise, unsharp mask, vignette) before the GIF was created. The other animations use the source frames directly.
