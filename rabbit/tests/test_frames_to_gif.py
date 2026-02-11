"""Tests for scripts/frames_to_gif module."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image
from scripts import _test_hooks as hooks
from scripts.frames_to_gif import (
    create_gif,
    generate_gif,
    get_sorted_frames,
    parse_frame_delay,
)


def get_gif_frame_count(path: Path) -> int:
    """Get the number of frames in a GIF file.

    Args:
        path: Path to the GIF file.

    Returns:
        Number of frames in the GIF.
    """
    img = Image.open(path)
    count: int = getattr(img, "n_frames", 1)
    img.close()
    return count


def verify_gif_format(path: Path) -> bool:
    """Verify a file is a valid GIF.

    Args:
        path: Path to the file.

    Returns:
        True if the file is a GIF.
    """
    img = Image.open(path)
    result = img.format == "GIF"
    img.close()
    return result


class FakeHooks:
    """Fake hooks for testing without side effects."""

    def __init__(self) -> None:
        self.messages: list[str] = []
        self.exit_codes: list[int] = []

    def print_message(self, msg: str) -> None:
        self.messages.append(msg)

    def exit_process(self, code: int) -> None:
        self.exit_codes.append(code)


@contextmanager
def fake_hooks_context() -> Iterator[FakeHooks]:
    """Context manager to set up and tear down fake hooks."""
    fakes = FakeHooks()
    original_print = hooks.print_message
    original_exit = hooks.exit_process

    hooks.print_message = fakes.print_message
    hooks.exit_process = fakes.exit_process

    yield fakes

    hooks.print_message = original_print
    hooks.exit_process = original_exit


def create_test_frame(
    path: Path, size: tuple[int, int] = (10, 10), color: tuple[int, int, int, int] | None = None
) -> None:
    """Create a test PNG frame with unique content."""
    if color is None:
        # Use path hash to create unique colors for each frame
        color_val = hash(str(path)) % 256
        color = (color_val, 255 - color_val, (color_val * 2) % 256, 255)
    img = Image.new("RGBA", size, color=color)
    img.save(path)


class TestParseFrameDelay:
    """Tests for parse_frame_delay function."""

    def test_parses_decimal_delay(self) -> None:
        """Parse delay from filename with decimal seconds."""
        assert parse_frame_delay("frame_0_delay-0.4s.png") == 400

    def test_parses_integer_delay(self) -> None:
        """Parse delay from filename with integer seconds."""
        assert parse_frame_delay("frame_1_delay-1s.png") == 1000

    def test_parses_small_delay(self) -> None:
        """Parse delay from filename with small decimal."""
        assert parse_frame_delay("frame_2_delay-0.05s.png") == 50

    def test_raises_on_missing_pattern(self) -> None:
        """Raise ValueError when delay pattern not found."""
        with pytest.raises(ValueError, match="No delay pattern found"):
            parse_frame_delay("frame_0.png")

    def test_raises_on_invalid_filename(self) -> None:
        """Raise ValueError for filename without delay."""
        with pytest.raises(ValueError, match="No delay pattern found"):
            parse_frame_delay("random_file.png")


class TestGetSortedFrames:
    """Tests for get_sorted_frames function."""

    def test_returns_sorted_frames(self, tmp_path: Path) -> None:
        """Return frames sorted by frame number."""
        # Create frames out of order
        create_test_frame(tmp_path / "frame_2_delay-0.1s.png")
        create_test_frame(tmp_path / "frame_0_delay-0.1s.png")
        create_test_frame(tmp_path / "frame_1_delay-0.1s.png")

        result = get_sorted_frames(tmp_path)

        assert len(result) == 3
        assert result[0].name == "frame_0_delay-0.1s.png"
        assert result[1].name == "frame_1_delay-0.1s.png"
        assert result[2].name == "frame_2_delay-0.1s.png"

    def test_raises_on_empty_directory(self, tmp_path: Path) -> None:
        """Raise ValueError when no PNG frames found."""
        with pytest.raises(ValueError, match="No PNG frames found"):
            get_sorted_frames(tmp_path)

    def test_raises_on_unparseable_frame_number(self, tmp_path: Path) -> None:
        """Raise ValueError when frame number can't be parsed."""
        # Create a file that matches glob but can't parse frame number
        create_test_frame(tmp_path / "frame_X_delay-0.1s.png")

        with pytest.raises(ValueError, match="Cannot parse frame number"):
            get_sorted_frames(tmp_path)


