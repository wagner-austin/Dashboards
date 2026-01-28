#!/usr/bin/env python3
"""
GIF/Video to ASCII Art Converter
================================

Converts GIF animations or video files to ASCII art at multiple sizes.
Outputs both individual .txt files and Python-ready FRAMES arrays.

Usage Examples:
---------------
    # Basic conversion (medium size, 10 frames)
    python gif_to_ascii.py input.gif --output output_dir/

    # Multiple sizes for parallax/depth effect (far, medium, close)
    python gif_to_ascii.py input.mp4 --widths 20,58,100 --output frames/

    # With color inversion (for light backgrounds)
    python gif_to_ascii.py input.gif --invert --output frames/

    # Flipped horizontally (for left/right variants)
    python gif_to_ascii.py input.gif --flip --output frames_flipped/

    # Custom frame count and contrast
    python gif_to_ascii.py input.mp4 --frames 8 --contrast 2.5 --output frames/

    # Preview without saving
    python gif_to_ascii.py input.gif --preview

Supported Formats:
------------------
    - GIF (.gif)
    - MP4 (.mp4)
    - AVI (.avi)
    - MOV (.mov)
    - WebM (.webm)
    - MKV (.mkv)
    - Single images (.png, .jpg, etc.)

Output:
-------
    For each width, creates:
    - w{width}_frame00.txt, w{width}_frame01.txt, ... (individual frames)
    - w{width}_frames.py (Python file with FRAMES = [...] array)

Character Gradient:
-------------------
    Uses the "minimalist" gradient by default: " .+-#"
    - Space = lightest (background)
    - .     = light
    - +     = medium
    - -     = medium-dark
    - #     = darkest

    This matches the asciiart.eu "Minimalist" preset.
"""

import argparse
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps
import cv2
import numpy as np


# =============================================================================
# CHARACTER GRADIENTS
# =============================================================================
# Maps brightness values to characters. Ordered from light to dark.
# The "minimalist" gradient matches asciiart.eu's output.

GRADIENTS = {
    "minimalist": " .-+#",  # 5 chars - matches asciiart.eu "Minimalist"
    "standard": " .:-=+*#%@",  # 10 chars - more detail
    "detailed": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
}


# =============================================================================
# IMAGE PROCESSING
# =============================================================================

def adjust_image(img, brightness=1.0, contrast=2.0, saturation=1.0, invert=False):
    """
    Apply image adjustments before ASCII conversion.

    Args:
        img: PIL Image
        brightness: Brightness multiplier (1.0 = no change)
        contrast: Contrast multiplier (2.0 = double contrast, matches asciiart.eu default)
        saturation: Color saturation (1.0 = no change, affects grayscale conversion)
        invert: If True, invert colors (use for light backgrounds)

    Returns:
        Adjusted PIL Image
    """
    if saturation != 1.0:
        img = ImageEnhance.Color(img).enhance(saturation)
    if brightness != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brightness)
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if invert:
        # Invert colors - useful when source has light background
        # but you want dark background (spaces) in ASCII output
        img = ImageOps.invert(img.convert("RGB"))
    return img


def image_to_ascii(img, width=58, gradient="minimalist", space_density=1):
    """
    Convert a PIL Image to ASCII art string.

    Args:
        img: PIL Image to convert
        width: Output width in characters
        gradient: Name of gradient from GRADIENTS dict, or custom string
        space_density: Repeat spaces this many times (for wider spacing)

    Returns:
        ASCII art as a multi-line string
    """
    # Get gradient characters (light to dark)
    chars = GRADIENTS.get(gradient, gradient)

    # Calculate height - ASCII chars are roughly 2x taller than wide,
    # so we halve the height to maintain aspect ratio
    aspect_ratio = img.height / img.width
    height = int(width * aspect_ratio * 0.5)

    # Resize image to target dimensions
    img = img.resize((width, height), Image.Resampling.LANCZOS)

    # Convert to grayscale (L = luminance)
    img = img.convert("L")

    # Get pixel values as flat list
    pixels = list(img.getdata())

    # Map each pixel brightness (0-255) to a character
    ascii_chars = []
    for pixel in pixels:
        # Map 0-255 to gradient index
        # pixel=0 (black) -> first char (lightest, usually space)
        # pixel=255 (white) -> last char (darkest, usually #)
        # Note: This assumes inverted images where dark=background
        idx = int(pixel / 256 * len(chars))
        idx = min(idx, len(chars) - 1)
        char = chars[idx]

        # Optional: repeat spaces for different density
        if char == ' ' and space_density > 1:
            char = ' ' * space_density
        ascii_chars.append(char)

    # Split into lines based on width
    lines = []
    for i in range(0, len(ascii_chars), width):
        line = ''.join(ascii_chars[i:i + width])
        lines.append(line)

    return '\n'.join(lines)


# =============================================================================
# FRAME EXTRACTION
# =============================================================================

def extract_gif_frames(gif_path):
    """
    Extract all frames from an animated GIF.

    Args:
        gif_path: Path to GIF file

    Returns:
        List of PIL Images (RGB)
    """
    img = Image.open(gif_path)
    frames = []

    try:
        while True:
            # Convert to RGBA to handle transparency
            frame = img.convert("RGBA")

            # Composite onto white background (transparent -> white)
            background = Image.new("RGBA", frame.size, (255, 255, 255, 255))
            frame = Image.alpha_composite(background, frame)
            frame = frame.convert("RGB")

            frames.append(frame.copy())
            img.seek(img.tell() + 1)  # Move to next frame
    except EOFError:
        pass  # End of frames

    return frames


