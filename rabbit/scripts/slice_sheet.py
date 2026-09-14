"""Register generated sprite poses on one canvas without rescaling individual frames."""

from pathlib import Path

from PIL import Image, ImageChops


def slice_sheet(
    source: Path,
    boxes: tuple[tuple[int, int, int, int], ...],
    output: Path,
    lifts: tuple[int, ...],
    delay: str,
) -> tuple[Path, ...]:
    """Slice explicitly reviewed cells and align their feet on a common baseline.

    Args:
        source: Source sheet PNG path.
        boxes: Reviewed, nonoverlapping crop rectangles in pixel coordinates.
        output: Destination directory for registered frame PNGs.
        lifts: Deliberate airborne height per pose, in pixels.
        delay: Frame duration string used by the existing GIF builder.

    Returns:
        Ordered paths to equal-size frame canvases.

    Raises:
        ValueError: SPRITE_LAYOUT if the layout is empty or lift counts differ.
        ValueError: SPRITE_CELL if a cell contains no visible character.
        ValueError: SPRITE_BOUNDS if a cell or lift is outside the valid range.
    """
    if not boxes or len(boxes) != len(lifts):
        raise ValueError("SPRITE_LAYOUT: Each cell needs an explicit airborne lift.")
    sheet = Image.open(source).convert("RGB")
    poses: list[Image.Image] = []
    for box, lift in zip(boxes, lifts, strict=True):
        left, top, right, bottom = box
        if not (0 <= left < right <= sheet.width and 0 <= top < bottom <= sheet.height):
            raise ValueError("SPRITE_BOUNDS: Crop must be inside the source sheet.")
        if lift < 0:
            raise ValueError("SPRITE_BOUNDS: Airborne lift must be nonnegative.")
        cell = sheet.crop(box)
        difference = ImageChops.difference(cell, Image.new("RGB", cell.size, "white"))
        mask = difference.convert("L").point(_ink_pixel)
        bounds = mask.getbbox()
        if bounds is None:
            raise ValueError("SPRITE_CELL: Reviewed cell contains no character.")
        poses.append(cell.crop(bounds))
    width = max(pose.width for pose in poses) + 32
    height = max(pose.height + lift for pose, lift in zip(poses, lifts, strict=True)) + 32
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, (pose, lift) in enumerate(zip(poses, lifts, strict=True)):
        canvas = Image.new("RGB", (width, height), "white")
        canvas.paste(pose, ((width - pose.width) // 2, height - 16 - pose.height - lift))
        path = output / f"frame_{index}_delay-{delay}s.png"
        canvas.save(path)
        paths.append(path)
    return tuple(paths)


def _ink_pixel(value: int) -> int:
    """Separate character ink from minor noise on the white sheet background."""
    return 255 if value > 45 else 0