class TestCreateGif:
    """Tests for create_gif function."""

    def test_creates_gif_from_frames(self, tmp_path: Path) -> None:
        """Create GIF from frame images."""
        frame0 = tmp_path / "frame_0_delay-0.1s.png"
        frame1 = tmp_path / "frame_1_delay-0.2s.png"
        create_test_frame(frame0, color=(255, 0, 0, 255))
        create_test_frame(frame1, color=(0, 255, 0, 255))
        output = tmp_path / "output.gif"

        create_gif([frame0, frame1], output)

        assert output.exists()
        assert verify_gif_format(output)
        assert get_gif_frame_count(output) == 2

    def test_creates_pingpong_gif(self, tmp_path: Path) -> None:
        """Create ping-pong GIF with reversed frames."""
        frames = []
        colors = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (255, 255, 0, 255)]
        for i in range(4):
            path = tmp_path / f"frame_{i}_delay-0.1s.png"
            create_test_frame(path, color=colors[i])
            frames.append(path)
        output = tmp_path / "pingpong.gif"

        create_gif(frames, output, pingpong=True)

        assert output.exists()
        # 4 frames + 2 reversed (excluding endpoints) = 6 frames
        assert get_gif_frame_count(output) == 6

    def test_pingpong_with_two_frames(self, tmp_path: Path) -> None:
        """Ping-pong with only 2 frames stays at 2 frames."""
        frames = []
        colors = [(255, 0, 0, 255), (0, 255, 0, 255)]
        for i in range(2):
            path = tmp_path / f"frame_{i}_delay-0.1s.png"
            create_test_frame(path, color=colors[i])
            frames.append(path)
        output = tmp_path / "pingpong.gif"

        create_gif(frames, output, pingpong=True)

        assert output.exists()
        # 2 frames is not > 2, so no pingpong effect
        assert get_gif_frame_count(output) == 2

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """Create parent directories if they don't exist."""
        frame = tmp_path / "frame_0_delay-0.1s.png"
        create_test_frame(frame)
        output = tmp_path / "subdir" / "nested" / "output.gif"

        create_gif([frame], output)

        assert output.exists()


class TestGenerateGif:
    """Tests for generate_gif function."""

    def test_generates_gif_with_default_output(self, tmp_path: Path) -> None:
        """Generate GIF with default output path."""
        create_test_frame(tmp_path / "frame_0_delay-0.1s.png")
        create_test_frame(tmp_path / "frame_1_delay-0.1s.png")

        with fake_hooks_context() as fakes:
            result = generate_gif(str(tmp_path))

        assert result == tmp_path / "animation.gif"
        assert result.exists()
        assert "Created" in fakes.messages[0]
        assert "2 frames" in fakes.messages[0]

    def test_generates_gif_with_custom_output(self, tmp_path: Path) -> None:
        """Generate GIF with custom output path."""
        create_test_frame(tmp_path / "frame_0_delay-0.1s.png")
        output = tmp_path / "custom.gif"

        with fake_hooks_context():
            result = generate_gif(str(tmp_path), output=str(output))

        assert result == output
        assert output.exists()

    def test_generates_pingpong_gif(self, tmp_path: Path) -> None:
        """Generate ping-pong GIF when requested."""
        colors = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (255, 255, 0, 255)]
        for i in range(4):
            create_test_frame(tmp_path / f"frame_{i}_delay-0.1s.png", color=colors[i])

        with fake_hooks_context():
            result = generate_gif(str(tmp_path), pingpong=True)

        assert get_gif_frame_count(result) == 6

    def test_exits_on_invalid_directory(self, tmp_path: Path) -> None:
        """Exit with error when source is not a directory."""
        fake_file = tmp_path / "not_a_dir.txt"
        fake_file.write_text("test")

        with fake_hooks_context() as fakes, pytest.raises(SystemExit):
            generate_gif(str(fake_file))

        assert fakes.exit_codes == [1]
        assert "not a directory" in fakes.messages[0]

    def test_exits_on_nonexistent_path(self, tmp_path: Path) -> None:
        """Exit with error when source path doesn't exist."""
        with fake_hooks_context() as fakes, pytest.raises(SystemExit):
            generate_gif(str(tmp_path / "nonexistent"))

        assert fakes.exit_codes == [1]


class TestMain:
    """Tests for main CLI function."""

    def test_main_with_source_dir(self, tmp_path: Path) -> None:
        """Main function processes source directory."""
        create_test_frame(tmp_path / "frame_0_delay-0.1s.png")

        with fake_hooks_context(), patch("sys.argv", ["frames_to_gif", str(tmp_path)]):
            from scripts.frames_to_gif import main

            main()

        assert (tmp_path / "animation.gif").exists()

    def test_main_with_output_option(self, tmp_path: Path) -> None:
        """Main function handles --output option."""
        create_test_frame(tmp_path / "frame_0_delay-0.1s.png")
        output = tmp_path / "custom.gif"
        argv = ["frames_to_gif", str(tmp_path), "-o", str(output)]

        with fake_hooks_context(), patch("sys.argv", argv):
            from scripts.frames_to_gif import main

            main()

        assert output.exists()

    def test_main_with_pingpong_option(self, tmp_path: Path) -> None:
        """Main function handles --pingpong option."""
        colors = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (255, 255, 0, 255)]
        for i in range(4):
            create_test_frame(tmp_path / f"frame_{i}_delay-0.1s.png", color=colors[i])
        argv = ["frames_to_gif", str(tmp_path), "--pingpong"]

        with fake_hooks_context(), patch("sys.argv", argv):
            from scripts.frames_to_gif import main

            main()

        assert get_gif_frame_count(tmp_path / "animation.gif") == 6
