"""Tests for gif_to_ascii module."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from PIL import Image
from tools import _test_hooks as hooks
from tools._test_hooks import VideoFrameData, VideoProps
from tools.gif_to_ascii import (
    adjust_image,
    crop_image,
    extract_frames,
    extract_gif_frames,
    extract_video_frames,
    image_to_ascii,
    main,
    parse_args,
    process_media,
)


class FakeHooks:
    """Fake hooks for testing without real files."""

    def __init__(self) -> None:
        self.messages: list[str] = []
        self.gif_frames: list[Image.Image] = []
        self.video_props: VideoProps = VideoProps(n_images=10)
        self.video_frames: list[VideoFrameData] = []

    def print_message(self, msg: str) -> None:
        self.messages.append(msg)

    def iter_gif_frames(self, img: Image.Image) -> Iterator[Image.Image]:
        return iter(self.gif_frames)

    def get_video_props(self, video_path: str | Path) -> VideoProps:
        return self.video_props

    def iter_video_frames(self, video_path: str | Path) -> Iterator[VideoFrameData]:
        return iter(self.video_frames)


@contextmanager
def fake_hooks_context() -> Iterator[FakeHooks]:
    """Context manager to set up and tear down fake hooks."""
    fakes = FakeHooks()
    original_print = hooks.print_message
    original_gif = hooks.iter_gif_frames
    original_props = hooks.get_video_props
    original_video = hooks.iter_video_frames

    hooks.print_message = fakes.print_message
    hooks.iter_gif_frames = fakes.iter_gif_frames
    hooks.get_video_props = fakes.get_video_props
    hooks.iter_video_frames = fakes.iter_video_frames

    yield fakes

    hooks.print_message = original_print
    hooks.iter_gif_frames = original_gif
    hooks.get_video_props = original_props
    hooks.iter_video_frames = original_video


def create_test_image() -> Image.Image:
    """Create a simple test image."""
    return Image.new("RGB", (100, 100), color=(128, 128, 128))


def test_crop_image_none_spec() -> None:
    """Test crop_image with no crop spec returns original."""
    test_image = create_test_image()
    result = crop_image(test_image, None)
    assert result.size == (100, 100)


def test_crop_image_percentage_all_sides() -> None:
    """Test crop_image with percentage from all sides."""
    test_image = create_test_image()
    result = crop_image(test_image, "10%")
    assert result.size == (80, 80)


def test_crop_image_percentage_horizontal_vertical() -> None:
    """Test crop_image with separate horizontal and vertical percentages."""
    test_image = create_test_image()
    result = crop_image(test_image, "10%,20%")
    assert result.size == (80, 60)


def test_crop_image_pixel_horizontal_vertical() -> None:
    """Test crop_image with separate horizontal and vertical pixel values."""
    test_image = create_test_image()
    result = crop_image(test_image, "10,20")
    assert result.size == (80, 60)


def test_crop_image_pixel_all_sides() -> None:
    """Test crop_image with pixel value from all sides."""
    test_image = create_test_image()
    result = crop_image(test_image, "10")
    assert result.size == (80, 80)


def test_crop_image_pixel_four_values() -> None:
    """Test crop_image with four pixel values (left, top, right, bottom)."""
    test_image = create_test_image()
    result = crop_image(test_image, "10,20,10,20")
    assert result.size == (80, 60)


def test_crop_image_mixed_percentage_and_pixels() -> None:
    """Test crop_image with mixed percentages and pixels in four values."""
    test_image = create_test_image()
    result = crop_image(test_image, "10%,20,10%,20")
    assert result.size == (80, 60)


def test_crop_image_invalid_spec() -> None:
    """Test crop_image raises ValueError for invalid spec."""
    import pytest

    test_image = create_test_image()
    with pytest.raises(ValueError, match="Invalid crop spec"):
        crop_image(test_image, "1,2,3")


def test_adjust_image_default() -> None:
    """Test adjust_image with default parameters."""
    test_image = create_test_image()
    result = adjust_image(test_image)
    assert result.size == test_image.size


def test_adjust_image_brightness() -> None:
    """Test adjust_image with brightness adjustment."""
    test_image = create_test_image()
    result = adjust_image(test_image, brightness=1.5)
    assert result.size == test_image.size


def test_adjust_image_contrast() -> None:
    """Test adjust_image with contrast adjustment."""
    test_image = create_test_image()
    result = adjust_image(test_image, contrast=1.5)
    assert result.size == test_image.size


def test_adjust_image_no_contrast() -> None:
    """Test adjust_image skips contrast adjustment when contrast is 1.0."""
    test_image = create_test_image()
    result = adjust_image(test_image, contrast=1.0)
    assert result.size == test_image.size


def test_adjust_image_saturation() -> None:
    """Test adjust_image with saturation adjustment."""
    test_image = create_test_image()
    result = adjust_image(test_image, saturation=1.5)
    assert result.size == test_image.size


def test_adjust_image_invert() -> None:
    """Test adjust_image with color inversion."""
    test_image = create_test_image()
    result = adjust_image(test_image, invert=True)
    assert result.size == test_image.size


def test_image_to_ascii_basic() -> None:
    """Test image_to_ascii produces output."""
    test_image = create_test_image()
    result = image_to_ascii(test_image, width=20)
    assert len(result) > 0
    lines = result.split("\n")
    assert len(lines[0]) == 20


def test_image_to_ascii_custom_gradient() -> None:
    """Test image_to_ascii with custom gradient."""
    test_image = create_test_image()
    result = image_to_ascii(test_image, width=10, gradient="standard")
    assert len(result) > 0


def test_image_to_ascii_space_density() -> None:
    """Test image_to_ascii with space density."""
    # Create a black image that will produce spaces (gradient starts with space for dark)
    black_image = Image.new("RGB", (10, 10), color=(0, 0, 0))
    result = image_to_ascii(black_image, width=5, space_density=2)
    assert len(result) > 0
    # With space_density=2, each space becomes double space
    # Check that the first line has proper spacing
    first_line = result.split("\n")[0]
    assert "  " in first_line or len(first_line) > 5


def test_image_to_ascii_with_trim_rows() -> None:
    """Test image_to_ascii trims rows from bottom."""
    # Create a tall image that will produce many rows
    test_image = Image.new("RGB", (20, 40), color=(128, 128, 128))
    result_no_trim = image_to_ascii(test_image, width=10, trim_rows=0)
    result_with_trim = image_to_ascii(test_image, width=10, trim_rows=3)

    lines_no_trim = result_no_trim.split("\n")
    lines_with_trim = result_with_trim.split("\n")

    # Trimmed result should have 3 fewer lines
    assert len(lines_with_trim) == len(lines_no_trim) - 3


def test_extract_gif_frames(tmp_path: Path) -> None:
    """Test extract_gif_frames uses hooks."""
    test_image = create_test_image()
    # Create a real GIF file that Image.open can open
    gif_path = tmp_path / "test.gif"
    test_image.save(gif_path)

    with fake_hooks_context() as fakes:
        fakes.gif_frames = [test_image.copy(), test_image.copy()]
        result = extract_gif_frames(gif_path)
        assert len(result) == 2


def test_extract_video_frames() -> None:
    """Test extract_video_frames uses hooks."""
    with fake_hooks_context() as fakes:
        # With n_images=2 and num_frames=2, frame_indices will be {0, 1}
        fakes.video_props = VideoProps(n_images=2)
        # Create RGB frame data
        frame_data = bytes([128] * (100 * 100 * 3))
        fakes.video_frames = [
            VideoFrameData(width=100, height=100, data=frame_data),
            VideoFrameData(width=100, height=100, data=frame_data),
        ]
        result = extract_video_frames("test.mp4", num_frames=2)
        assert len(result) == 2


def test_extract_video_frames_none_n_images() -> None:
    """Test extract_video_frames handles None n_images."""
    with fake_hooks_context() as fakes:
        fakes.video_props = VideoProps(n_images=None)
        frame_data = bytes([128] * (100 * 100 * 3))
        fakes.video_frames = [
            VideoFrameData(width=100, height=100, data=frame_data),
        ]
        result = extract_video_frames("test.mp4", num_frames=1)
        assert len(result) == 1


def test_extract_video_frames_skips_intermediate_frames() -> None:
    """Test extract_video_frames skips frames not in frame_indices."""
    with fake_hooks_context() as fakes:
        # With n_images=10 and num_frames=2, frame_indices will be {0, 5}
        # Frames 1,2,3,4,6,7,8,9 should be skipped
        fakes.video_props = VideoProps(n_images=10)
        frame_data = bytes([128] * (100 * 100 * 3))
        fakes.video_frames = [
            VideoFrameData(width=100, height=100, data=frame_data),  # idx 0, keep
            VideoFrameData(width=100, height=100, data=frame_data),  # idx 1, skip
            VideoFrameData(width=100, height=100, data=frame_data),  # idx 2, skip
            VideoFrameData(width=100, height=100, data=frame_data),  # idx 3, skip
            VideoFrameData(width=100, height=100, data=frame_data),  # idx 4, skip
            VideoFrameData(width=100, height=100, data=frame_data),  # idx 5, keep
        ]
        result = extract_video_frames("test.mp4", num_frames=2)
        assert len(result) == 2


def test_extract_video_frames_loop_completes() -> None:
    """Test extract_video_frames when loop completes without break."""
    with fake_hooks_context() as fakes:
        # Request 5 frames but only provide 2 frames total
        # Loop should complete normally without hitting break
        fakes.video_props = VideoProps(n_images=2)
        frame_data = bytes([128] * (100 * 100 * 3))
        fakes.video_frames = [
            VideoFrameData(width=100, height=100, data=frame_data),
            VideoFrameData(width=100, height=100, data=frame_data),
        ]
        result = extract_video_frames("test.mp4", num_frames=5)
        assert len(result) == 2  # Only 2 frames available


def test_extract_frames_gif(tmp_path: Path) -> None:
    """Test extract_frames dispatches to GIF handler."""
    test_image = create_test_image()
    with fake_hooks_context() as fakes:
        fakes.gif_frames = [test_image]
        # Create a real GIF file for extension detection
        gif_path = tmp_path / "test.gif"
        test_image.save(gif_path)
        result = extract_frames(gif_path)
        assert len(result) == 1


def test_extract_frames_video() -> None:
    """Test extract_frames dispatches to video handler."""
    with fake_hooks_context() as fakes:
        fakes.video_props = VideoProps(n_images=10)
        frame_data = bytes([128] * (100 * 100 * 3))
        fakes.video_frames = [
            VideoFrameData(width=100, height=100, data=frame_data),
        ]
        result = extract_frames("test.mp4", num_frames=1)
        assert len(result) == 1


def test_extract_frames_static_image(tmp_path: Path) -> None:
    """Test extract_frames handles static images."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        result = extract_frames(png_path)
        assert len(result) == 1


