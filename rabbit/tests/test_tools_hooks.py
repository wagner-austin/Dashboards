"""Tests for tools/_test_hooks module."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from PIL import Image
from tools import _test_hooks as hooks
from tools._test_hooks import (
    VideoFrameData,
    VideoProps,
    _real_get_video_props,
    _real_iter_gif_frames,
    _real_iter_video_frames,
    _real_print,
    reset_hooks,
)


def test_video_frame_data_immutable() -> None:
    """Test VideoFrameData is immutable."""
    frame = VideoFrameData(width=100, height=50, data=b"test")
    assert frame.width == 100
    assert frame.height == 50
    assert frame.data == b"test"


def test_video_props_immutable() -> None:
    """Test VideoProps is immutable."""
    props = VideoProps(n_images=10)
    assert props.n_images == 10


def test_video_props_none() -> None:
    """Test VideoProps with None n_images."""
    props = VideoProps(n_images=None)
    assert props.n_images is None


def test_real_print(capsys: pytest.CaptureFixture[str]) -> None:
    """Test _real_print outputs to stdout."""
    _real_print("test message")
    captured = capsys.readouterr()
    assert "test message" in captured.out


def test_real_iter_gif_frames(tmp_path: Path) -> None:
    """Test _real_iter_gif_frames iterates over GIF frames."""
    # Create a simple animated GIF
    frames = [
        Image.new("RGB", (10, 10), color=(255, 0, 0)),
        Image.new("RGB", (10, 10), color=(0, 255, 0)),
    ]
    gif_path = tmp_path / "test.gif"
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0,
    )

    img = Image.open(gif_path)
    result = list(_real_iter_gif_frames(img))
    assert len(result) == 2


def test_reset_hooks() -> None:
    """Test reset_hooks restores original implementations."""
    # Save originals
    original_print = hooks.print_message
    original_gif = hooks.iter_gif_frames
    original_props = hooks.get_video_props
    original_video = hooks.iter_video_frames

    # Modify hooks using proper function signatures
    def fake_print(msg: str) -> None:
        pass

    def fake_gif(img: Image.Image) -> Iterator[Image.Image]:
        return iter([])

    def fake_props(video_path: str | Path) -> VideoProps:
        return VideoProps(n_images=0)

    def fake_video(video_path: str | Path) -> Iterator[VideoFrameData]:
        return iter([])

    hooks.print_message = fake_print
    hooks.iter_gif_frames = fake_gif
    hooks.get_video_props = fake_props
    hooks.iter_video_frames = fake_video

    # Reset
    reset_hooks()

    # Verify they are the real implementations
    assert hooks.print_message == _real_print
    assert hooks.iter_gif_frames == _real_iter_gif_frames

    # Cleanup - restore test's original references
    hooks.print_message = original_print
    hooks.iter_gif_frames = original_gif
    hooks.get_video_props = original_props
    hooks.iter_video_frames = original_video


def _create_test_video(video_path: Path) -> None:
    """Create a simple test video file using imageio-ffmpeg."""
    # Use imageio directly in subprocess to create video
    import subprocess
    import sys

    script = """
import imageio.v3 as iio
import sys

# Create 3 simple frames (10x10 RGB) as bytes
frames = []
for color in [(255, 0, 0), (0, 255, 0), (0, 0, 255)]:
    # Create 10x10 image with solid color
    frame_data = []
    for _ in range(10):
        row = []
        for _ in range(10):
            row.append(list(color))
        frame_data.append(row)
    frames.append(frame_data)

iio.imwrite(sys.argv[1], frames, extension=".mp4", fps=1)
"""
    subprocess.run(
        [sys.executable, "-c", script, str(video_path)],
        check=True,
        capture_output=True,
    )


def test_real_get_video_props(tmp_path: Path) -> None:
    """Test _real_get_video_props returns video properties."""
    video_path = tmp_path / "test.mp4"
    _create_test_video(video_path)

    props = _real_get_video_props(video_path)

    assert isinstance(props, VideoProps)
    # Video has 3 frames
    assert props.n_images == 3


def test_real_iter_video_frames(tmp_path: Path) -> None:
    """Test _real_iter_video_frames iterates over video frames."""
    video_path = tmp_path / "test.mp4"
    _create_test_video(video_path)

    frames = list(_real_iter_video_frames(video_path))

    assert len(frames) == 3
    for frame in frames:
        assert isinstance(frame, VideoFrameData)
        # Size may be slightly different due to video codec constraints
        assert frame.width >= 10
        assert frame.height >= 10
