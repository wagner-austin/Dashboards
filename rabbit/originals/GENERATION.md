# Companion animation assets

Generated with the built-in image generation tool on September 13, 2026.
Original assets remain in their existing folders. New sheets, registered PNGs,
and GIFs are committed under `lion/lion_run_animation` and
`bunny/bunny_upright_animation`.

## Prompts

Lion reference: `lion/lion_walk_animation/frame_0_delay-0.12s.png`.

> Create a production sprite sheet for this exact blue lion character, keeping the cyan blue body, dark indigo-purple mane, face and pixel-art aesthetic. Reference image is identity/style reference. Exactly FOUR frames in a 2 by 2 equal-cell grid, read left to right top to bottom, showing a fast RUN / gallop cycle: 1 rear legs pushing off, forelegs reaching; 2 full airborne extension; 3 forelegs landing hindlegs coming forward; 4 compressed gathered legs before push-off. Every lion faces LEFT in strict side view. Clean crisp pixel art, no blur or ghost limbs, consistent anatomy and size across every frame. Flat pure WHITE background. Each complete lion including tail and all feet entirely inside its cell with broad white margins. Identical camera, body scale and foot ground baseline relative to each cell. No text, no numbers, no grid lines, no shadows. Distinct articulated leg poses so the four images work as animation keyframes; use the same lion design in all four.

Rabbit references: `bunny/bunny_sit_alert/frame_0_delay-0.4s.png` and
`bunny/bunny_stand_alert_animation/frame_1_delay-0.4s.png`.

> Production pixel-art sprite sheet, exactly 4 animation keyframes in an evenly spaced 2x2 grid. Use references for the same tan-brown rabbit with pink ears, dark outline, white tail. A continuous SITTING UP ON HIND LEGS / LOOKING AROUND animation: 1 crouched on all fours facing LEFT in strict side profile, 2 raising chest with forepaws lifting, 3 upright balanced on hind legs forepaws tucked at chest, 4 still upright ears perked and head slightly looking toward viewer. Keep rabbit identity, body proportions, pixel-art style and camera scale identical across every frame. Pure solid white background, NO shadows, text, grid, or labels. Every entire rabbit including ears and tail fully visible and centered horizontally inside its equal cell with wide white margins. Feet at exactly the same ground baseline within each cell. Do NOT enlarge shorter poses; upright frames are naturally taller. This will convert to monochrome ASCII, so clear silhouette and crisp leg outlines are essential.

## Reproduce the registered frames

From the `rabbit` directory, using its Poetry environment:

```python
from pathlib import Path
from scripts.slice_sheet import slice_sheet
from scripts.frames_to_gif import create_gif

lion = Path("originals/lion/lion_run_animation")
frames = slice_sheet(
    lion / "sheet.png",
    ((0, 0, 748, 526), (748, 0, 1495, 526),
     (0, 526, 748, 1052), (748, 526, 1495, 1052)),
    lion, (0, 26, 0, 0), "0.08",
)
create_gif(list(frames), lion / "run.gif")

rabbit = Path("originals/bunny/bunny_upright_animation")
frames = slice_sheet(
    rabbit / "sheet.png",
    ((0, 0, 650, 550), (650, 0, 1303, 550),
     (0, 550, 650, 1207), (650, 550, 1303, 1207)),
    rabbit, (0, 0, 0, 0), "0.3",
)
create_gif(list(frames), rabbit / "upright.gif")
```

Then run `make build`. The normal converter generates both facings; no
direction-specific redraw is involved. Crop boundaries were inspected visually:
the rabbit's lower row starts above the sheet's halfway point, so blindly
dividing it into four equal rectangles cuts its ears. The slicer preserves each
pose's size and uses one shared canvas with a foot baseline. The airborne lion
frame retains a deliberate 26-pixel lift.

In-game sprint timing is 75 ms per pose; the downloadable GIF uses 80 ms
because GIF timing is quantized to hundredths of a second. Upright poses use
300 ms and hold the last pose while the rabbit rests.
