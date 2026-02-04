#!/usr/bin/env python3
"""GIF/Video to ASCII Art Converter.

Converts GIF animations, video files, or static images to ASCII art at multiple sizes.
Outputs both individual .txt files and Python-ready FRAMES arrays.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

from tools import _test_hooks as hooks

# Character gradients - maps brightness values to characters (light to dark)
GRADIENTS: dict[str, str] = {
    "minimalist": " .-+#",
    "standard": " .:-=+*#%@",
    "detailed": (" .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"),
}


@dataclass(frozen=True)
class CliArgs:
    """Typed CLI arguments."""

    input_path: str
    widths: list[int]
    num_frames: int
    gradient: str
    brightness: float
    contrast: float
    flip: bool
    invert: bool
    crop: str | None
    trim_rows: int
    output_format: str
    output_dir: str | None
    preview: bool


def crop_image(img: Image.Image, crop_spec: str | None) -> Image.Image:
    """Crop an image based on specification.

    Args:
        img: PIL Image
        crop_spec: Crop specification string:
            - "25%" = 25% from all sides
            - "25%,10%" = 25% from left/right, 10% from top/bottom
            - "10,20,10,20" = pixels: left, top, right, bottom

    Returns:
        Cropped PIL Image

    Raises:
        ValueError: If crop_spec format is invalid.
    """
    if not crop_spec:
        return img

    w, h = img.size
    parts = crop_spec.replace(" ", "").split(",")

    left: int
    right: int
    top: int
    bottom: int

    if len(parts) == 1:
        val = parts[0]
        if val.endswith("%"):
            pct = float(val[:-1]) / 100
            left = right = int(w * pct)
            top = bottom = int(h * pct)
        else:
            left = right = top = bottom = int(val)
    elif len(parts) == 2:
        h_val, v_val = parts
        if h_val.endswith("%"):
            pct = float(h_val[:-1]) / 100
            left = right = int(w * pct)
        else:
            left = right = int(h_val)
        if v_val.endswith("%"):
            pct = float(v_val[:-1]) / 100
            top = bottom = int(h * pct)
        else:
            top = bottom = int(v_val)
    elif len(parts) == 4:
        vals: list[int] = []
        for i, val in enumerate(parts):
            dim = w if i in [0, 2] else h
            if val.endswith("%"):
                vals.append(int(dim * float(val[:-1]) / 100))
            else:
                vals.append(int(val))
        left, top, right, bottom = vals[0], vals[1], vals[2], vals[3]
    else:
        msg = f"Invalid crop spec: {crop_spec}"
        raise ValueError(msg)

    return img.crop((left, top, w - right, h - bottom))


def adjust_image(
    img: Image.Image,
    brightness: float = 1.0,
    contrast: float = 2.0,
    saturation: float = 1.0,
    invert: bool = False,
) -> Image.Image:
    """Apply image adjustments before ASCII conversion."""
    result = img
    if saturation != 1.0:
        result = ImageEnhance.Color(result).enhance(saturation)
    if brightness != 1.0:
        result = ImageEnhance.Brightness(result).enhance(brightness)
    if contrast != 1.0:
        result = ImageEnhance.Contrast(result).enhance(contrast)
    if invert:
        result = ImageOps.invert(result.convert("RGB"))
    return result


def image_to_ascii(
    img: Image.Image,
    width: int = 58,
    gradient: str = "minimalist",
    space_density: int = 1,
    trim_rows: int = 0,
) -> str:
    """Convert a PIL Image to ASCII art string."""
    chars = GRADIENTS.get(gradient, gradient)

    aspect_ratio = img.height / img.width
    height = int(width * aspect_ratio * 0.5)

    resized = img.resize((width, height), Image.Resampling.LANCZOS)
    grayscale = resized.convert("L")

    # Get pixel data as bytes for typed access
    pixel_bytes: bytes = grayscale.tobytes()
    pixels: list[int] = list(pixel_bytes)

    ascii_chars: list[str] = []
    for pixel_val in pixels:
        idx = int(pixel_val / 256 * len(chars))
        idx = min(idx, len(chars) - 1)
        char = chars[idx]

        if char == " " and space_density > 1:
            char = " " * space_density
        ascii_chars.append(char)

    lines: list[str] = []
    for i in range(0, len(ascii_chars), width):
        line = "".join(ascii_chars[i : i + width])
        lines.append(line)

    # Trim rows from bottom if requested
    if trim_rows > 0 and len(lines) > trim_rows:
        lines = lines[:-trim_rows]

    return "\n".join(lines)


def extract_gif_frames(gif_path: str | Path) -> list[Image.Image]:
    """Extract all frames from an animated GIF using PIL."""
    img = Image.open(gif_path)
    frames: list[Image.Image] = []

    for frame in hooks.iter_gif_frames(img):
        frame_rgba = frame.convert("RGBA")
        background = Image.new("RGBA", frame_rgba.size, (255, 255, 255, 255))
        composited = Image.alpha_composite(background, frame_rgba)
        frames.append(composited.convert("RGB"))

    return frames


def extract_video_frames(video_path: str | Path, num_frames: int = 10) -> list[Image.Image]:
    """Extract evenly-spaced frames from a video file."""
    props = hooks.get_video_props(video_path)
    total_frames = props.n_images if props.n_images is not None else 1000

    frame_indices = {int(i * total_frames / num_frames) for i in range(num_frames)}

    frames: list[Image.Image] = []
    for frame_idx, frame_data in enumerate(hooks.iter_video_frames(video_path)):
        if frame_idx in frame_indices:
            size = (frame_data.width, frame_data.height)
            pil_img = Image.frombytes("RGB", size, frame_data.data)
            frames.append(pil_img)
            if len(frames) >= num_frames:
                break

    return frames


def extract_frames(file_path: str | Path, num_frames: int = 10) -> list[Image.Image]:
    """Extract frames from supported file types.

    Supports:
        - .gif: Animated GIF (extracts all frames)
        - .mp4, .avi, .mov, .webm, .mkv: Video files (extracts num_frames)
        - .png, .jpg, .jpeg, .bmp, .webp: Static images (returns single frame)

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If file format is unsupported.
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".gif":
        return extract_gif_frames(file_path)

    if ext in [".mp4", ".avi", ".mov", ".webm", ".mkv"]:
        return extract_video_frames(file_path, num_frames)

    if ext in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
        img = Image.open(file_path).convert("RGB")
        return [img]

    supported = ".gif, .mp4, .avi, .mov, .webm, .mkv, .png, .jpg, .jpeg, .bmp, .webp"
    msg = f"Unsupported format: {ext}. Supported: {supported}"
    raise ValueError(msg)