def extract_video_frames(video_path, num_frames=10):
    """
    Extract evenly-spaced frames from a video file using OpenCV.

    Args:
        video_path: Path to video file (MP4, AVI, MOV, etc.)
        num_frames: Number of frames to extract

    Returns:
        List of PIL Images (RGB)
    """
    cap = cv2.VideoCapture(str(video_path))

    # Get total frame count
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        total_frames = 1000  # Fallback for streams

    frames = []

    # Calculate which frames to extract (evenly spaced)
    frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]

    for idx in frame_indices:
        # Seek to frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()

        if ret:
            # OpenCV uses BGR, convert to RGB for PIL
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            frames.append(img)

    cap.release()
    return frames


def extract_frames(file_path, num_frames=10):
    """
    Extract frames from any supported file type.

    Args:
        file_path: Path to GIF, video, or image file
        num_frames: Number of frames to extract (for videos)

    Returns:
        List of PIL Images
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".gif":
        # GIFs: extract all frames (ignore num_frames)
        return extract_gif_frames(file_path)
    elif ext in [".mp4", ".avi", ".mov", ".webm", ".mkv"]:
        # Videos: extract specified number of frames
        return extract_video_frames(file_path, num_frames)
    else:
        # Single image: return as single-frame list
        img = Image.open(file_path).convert("RGB")
        return [img]


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_media(file_path, widths, gradient="minimalist", brightness=1.0,
                  contrast=2.0, flip=False, invert=False, output_dir=None, num_frames=10):
    """
    Process a media file and output ASCII frames at multiple sizes.

    Args:
        file_path: Path to input GIF/video/image
        widths: List of output widths (e.g., [20, 58, 100])
        gradient: Character gradient name or custom string
        brightness: Brightness adjustment (1.0 = no change)
        contrast: Contrast adjustment (2.0 = asciiart.eu default)
        flip: If True, flip frames horizontally
        invert: If True, invert colors (for light backgrounds)
        output_dir: Directory to save output files (None = don't save)
        num_frames: Number of frames to extract from videos

    Returns:
        Dict mapping size keys to lists of ASCII strings
        e.g., {"w20": [...], "w58": [...], "w100": [...]}
    """
    # Extract frames from source
    frames = extract_frames(file_path, num_frames=num_frames)
    print(f"Extracted {len(frames)} frames from {file_path}")

    results = {}

    # Process each width
    for width in widths:
        size_key = f"w{width}"
        results[size_key] = []

        for i, frame in enumerate(frames):
            # Apply image adjustments
            adjusted = adjust_image(
                frame,
                brightness=brightness,
                contrast=contrast,
                invert=invert
            )

            # Flip horizontally if requested (for left/right variants)
            if flip:
                adjusted = ImageOps.mirror(adjusted)

            # Convert to ASCII
            ascii_art = image_to_ascii(adjusted, width=width, gradient=gradient)
            results[size_key].append(ascii_art)

            print(f"  Width {width}, Frame {i + 1}/{len(frames)} done")

    # Save output files
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create __init__.py for package import
        init_file = output_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f"# ASCII frames generated from: {Path(file_path).name}\n")

        for size_key, ascii_frames in results.items():
            # Save Python-ready .py file with FRAMES array
            py_file = output_path / f"{size_key}_frames.py"
            with open(py_file, 'w') as f:
                f.write(f'"""{size_key} frames ({len(ascii_frames)} total)."""\n')
                f.write(f"# Generated from: {Path(file_path).name}\n")
                f.write(f"# Settings: contrast={contrast}, brightness={brightness}")
                f.write(f", invert={invert}, flip={flip}\n\n")
                f.write("FRAMES = [\n")
                for frame in ascii_frames:
                    f.write('    """\\\n')
                    for line in frame.split('\n'):
                        f.write(f'{line}\n')
                    f.write('""",\n')
                f.write("]\n")

            print(f"Saved {size_key}_frames.py to {output_path}")

    return results


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Convert GIF/video to ASCII art at multiple sizes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s bunny.gif --output bunny_frames/
  %(prog)s tree.mp4 --widths 20,58,100 --frames 10 --invert --output tree_frames/
  %(prog)s sprite.gif --flip --output sprite_right/
  %(prog)s video.mp4 --preview
        """
    )

    parser.add_argument("input", help="Path to GIF, video, or image file")
    parser.add_argument("--widths", default="58",
                        help="Comma-separated output widths (default: 58)")
    parser.add_argument("--frames", type=int, default=10,
                        help="Number of frames to extract from video (default: 10)")
    parser.add_argument("--gradient", default="minimalist",
                        choices=list(GRADIENTS.keys()),
                        help="Character gradient (default: minimalist)")
    parser.add_argument("--brightness", type=float, default=1.0,
                        help="Brightness multiplier (default: 1.0)")
    parser.add_argument("--contrast", type=float, default=2.0,
                        help="Contrast multiplier (default: 2.0)")
    parser.add_argument("--flip", action="store_true",
                        help="Flip horizontally (for left/right variants)")
    parser.add_argument("--invert", action="store_true",
                        help="Invert colors (use for light backgrounds)")
    parser.add_argument("--output", "-o",
                        help="Output directory (omit to skip saving)")
    parser.add_argument("--preview", action="store_true",
                        help="Print first frame to terminal")

    args = parser.parse_args()

    # Parse widths
    widths = [int(w.strip()) for w in args.widths.split(",")]

    # Process the file
    results = process_media(
        args.input,
        widths=widths,
        gradient=args.gradient,
        brightness=args.brightness,
        contrast=args.contrast,
        flip=args.flip,
        invert=args.invert,
        output_dir=args.output,
        num_frames=args.frames
    )

    # Preview first frame if requested
    if args.preview:
        first_key = list(results.keys())[0]
        print(f"\n--- Preview ({first_key}, frame 0) ---\n")
        print(results[first_key][0])


if __name__ == "__main__":
    main()
