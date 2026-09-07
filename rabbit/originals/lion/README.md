# Lion Animations

Blue lion, generated rather than drawn. Same eight animations as the bunny, so
it drives the same state machine.

The engine picks the character from `config.json` (`"character": "lion"`), and
`?character=lion` on the page URL overrides it for previewing — see the root
README.

## Why sprite sheets

Frames are generated a **whole cycle at a time**, as one image holding N poses
in a row, then sliced apart. That is the entire trick, and it exists because
the hard problem is not drawing a lion — it is drawing the *same* lion twice.

A model asked for frame 2 in a fresh call has no memory of frame 1 and will
quietly redesign the mane, so a cycle assembled from separate calls flickers
between subtly different animals. Inside one image it cannot drift from
itself, so character identity comes free. What it does **not** give you is
registration, and that half is fixed with arithmetic afterwards.

`lion_ref.png` (in the scratchpad, regenerate from `prompt_ref.txt`) is the
character reference passed to every cycle's generation, which is what keeps
the cycles consistent with each other rather than merely internally
consistent.

## Recipe

```bash
# 1. one sheet per cycle, sliced into registered frames
python cycles.py walk idle jump ...

# 2. frames -> gif  (delays are read from the filenames)
poetry run python -m scripts.frames_to_gif originals/lion/lion_walk_animation \
    --output originals/lion/lion_walk_animation/walk.gif

# 3. gif -> ascii TS modules, per config.json
poetry run python -m scripts.generate_sprites

# 4. judge it before wiring it
make dev   # then /preview.html — onion skin + churn
```

## What the slicer has to fix, and why

Three things went wrong in ways that were not visible until several steps
later. All three are handled in `slice.py`; none needs better prompting.

**Registration drift.** Measured on the first walk sheet: panel 2 came out
**12% narrower** than panel 1 and its feet sat **25px higher**. Played back
that reads as the lion pulsing and floating, not walking. Fixed by cropping
each figure to its own ink bounding box, scaling every frame in a cycle by
**one shared factor**, and standing them all on a common baseline.

The shared factor matters: scaling each frame to its own target height would
flatten the animation's real vertical bob along with the drift, because at the
bounding-box level the two are the same signal.

**Figures overlap in X without touching.** The obvious segmentation — cut on
empty columns — does not work. A lion's tail curls back far enough to sit in
the same *columns* as the previous lion's face, with clear white space
between them, so there is no empty column to cut on even though the figures
never touch. They are 2D connected components; that is the question to ask.
Having found them, cropping each component's bounding *rectangle* re-imports
the neighbour's intruding tail, so each frame is rebuilt from its own
component mask alone, on white.

Whiskers are why the component-size floor exists: they detach from the face at
this resolution and would each count as a figure.

**Facing is not reliable.** A sheet prompted "every lion faces LEFT" came back
with all four facing right, and an earlier one had exactly one panel mirrored.
So facing is aligned mechanically: each figure's 64×64 silhouette is compared
against the character reference as-is and mirrored, and flipped if the mirror
fits better. Aligning against the *reference* rather than against the sheet's
own first frame is deliberate — per-sheet alignment keeps each cycle
internally consistent while letting walk face one way and jump the other,
which only surfaces once both are in the engine.

Left and right variants are **not** generated: `generate_sprites.py` mirrors
them from this art (`flip=True` for `right`). Only one facing is ever drawn.

**The slicer refuses rather than guesses.** If it does not find exactly the
expected number of figures it fails and prints what it found. An even split of
a sheet whose figures merged would cut a lion in half, and that error would
only surface as garbage ASCII several steps later.

## Judging a cycle

`preview.html` is the tool. Churn is a comparison against the same animation's
bunny figure, not an absolute score — see the root README.

Measured on the walk cycle after registration: **54% / 63% / 69%, mean 62%**,
against the bunny walk's 70%. Frames all 25 ASCII rows, which is the
registration check — unequal row counts mean the figures are still drifting.

Before registration the same cycle measured 72%, which looked healthy and was
not: the churn was the lion changing *size* between frames, not its legs
moving. Churn alone cannot tell those apart. Onion skin can, and the row
counts give it away.

## Frame counts

Nothing requires the lion to match the bunny's counts — every timer in
`Bunny.ts` reads `frames.length`.

| Animation | Frames | Delay |
|-----------|--------|-------|
| walk | 4 | 0.12s |
| idle | 3 | 0.5s |
| walk_to_idle | 3 | 0.3s |
| jump | 6 | 0.06s |
| walk_to_turn_away | 2 | 0.4s |
| walk_to_turn_toward | 2 | 0.4s |
| hop_away | 4 | 0.4s |
| hop_toward | 4 | 0.4s |

The jump is 6 rather than the bunny's 17: the bunny's came from a video, and
17 distinct poses is not something a sheet holds at usable resolution.

`hop_away` and `hop_toward` are rear and front views, so they are undirected —
the character has no side when it is facing away from or toward the camera.
Config must declare them with fewer than two directions or the loader refuses
the character at startup, naming the animation.

## Generation notes

- Model: `gemini-3-pro-image`, falling back to `gemini-3.1-flash-image` /
  `gemini-2.5-flash-image`. All three return 503 "experiencing high demand"
  often; a single attempt is not a test of anything, so the driver retries
  across models with a delay.
- Aspect ratio is set per cycle to roughly N:1 so panels stay square-ish.
- The prompt asks for a wide white gap between figures and no whiskers
  crossing it. It is not reliably honoured, which is why the slicer segments
  in 2D instead of depending on it.
