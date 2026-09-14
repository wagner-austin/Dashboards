"""Exercise registration and explicit layout failures using real image files."""

from pathlib import Path

import pytest
from PIL import Image
from scripts.slice_sheet import slice_sheet


def test_registers_shared_canvas_without_stretching(tmp_path: Path) -> None:
    sheet = Image.new("RGB", (40, 20), "white")
    sheet.paste("blue", (2, 6, 12, 16))
    sheet.paste("blue", (22, 2, 32, 17))
    source = tmp_path / "sheet.png"
    sheet.save(source)
    paths = slice_sheet(source, ((0, 0, 20, 20), (20, 0, 40, 20)), tmp_path / "out", (0, 3), "0.08")
    assert tuple(path.name for path in paths) == (
        "frame_0_delay-0.08s.png",
        "frame_1_delay-0.08s.png",
    )
    first = Image.open(paths[0])
    second = Image.open(paths[1])
    assert first.size == second.size == (42, 50)
    assert first.getpixel((16, 33)) == (0, 0, 255)
    assert first.getpixel((16, 34)) == (255, 255, 255)
    assert second.getpixel((16, 30)) == (0, 0, 255)
    assert second.getpixel((16, 31)) == (255, 255, 255)


def test_rejects_layout_mismatch(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="SPRITE_LAYOUT"):
        slice_sheet(tmp_path / "missing", (), tmp_path, (), "0.1")
    with pytest.raises(ValueError, match="SPRITE_LAYOUT"):
        slice_sheet(tmp_path / "missing", ((0, 0, 1, 1),), tmp_path, (), "0.1")


def test_rejects_empty_or_invalid_cells(tmp_path: Path) -> None:
    source = tmp_path / "empty.png"
    Image.new("RGB", (20, 20), "white").save(source)
    with pytest.raises(ValueError, match="SPRITE_CELL"):
        slice_sheet(source, ((0, 0, 20, 20),), tmp_path, (0,), "0.1")
    with pytest.raises(ValueError, match="SPRITE_BOUNDS"):
        slice_sheet(source, ((0, 0, 21, 20),), tmp_path, (0,), "0.1")
    with pytest.raises(ValueError, match="SPRITE_BOUNDS"):
        slice_sheet(source, ((0, 0, 20, 20),), tmp_path, (-1,), "0.1")