def test_extract_frames_unsupported_format() -> None:
    """Test extract_frames raises for unsupported format."""
    import pytest

    with fake_hooks_context(), pytest.raises(ValueError, match="Unsupported format"):
        extract_frames("test.xyz")


def test_process_media_basic(tmp_path: Path) -> None:
    """Test process_media produces ASCII output."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        result = process_media(png_path, widths=[20])
        assert "w20" in result
        assert len(result["w20"]) == 1


def test_process_media_with_crop(tmp_path: Path) -> None:
    """Test process_media with crop option."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        result = process_media(png_path, widths=[20], crop="10%")
        assert "w20" in result


def test_process_media_with_flip(tmp_path: Path) -> None:
    """Test process_media with flip option."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        result = process_media(png_path, widths=[20], flip=True)
        assert "w20" in result


def test_process_media_output_py(tmp_path: Path) -> None:
    """Test process_media saves Python output."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        output_dir = tmp_path / "output"
        process_media(png_path, widths=[20], output_dir=output_dir, output_format="py")
        assert (output_dir / "w20_frames.py").exists()
        assert (output_dir / "__init__.py").exists()


def test_process_media_output_js(tmp_path: Path) -> None:
    """Test process_media saves JavaScript output."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        output_dir = tmp_path / "output"
        process_media(png_path, widths=[20], output_dir=output_dir, output_format="js")
        assert (output_dir / "w20_frames.ts").exists()


def test_process_media_output_with_flip(tmp_path: Path) -> None:
    """Test process_media saves output with _right suffix when flipped."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        output_dir = tmp_path / "output"
        process_media(png_path, widths=[20], output_dir=output_dir, flip=True)
        assert (output_dir / "w20_right_frames.py").exists()