def _save_js_output(
    output_path: Path,
    size_key: str,
    suffix: str,
    ascii_frames: list[str],
    file_path: str | Path,
    contrast: float,
    brightness: float,
    invert: bool,
    flip: bool,
    crop: str | None,
    direct_file: bool = False,
) -> None:
    """Save frames as JavaScript module.

    Args:
        output_path: Directory to save to, or exact file path if direct_file=True
        size_key: Size identifier (e.g. "w50")
        suffix: Optional suffix (e.g. "_right")
        ascii_frames: List of ASCII art strings
        file_path: Source file path for header comment
        contrast: Contrast setting for header comment
        brightness: Brightness setting for header comment
        invert: Invert setting for header comment
        flip: Flip setting for header comment
        crop: Crop setting for header comment
        direct_file: If True, output_path is the exact file to write
    """
    ts_file = output_path if direct_file else output_path / f"{size_key}{suffix}_frames.ts"
    with ts_file.open("w") as f:
        f.write(f"// {size_key} frames ({len(ascii_frames)} total)\n")
        f.write(f"// Generated from: {Path(file_path).name}\n")
        f.write(f"// Settings: contrast={contrast}, brightness={brightness}")
        f.write(f", invert={invert}, flip={flip}")
        if crop:
            f.write(f", crop={crop}")
        f.write("\n\n")
        f.write("export const frames: readonly string[] = [\n")
        for frame in ascii_frames:
            escaped = frame.replace("\\", "\\\\").replace("`", "\\`")
            escaped = escaped.replace("${", "\\${")
            f.write(f"`{escaped}`,\n")
        f.write("];\n")
    hooks.print_message(f"Saved {ts_file.name} to {ts_file.parent}")


