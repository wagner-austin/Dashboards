"""Generate GIF from PNG frames in a directory.

Reads PNG frames with delay encoded in filenames (e.g., frame_0_delay-0.4s.png)
and creates an animated GIF with proper timing.
"""

import re
from pathlib import Path

from PIL import Image

from scripts import _test_hooks as hooks


def parse_frame_delay(filename: str) -> int:
    """Extract delay in milliseconds from filename.

    Args:
        filename: Filename like 'frame_0_delay-0.4s.png'

    Returns:
        Delay in milliseconds (e.g., 400 for 0.4s)

    Raises:
        ValueError: If delay pattern not found in filename.
    """
    match = re.search(r"delay-(\d+\.?\d*)s", filename)
    if match is None:
        raise ValueError(f"No delay pattern found in filename: {filename}")
    return int(float(match.group(1)) * 1000)


def get_sorted_frames(directory: Path) -> list[Path]:
    """Get PNG frames sorted by frame number.

    Handles both single-digit (frame_0) and padded (frame_03) numbering.

    Args:
        directory: Directory containing frame_N_delay-Xs.png files.

    Returns:
        List of frame paths sorted by frame number.

    Raises:
        ValueError: If no PNG frames found or frame numbers can't be parsed.
    """
    frames = list(directory.glob("frame_*_delay-*.png"))
    if len(frames) == 0:
        raise ValueError(f"No PNG frames found in {directory}")

    def get_frame_number(path: Path) -> int:
        # Match frame_N or frame_NN (with optional leading zeros)
        match = re.search(r"frame_(\d+)", path.name)
        if match is None:
            raise ValueError(f"Cannot parse frame number from: {path.name}")
        return int(match.group(1))  # int() handles leading zeros

    return sorted(frames, key=get_frame_number)


def create_gif(
    frame_paths: list[Path],
    output_path: Path,
    pingpong: bool = False,
) -> None:
    """Create GIF from frame images.

    Args:
        frame_paths: Ordered list of frame image paths.
        output_path: Path for output GIF file.
        pingpong: If True, play frames forward then backward (excluding endpoints).
    """
    frames: list[Image.Image] = []
    durations: list[int] = []

    for path in frame_paths:
        img = Image.open(path).convert("RGBA")
        frames.append(img)
        durations.append(parse_frame_delay(path.name))

    if pingpong and len(frames) > 2:
        # Add frames in reverse, excluding first and last to avoid duplicates
        frames = frames + frames[-2:0:-1]
        durations = durations + durations[-2:0:-1]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        transparency=0,
        disposal=2,
    )


def generate_gif(
    source_dir: str,
    output: str | None = None,
    pingpong: bool = False,
) -> Path:
    """Generate GIF from PNG frames in a directory.

    Args:
        source_dir: Directory containing frame_N_delay-Xs.png files.
        output: Output GIF path. Defaults to source_dir/animation.gif.
        pingpong: If True, create ping-pong animation.

    Returns:
        Path to the created GIF file.
    """
    source_path = Path(source_dir)
    if not source_path.is_dir():
        hooks.print_message(f"Error: {source_dir} is not a directory")
        hooks.exit_process(1)
        raise SystemExit(1)

    frame_paths = get_sorted_frames(source_path)
    output_path = source_path / "animation.gif" if output is None else Path(output)

    create_gif(frame_paths, output_path, pingpong=pingpong)
    hooks.print_message(f"Created {output_path} ({len(frame_paths)} frames)")

    return output_path


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate GIF from PNG frames in a directory")
    parser.add_argument(
        "source_dir",
        help="Directory containing frame_N_delay-Xs.png files",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output GIF path (default: source_dir/animation.gif)",
    )
    parser.add_argument(
        "--pingpong",
        "-p",
        action="store_true",
        help="Create ping-pong animation (play forward then backward)",
    )

    args = parser.parse_args()
    source_dir: str = args.source_dir
    output: str | None = args.output
    pingpong: bool = args.pingpong
    generate_gif(source_dir, output, pingpong)


if __name__ == "__main__":
    main()