def test_process_media_output_with_crop_in_header(tmp_path: Path) -> None:
    """Test process_media includes crop in output header."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        output_dir = tmp_path / "output"
        process_media(png_path, widths=[20], output_dir=output_dir, crop="10%")
        content = (output_dir / "w20_frames.py").read_text()
        assert "crop=10%" in content


def test_process_media_output_js_with_crop(tmp_path: Path) -> None:
    """Test process_media saves JS output with crop in header."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        output_dir = tmp_path / "output"
        process_media(png_path, widths=[20], output_dir=output_dir, output_format="js", crop="10%")
        content = (output_dir / "w20_frames.ts").read_text()
        assert "crop=10%" in content


def test_process_media_output_py_existing_init(tmp_path: Path) -> None:
    """Test process_media doesn't overwrite existing __init__.py."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True)
        init_file = output_dir / "__init__.py"
        init_file.write_text("# Existing init\n")
        process_media(png_path, widths=[20], output_dir=output_dir, output_format="py")
        content = init_file.read_text()
        assert content == "# Existing init\n"


def test_process_media_direct_ts_file(tmp_path: Path) -> None:
    """Test process_media writes directly to .ts file when path ends with .ts."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        output_file = tmp_path / "output" / "w20.ts"
        process_media(png_path, widths=[20], output_dir=output_file, output_format="js")
        assert output_file.exists()
        content = output_file.read_text()
        assert "export const frames" in content