def _save_py_output(
    output_path: Path,
    size_key: str,
    suffix: str,
    ascii_frames: list[str],
    file_path: str | Path,
    contrast: float,
    brightness: float,
    invert: bool,
    flip: bool,
    crop: str | None,
    direct_file: bool = False,
) -> None:
    """Save frames as Python module.

    Args:
        output_path: Directory to save to, or exact file path if direct_file=True
        size_key: Size identifier (e.g. "w50")
        suffix: Optional suffix (e.g. "_right")
        ascii_frames: List of ASCII art strings
        file_path: Source file path for header comment
        contrast: Contrast setting for header comment
        brightness: Brightness setting for header comment
        invert: Invert setting for header comment
        flip: Flip setting for header comment
        crop: Crop setting for header comment
        direct_file: If True, output_path is the exact file to write
    """
    if direct_file:
        py_file = output_path
    else:
        init_file = output_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f"# ASCII frames generated from: {Path(file_path).name}\n")
        py_file = output_path / f"{size_key}{suffix}_frames.py"

    with py_file.open("w") as f:
        f.write(f'"""{size_key} frames ({len(ascii_frames)} total)."""\n')
        f.write(f"# Generated from: {Path(file_path).name}\n")
        f.write(f"# Settings: contrast={contrast}, brightness={brightness}")
        f.write(f", invert={invert}, flip={flip}")
        if crop:
            f.write(f", crop={crop}")
        f.write("\n\n")
        f.write("FRAMES = [\n")
        for frame in ascii_frames:
            f.write('    """\\\n')
            for line in frame.split("\n"):
                f.write(f"{line}\n")
            f.write('""",\n')
        f.write("]\n")
    hooks.print_message(f"Saved {py_file.name} to {py_file.parent}")


def process_media(
    file_path: str | Path,
    widths: list[int],
    gradient: str = "minimalist",
    brightness: float = 1.0,
    contrast: float = 2.0,
    flip: bool = False,
    invert: bool = False,
    output_dir: str | Path | None = None,
    num_frames: int = 10,
    crop: str | None = None,
    output_format: str = "py",
    trim_rows: int = 0,
) -> dict[str, list[str]]:
    """Process a media file and output ASCII frames at multiple sizes."""
    frames = extract_frames(file_path, num_frames=num_frames)
    hooks.print_message(f"Extracted {len(frames)} frames from {file_path}")

    results: dict[str, list[str]] = {}

    for width in widths:
        size_key = f"w{width}"
        results[size_key] = []

        for i, frame in enumerate(frames):
            if crop:
                frame = crop_image(frame, crop)

            adjusted = adjust_image(
                frame,
                brightness=brightness,
                contrast=contrast,
                invert=invert,
            )

            if flip:
                adjusted = ImageOps.mirror(adjusted)

            ascii_art = image_to_ascii(
                adjusted, width=width, gradient=gradient, trim_rows=trim_rows
            )
            results[size_key].append(ascii_art)

            hooks.print_message(f"  Width {width}, Frame {i + 1}/{len(frames)} done")

    if output_dir:
        output_path = Path(output_dir)

        # Check if output is a direct file (ends with .ts/.js and single width)
        is_direct_ts = (
            (str(output_dir).endswith(".ts") or str(output_dir).endswith(".js"))
            and len(widths) == 1
            and output_format == "js"
        )
        is_direct_py = (
            str(output_dir).endswith(".py") and len(widths) == 1 and output_format == "py"
        )

        if is_direct_ts or is_direct_py:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path.mkdir(parents=True, exist_ok=True)

        for size_key, ascii_frames in results.items():
            suffix = "_right" if flip else ""

            if output_format == "js":
                _save_js_output(
                    output_path,
                    size_key,
                    suffix,
                    ascii_frames,
                    file_path,
                    contrast,
                    brightness,
                    invert,
                    flip,
                    crop,
                    direct_file=is_direct_ts,
                )
            else:
                _save_py_output(
                    output_path,
                    size_key,
                    suffix,
                    ascii_frames,
                    file_path,
                    contrast,
                    brightness,
                    invert,
                    flip,
                    crop,
                    direct_file=is_direct_py,
                )

    return results


