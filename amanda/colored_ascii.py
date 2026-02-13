"""Convert GIF to colored ASCII HTML frames."""
from PIL import Image, ImageEnhance
from pathlib import Path

# Character gradient (light to dark) - using lighter chars for brightness
GRADIENT = " .:#"


def image_to_colored_ascii(img: Image.Image, width: int = 80) -> str:
    """Convert image to colored ASCII HTML."""
    aspect_ratio = img.height / img.width
    height = int(width * aspect_ratio * 0.5)

    resized = img.resize((width, height), Image.Resampling.LANCZOS)
    rgb = resized.convert("RGB")
    grayscale = resized.convert("L")

    rgb_pixels = list(rgb.getdata())
    gray_pixels = list(grayscale.getdata())

    html_chars: list[str] = []
    for i, (r, g, b) in enumerate(rgb_pixels):
        brightness = gray_pixels[i]
        idx = int(brightness / 256 * len(GRADIENT))
        idx = min(idx, len(GRADIENT) - 1)
        char = GRADIENT[idx]

        if char == " ":
            html_chars.append(" ")
        else:
            color = f"#{r:02x}{g:02x}{b:02x}"
            html_chars.append(f'<span style="color:{color}">{char}</span>')

    lines: list[str] = []
    for i in range(0, len(html_chars), width):
        line = "".join(html_chars[i : i + width])
        lines.append(line)

    return "\n".join(lines)


def extract_gif_frames(gif_path: Path) -> list[Image.Image]:
    """Extract all frames from GIF."""
    img = Image.open(gif_path)
    frames: list[Image.Image] = []

    try:
        while True:
            frame = img.copy().convert("RGBA")
            bg = Image.new("RGBA", frame.size, (255, 255, 255, 255))
            composited = Image.alpha_composite(bg, frame)
            frames.append(composited.convert("RGB"))
            img.seek(img.tell() + 1)
    except EOFError:
        pass

    return frames


def main() -> None:
    gif_path = Path("originals/happy birthday/happy_birthday.gif")
    output_path = Path("src/sprites/happy_birthday_colored/frames.ts")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading {gif_path}...")
    frames = extract_gif_frames(gif_path)
    print(f"Extracted {len(frames)} frames")

    html_frames: list[str] = []
    for i, frame in enumerate(frames):
        # Apply contrast enhancement
        enhanced = ImageEnhance.Contrast(frame).enhance(2.0)
        html = image_to_colored_ascii(enhanced, width=160)
        html_frames.append(html)
        print(f"  Frame {i + 1}/{len(frames)} done")

    # Write as TypeScript module
    with output_path.open("w", encoding="utf-8") as f:
        f.write("// Colored ASCII frames for happy birthday\n")
        f.write("export const frames: readonly string[] = [\n")
        for html in html_frames:
            escaped = html.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
            f.write(f"`{escaped}`,\n")
        f.write("];\n")

    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