def test_process_media_direct_py_file(tmp_path: Path) -> None:
    """Test process_media writes directly to .py file when path ends with .py."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        output_file = tmp_path / "output" / "w20.py"
        process_media(png_path, widths=[20], output_dir=output_file, output_format="py")
        assert output_file.exists()
        content = output_file.read_text()
        assert "FRAMES = [" in content


def test_process_media_direct_file_multiple_widths_uses_directory(tmp_path: Path) -> None:
    """Test process_media uses directory mode when multiple widths specified."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        # Even though path ends in .ts, multiple widths means it's treated as directory
        output_path = tmp_path / "output.ts"
        process_media(png_path, widths=[20, 30], output_dir=output_path, output_format="js")
        # Should create files inside the directory
        assert (output_path / "w20_frames.ts").exists()
        assert (output_path / "w30_frames.ts").exists()


def test_parse_args_minimal() -> None:
    """Test parse_args with minimal arguments."""
    result = parse_args(["test.gif"])
    assert result.input_path == "test.gif"
    assert result.widths == [58]
    assert result.gradient == "minimalist"


def test_parse_args_all_options() -> None:
    """Test parse_args with all options."""
    result = parse_args(
        [
            "test.mp4",
            "--widths",
            "30,50,80",
            "--frames",
            "5",
            "--gradient",
            "standard",
            "--brightness",
            "1.5",
            "--contrast",
            "2.5",
            "--flip",
            "--invert",
            "--crop",
            "10%",
            "--format",
            "js",
            "--output",
            "out",
            "--preview",
        ]
    )
    assert result.input_path == "test.mp4"
    assert result.widths == [30, 50, 80]
    assert result.num_frames == 5
    assert result.gradient == "standard"
    assert result.brightness == 1.5
    assert result.contrast == 2.5
    assert result.flip is True
    assert result.invert is True
    assert result.crop == "10%"
    assert result.output_format == "js"
    assert result.output_dir == "out"
    assert result.preview is True


def test_main_basic(tmp_path: Path) -> None:
    """Test main function with basic arguments."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        result = main([str(png_path)])
        assert result == 0


def test_main_with_preview(tmp_path: Path) -> None:
    """Test main function with preview option."""
    test_image = create_test_image()
    with fake_hooks_context() as fakes:
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        result = main([str(png_path), "--preview"])
        assert result == 0
        # Check that preview message was printed
        preview_messages = [m for m in fakes.messages if "Preview" in m]
        assert len(preview_messages) > 0


def test_main_with_output(tmp_path: Path) -> None:
    """Test main function with output option."""
    test_image = create_test_image()
    with fake_hooks_context():
        png_path = tmp_path / "test.png"
        test_image.save(png_path)
        output_dir = tmp_path / "output"
        result = main([str(png_path), "--output", str(output_dir)])
        assert result == 0
        assert output_dir.exists()
