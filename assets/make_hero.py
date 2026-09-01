"""Key the sky out of the raven GIF and emit an animated WebP with real alpha.

The subject is a dark bird against bright blue sky. Sky pixels have a large
blue-minus-red difference; the bird — including its grey wing highlights — does
not. Deriving alpha from that difference on a ramp keeps the motion blur soft,
which a 1-bit GIF transparency mask cannot do.
"""
from PIL import Image

SRC = r"C:\Users\Test\PROJECTS\Dashboards\assets\hero.gif"
OUT = r"C:\Users\Test\PROJECTS\Dashboards\assets\hero.webp"

# Blue-minus-red at which a pixel counts as fully sky. Measured from the
# source: corners read 96-128, the bird reads well under 40.
FULL_SKY = 88.0
# Below this the pixel is fully opaque subject.
FULL_SUBJECT = 30.0


def frame_to_rgba(frame: Image.Image) -> Image.Image:
    rgba = frame.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            skyness = (b - r - FULL_SUBJECT) / (FULL_SKY - FULL_SUBJECT)
            skyness = 0.0 if skyness < 0.0 else (1.0 if skyness > 1.0 else skyness)
            px[x, y] = (r, g, b, int(round(255 * (1.0 - skyness))))
    return rgba


def main() -> None:
    src = Image.open(SRC)
    frames = []
    durations = []
    for i in range(getattr(src, "n_frames", 1)):
        src.seek(i)
        frames.append(frame_to_rgba(src))
        durations.append(src.info.get("duration", 300))

    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        lossless=True,
    )
    print(f"wrote {OUT}: {len(frames)} frames, {frames[0].size}")


if __name__ == "__main__":
    main()