def parse_args(argv: list[str] | None = None) -> CliArgs:
    """Parse command line arguments into typed dataclass."""
    parser = argparse.ArgumentParser(
        description="Convert GIF/video/images to ASCII art at multiple sizes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("input", help="Path to GIF, video, or image file")
    parser.add_argument(
        "--widths", default="58", help="Comma-separated output widths (default: 58)"
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=10,
        help="Number of frames to extract from video (default: 10)",
    )
    parser.add_argument(
        "--gradient",
        default="minimalist",
        choices=list(GRADIENTS.keys()),
        help="Character gradient (default: minimalist)",
    )
    parser.add_argument(
        "--brightness",
        type=float,
        default=1.0,
        help="Brightness multiplier (default: 1.0)",
    )
    parser.add_argument(
        "--contrast",
        type=float,
        default=2.0,
        help="Contrast multiplier (default: 2.0)",
    )
    parser.add_argument(
        "--flip",
        action="store_true",
        help="Flip horizontally (for left/right variants)",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert colors (use for light backgrounds)",
    )
    parser.add_argument(
        "--crop",
        help="Crop before converting: '25%%' (all sides), '10,20,10,20' (l,t,r,b)",
    )
    parser.add_argument(
        "--format",
        default="py",
        choices=["py", "js"],
        help="Output format: 'py' for Python, 'js' for JavaScript (default: py)",
    )
    parser.add_argument("--output", "-o", help="Output directory (omit to skip saving)")
    parser.add_argument(
        "--trim-rows",
        type=int,
        default=0,
        help="Number of rows to trim from bottom of ASCII output (default: 0)",
    )
    parser.add_argument("--preview", action="store_true", help="Print first frame to terminal")

    args = parser.parse_args(argv)

    # Access Namespace attributes with explicit type annotations
    # Type annotation overrides Any from argparse.Namespace
    input_val: str = args.input
    widths_val: str = args.widths
    frames_val: int = args.frames
    gradient_val: str = args.gradient
    brightness_val: float = args.brightness
    contrast_val: float = args.contrast
    flip_val: bool = args.flip
    invert_val: bool = args.invert
    crop_val: str | None = args.crop
    trim_rows_val: int = args.trim_rows
    format_val: str = args.format
    output_val: str | None = args.output
    preview_val: bool = args.preview

    widths_list = [int(w.strip()) for w in widths_val.split(",")]

    return CliArgs(
        input_path=input_val,
        widths=widths_list,
        num_frames=frames_val,
        gradient=gradient_val,
        brightness=brightness_val,
        contrast=contrast_val,
        flip=flip_val,
        invert=invert_val,
        crop=crop_val,
        trim_rows=trim_rows_val,
        output_format=format_val,
        output_dir=output_val,
        preview=preview_val,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    cli_args = parse_args(argv)

    results = process_media(
        cli_args.input_path,
        widths=cli_args.widths,
        gradient=cli_args.gradient,
        brightness=cli_args.brightness,
        contrast=cli_args.contrast,
        flip=cli_args.flip,
        invert=cli_args.invert,
        output_dir=cli_args.output_dir,
        num_frames=cli_args.num_frames,
        crop=cli_args.crop,
        output_format=cli_args.output_format,
        trim_rows=cli_args.trim_rows,
    )

    if cli_args.preview:
        first_key = next(iter(results.keys()))
        hooks.print_message(f"\n--- Preview ({first_key}, frame 0) ---\n")
        first_frames = results[first_key]
        if first_frames:
            hooks.print_message(first_frames[0])

    return 0


if __name__ == "__main__":
    sys.exit(main())
