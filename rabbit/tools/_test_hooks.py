"""Test hooks for gif_to_ascii module.

Production code uses real implementations set at module load.
Tests replace hooks with fakes for isolation.
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageSequence


@dataclass(frozen=True)
class VideoFrameData:
    """Typed container for video frame data."""

    width: int
    height: int
    data: bytes


@dataclass(frozen=True)
class VideoProps:
    """Video properties from imageio."""

    n_images: int | None


# Subprocess script for video property extraction
_VIDEO_PROPS_SCRIPT = """
import json
import sys
import imageio.v3 as iio
props = iio.improps(sys.argv[1], plugin="pyav")
print(json.dumps({"n_images": props.n_images}))
"""

# Subprocess script for video frame extraction
_VIDEO_FRAMES_SCRIPT = """
import base64
import json
import sys
import imageio.v3 as iio
for frame in iio.imiter(sys.argv[1], plugin="pyav"):
    data = {
        "width": int(frame.shape[1]),
        "height": int(frame.shape[0]),
        "data": base64.b64encode(frame.tobytes()).decode("ascii")
    }
    print(json.dumps(data), flush=True)
"""


def _real_print(msg: str) -> None:
    """Print a message to stdout."""
    print(msg)


def _real_iter_gif_frames(img: Image.Image) -> Iterator[Image.Image]:
    """Iterate over frames in an animated GIF."""
    return ImageSequence.Iterator(img)


def _real_get_video_props(video_path: str | Path) -> VideoProps:
    """Get video properties using subprocess to isolate untyped imageio code."""
    result = subprocess.run(
        [sys.executable, "-c", _VIDEO_PROPS_SCRIPT, str(video_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    data: dict[str, int | None] = json.loads(result.stdout.strip())
    n_images: int | None = data.get("n_images")
    return VideoProps(n_images=n_images)


class VideoFrameStreamError(RuntimeError):
    """Raised when a frame-extraction subprocess cannot be read or fails."""


def _decode_frame_stream(proc: subprocess.Popen[str]) -> Iterator[VideoFrameData]:
    """Decode the JSON frame lines a frame-extraction subprocess writes.

    Args:
        proc: The subprocess, started with ``stdout=subprocess.PIPE`` and ``text=True``.
            Each non-blank stdout line is one JSON object with ``width``, ``height``
            and base64 ``data``; a blank line carries no frame and is skipped.

    Yields:
        VideoFrameData: One decoded frame per non-blank line, in stream order.

    Raises:
        VideoFrameStreamError: ``VIDEO_FRAMES_NO_STDOUT`` when the process was started
            without a stdout pipe, or ``VIDEO_FRAMES_EXIT`` when it exits non-zero.
    """
    stdout = proc.stdout
    if stdout is None:
        msg = "VIDEO_FRAMES_NO_STDOUT: the frame extractor was started without stdout=PIPE"
        raise VideoFrameStreamError(msg)

    for line in stdout:
        line = line.strip()
        if not line:
            continue
        data: dict[str, str | int] = json.loads(line)
        width: int = int(data["width"])
        height: int = int(data["height"])
        data_str: str = str(data["data"])
        frame_bytes: bytes = base64.b64decode(data_str)
        yield VideoFrameData(width=width, height=height, data=frame_bytes)

    returncode = proc.wait()
    if returncode != 0:
        msg = f"VIDEO_FRAMES_EXIT: the frame extractor exited with status {returncode}"
        raise VideoFrameStreamError(msg)


def _real_iter_video_frames(video_path: str | Path) -> Iterator[VideoFrameData]:
    """Iterate over video frames using subprocess to isolate untyped imageio code.

    The extractor's stderr is inherited rather than piped, so a decode failure is
    printed where the caller reads it instead of filling a pipe nobody drains.

    Args:
        video_path: The video file to decode.

    Returns:
        Iterator[VideoFrameData]: The decoded frames, in stream order.
    """
    proc = subprocess.Popen(
        [sys.executable, "-c", _VIDEO_FRAMES_SCRIPT, str(video_path)],
        stdout=subprocess.PIPE,
        text=True,
    )
    return _decode_frame_stream(proc)


# Module-level hooks - production uses real implementations
# Tests replace these with fakes
print_message = _real_print
iter_gif_frames = _real_iter_gif_frames
get_video_props = _real_get_video_props
iter_video_frames = _real_iter_video_frames


def reset_hooks() -> None:
    """Reset all hooks to production implementations."""
    global print_message, iter_gif_frames, get_video_props, iter_video_frames
    print_message = _real_print
    iter_gif_frames = _real_iter_gif_frames
    get_video_props = _real_get_video_props
    iter_video_frames = _real_iter_video_frames
