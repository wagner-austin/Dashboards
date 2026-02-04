"""Tests for scripts/generate_sprites module."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from scripts import _test_hooks as hooks
from scripts.generate_sprites import (
    _extract_animation_params,
    _parse_sprite_filename,
    _process_animated_sprite,
    _process_animation,
    _process_static_sprite,
    generate_index_files,
    generate_sprite_module,
    load_config,
    main,
    process_sprite,
)


class FakeHooks:
    """Fake hooks for testing without real subprocess calls."""

    def __init__(self) -> None:
        self.messages: list[str] = []
        self.exit_codes: list[int] = []
        self.commands: list[list[str]] = []
        self.return_code: int = 0
        self.stderr: str = ""

    def print_message(self, msg: str) -> None:
        self.messages.append(msg)

    def exit_process(self, code: int) -> None:
        self.exit_codes.append(code)

    def run_command(self, cmd: list[str]) -> subprocess.CompletedProcess[str]:
        self.commands.append(cmd)
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=self.return_code,
            stdout="",
            stderr=self.stderr,
        )


@contextmanager
def fake_hooks_context() -> Iterator[FakeHooks]:
    """Context manager to set up and tear down fake hooks."""
    fakes = FakeHooks()
    original_print = hooks.print_message
    original_exit = hooks.exit_process
    original_run = hooks.run_command

    hooks.print_message = fakes.print_message
    hooks.exit_process = fakes.exit_process
    hooks.run_command = fakes.run_command

    yield fakes

    hooks.print_message = original_print
    hooks.exit_process = original_exit
    hooks.run_command = original_run


def test_load_config_success(tmp_path: Path) -> None:
    """Test load_config successfully loads config.json."""
    config_data = {"sprites": {"bunny": {"source": "test.gif"}}}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    with fake_hooks_context():
        result = load_config(tmp_path)

    assert result == config_data


def test_load_config_not_found(tmp_path: Path) -> None:
    """Test load_config exits when config.json not found."""
    with fake_hooks_context() as fakes, pytest.raises(SystemExit):
        load_config(tmp_path)

    assert fakes.exit_codes == [1]
    assert "config.json not found" in fakes.messages[0]


def test_load_config_default_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test load_config uses current directory when base is None."""
    # Create config.json in tmp_path
    config_data: dict[str, object] = {"sprites": {"test": {}}}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    # Change to tmp_path so load_config finds config.json
    monkeypatch.chdir(tmp_path)

    with fake_hooks_context():
        result = load_config()  # No base argument, uses default

    assert result == config_data


def test_generate_sprite_module_success(tmp_path: Path) -> None:
    """Test generate_sprite_module runs command successfully."""
    output_path = tmp_path / "sprites" / "bunny" / "w50.js"

    with fake_hooks_context() as fakes:
        generate_sprite_module(
            source="test.gif",
            output_path=output_path,
            width=50,
            contrast=1.5,
            invert=False,
        )

    assert len(fakes.commands) == 1
    cmd = fakes.commands[0]
    assert "test.gif" in cmd
    assert "--width" in cmd
    assert "50" in cmd
    assert "--contrast" in cmd
    assert "1.5" in cmd
    assert "--invert" not in cmd
    assert "--crop" not in cmd


def test_generate_sprite_module_with_invert(tmp_path: Path) -> None:
    """Test generate_sprite_module adds --invert flag."""
    output_path = tmp_path / "sprites" / "bunny" / "w50.js"

    with fake_hooks_context() as fakes:
        generate_sprite_module(
            source="test.gif",
            output_path=output_path,
            width=50,
            contrast=1.5,
            invert=True,
        )

    cmd = fakes.commands[0]
    assert "--invert" in cmd


def test_generate_sprite_module_with_crop(tmp_path: Path) -> None:
    """Test generate_sprite_module adds --crop option."""
    output_path = tmp_path / "sprites" / "bunny" / "w50.js"

    with fake_hooks_context() as fakes:
        generate_sprite_module(
            source="test.gif",
            output_path=output_path,
            width=50,
            contrast=1.5,
            invert=False,
            crop="10%",
        )

    cmd = fakes.commands[0]
    assert "--crop" in cmd
    assert "10%" in cmd


def test_generate_sprite_module_with_flip(tmp_path: Path) -> None:
    """Test generate_sprite_module adds --flip flag."""
    output_path = tmp_path / "sprites" / "bunny" / "w50.js"

    with fake_hooks_context() as fakes:
        generate_sprite_module(
            source="test.gif",
            output_path=output_path,
            width=50,
            contrast=1.5,
            invert=False,
            flip=True,
        )

    cmd = fakes.commands[0]
    assert "--flip" in cmd


def test_generate_sprite_module_error(tmp_path: Path) -> None:
    """Test generate_sprite_module exits on command error."""
    output_path = tmp_path / "sprites" / "bunny" / "w50.js"

    with fake_hooks_context() as fakes:
        fakes.return_code = 1
        fakes.stderr = "Command failed"
        generate_sprite_module(
            source="test.gif",
            output_path=output_path,
            width=50,
            contrast=1.5,
            invert=False,
        )

    assert fakes.exit_codes == [1]
    error_msgs = [m for m in fakes.messages if "Error" in m]
    assert len(error_msgs) > 0


def test_generate_sprite_module_creates_parent_dirs(tmp_path: Path) -> None:
    """Test generate_sprite_module creates parent directories."""
    output_path = tmp_path / "deep" / "nested" / "path" / "w50.js"

    with fake_hooks_context():
        generate_sprite_module(
            source="test.gif",
            output_path=output_path,
            width=50,
            contrast=1.5,
            invert=False,
        )

    assert output_path.parent.exists()


def test_parse_sprite_filename_no_direction() -> None:
    """Test _parse_sprite_filename with no direction suffix."""
    width, direction = _parse_sprite_filename("w50")
    assert width == "50"
    assert direction is None


def test_parse_sprite_filename_left() -> None:
    """Test _parse_sprite_filename with left direction."""
    width, direction = _parse_sprite_filename("w50_left")
    assert width == "50"
    assert direction == "left"


def test_parse_sprite_filename_right() -> None:
    """Test _parse_sprite_filename with right direction."""
    width, direction = _parse_sprite_filename("w50_right")
    assert width == "50"
    assert direction == "right"


def test_extract_animation_params_valid() -> None:
    """Test _extract_animation_params with valid config."""
    config: dict[str, object] = {
        "source": "test.gif",
        "widths": [30, 50, 80],
        "contrast": 2.0,
        "invert": True,
        "crop": "10%",
        "directions": ["left", "right"],
    }

    result = _extract_animation_params(config)

    assert result is not None
    source, widths, contrast, invert, crop, directions, trim_rows = result
    assert source == "test.gif"
    assert widths == [30, 50, 80]
    assert contrast == 2.0
    assert invert is True
    assert crop == "10%"
    assert directions == ["left", "right"]
    assert trim_rows == 0


def test_extract_animation_params_missing_source() -> None:
    """Test _extract_animation_params returns None for missing source."""
    config: dict[str, object] = {
        "widths": [30, 50],
    }

    result = _extract_animation_params(config)

    assert result is None


def test_extract_animation_params_missing_widths() -> None:
    """Test _extract_animation_params returns None for missing widths."""
    config: dict[str, object] = {
        "source": "test.gif",
    }

    result = _extract_animation_params(config)

    assert result is None


def test_extract_animation_params_invalid_contrast() -> None:
    """Test _extract_animation_params defaults invalid contrast."""
    config: dict[str, object] = {
        "source": "test.gif",
        "widths": [30],
        "contrast": "invalid",
    }

    result = _extract_animation_params(config)

    assert result is not None
    _, _, contrast, _, _, _, _ = result
    assert contrast == 1.5


def test_extract_animation_params_invalid_invert() -> None:
    """Test _extract_animation_params defaults invalid invert."""
    config: dict[str, object] = {
        "source": "test.gif",
        "widths": [30],
        "invert": "invalid",
    }

    result = _extract_animation_params(config)

    assert result is not None
    _, _, _, invert, _, _, _ = result
    assert invert is False


def test_extract_animation_params_invalid_crop() -> None:
    """Test _extract_animation_params clears invalid crop."""
    config: dict[str, object] = {
        "source": "test.gif",
        "widths": [30],
        "crop": 123,
    }

    result = _extract_animation_params(config)

    assert result is not None
    _, _, _, _, crop, _, _ = result
    assert crop is None


def test_extract_animation_params_int_source() -> None:
    """Test _extract_animation_params returns None for non-string source."""
    config: dict[str, object] = {
        "source": 123,
        "widths": [30],
    }

    result = _extract_animation_params(config)

    assert result is None


def test_extract_animation_params_non_list_widths() -> None:
    """Test _extract_animation_params returns None for non-list widths."""
    config: dict[str, object] = {
        "source": "test.gif",
        "widths": "30,50",
    }

    result = _extract_animation_params(config)

    assert result is None


def test_extract_animation_params_int_contrast() -> None:
    """Test _extract_animation_params accepts int contrast."""
    config: dict[str, object] = {
        "source": "test.gif",
        "widths": [30],
        "contrast": 2,
    }

    result = _extract_animation_params(config)

    assert result is not None
    _, _, contrast, _, _, _, _ = result
    assert contrast == 2.0


def test_extract_animation_params_defaults() -> None:
    """Test _extract_animation_params applies defaults for optional fields."""
    config: dict[str, object] = {
        "source": "test.gif",
        "widths": [30],
    }

    result = _extract_animation_params(config)

    assert result is not None
    _, _, contrast, invert, crop, directions, trim_rows = result
    assert contrast == 1.5
    assert invert is False
    assert crop is None
    assert directions == ["left"]  # Default direction
    assert trim_rows == 0


def test_extract_animation_params_invalid_directions() -> None:
    """Test _extract_animation_params defaults invalid directions."""
    config: dict[str, object] = {
        "source": "test.gif",
        "widths": [30],
        "directions": "invalid",
    }

    result = _extract_animation_params(config)

    assert result is not None
    _, _, _, _, _, directions, _ = result
    assert directions == ["left"]


def test_extract_animation_params_invalid_direction_items() -> None:
    """Test _extract_animation_params filters invalid direction items."""
    config: dict[str, object] = {
        "source": "test.gif",
        "widths": [30],
        "directions": [123, "left", None],
    }

    result = _extract_animation_params(config)

    assert result is not None
    _, _, _, _, _, directions, _ = result
    assert directions == ["left"]


def test_extract_animation_params_empty_directions() -> None:
    """Test _extract_animation_params defaults empty directions list."""
    config: dict[str, object] = {
        "source": "test.gif",
        "widths": [30],
        "directions": [],
    }

    result = _extract_animation_params(config)

    assert result is not None
    _, _, _, _, _, directions, _ = result
    assert directions == ["left"]


def test_extract_animation_params_invalid_trim_rows() -> None:
    """Test _extract_animation_params defaults invalid trim_rows."""
    config: dict[str, object] = {
        "source": "test.gif",
        "widths": [30],
        "trim_rows": "invalid",
    }

    result = _extract_animation_params(config)

    assert result is not None
    _, _, _, _, _, _, trim_rows = result
    assert trim_rows == 0


def test_extract_animation_params_with_trim_rows() -> None:
    """Test _extract_animation_params parses trim_rows correctly."""
    config: dict[str, object] = {
        "source": "test.gif",
        "widths": [30],
        "trim_rows": 5,
    }

    result = _extract_animation_params(config)

    assert result is not None
    _, _, _, _, _, _, trim_rows = result
    assert trim_rows == 5


def test_process_animation_with_trim_rows(tmp_path: Path) -> None:
    """Test _process_animation passes trim_rows to gif_to_ascii."""
    widths: list[int] = [30]

    with fake_hooks_context() as fakes:
        _process_animation(
            sprite_name="bunny",
            anim_name="walk",
            source="test.gif",
            widths=widths,
            contrast=1.5,
            invert=False,
            crop=None,
            directions=["left"],
            trim_rows=3,
            base=tmp_path,
        )

    assert len(fakes.commands) == 1
    cmd = fakes.commands[0]
    # Check trim-rows flag is present
    assert "--trim-rows" in cmd
    trim_idx = cmd.index("--trim-rows") + 1
    assert cmd[trim_idx] == "3"


def test_process_animation_valid_widths(tmp_path: Path) -> None:
    """Test _process_animation processes valid widths."""
    widths: list[int] = [30, 50]

    with fake_hooks_context() as fakes:
        _process_animation(
            sprite_name="bunny",
            anim_name="walk",
            source="test.gif",
            widths=widths,
            contrast=1.5,
            invert=False,
            crop=None,
            directions=["left"],
            base=tmp_path,
        )

    assert len(fakes.commands) == 2


def test_process_animation_invalid_widths_via_animated_sprite(tmp_path: Path) -> None:
    """Test _process_animation skips non-int widths via config path."""
    # Test through _process_animated_sprite which passes config values
    # Config values come as object types from JSON, so mixed types are valid
    animations: dict[str, object] = {
        "walk": {
            "source": "test.gif",
            "widths": [30, "invalid", 50],  # Mixed types from JSON
            "contrast": 1.5,
            "invert": False,
        },
    }

    with fake_hooks_context() as fakes:
        _process_animated_sprite("bunny", animations, tmp_path)

    # Only valid int widths (30, 50) should be processed
    assert len(fakes.commands) == 2


def test_process_animation_default_base(tmp_path: Path) -> None:
    """Test _process_animation uses default base path."""
    widths: list[int] = [30]

    with fake_hooks_context() as fakes:
        _process_animation(
            sprite_name="bunny",
            anim_name="walk",
            source="test.gif",
            widths=widths,
            contrast=1.5,
            invert=False,
            crop=None,
            directions=["left"],
        )

    assert len(fakes.commands) == 1
    cmd = fakes.commands[0]
    output_idx = cmd.index("--output") + 1
    # Check path components work on both Windows and Unix
    output_path = cmd[output_idx]
    assert "bunny" in output_path
    assert "walk" in output_path
    assert "w30.ts" in output_path


def test_process_animation_multiple_directions(tmp_path: Path) -> None:
    """Test _process_animation generates both left and right variants."""
    widths: list[int] = [30]

    with fake_hooks_context() as fakes:
        _process_animation(
            sprite_name="bunny",
            anim_name="walk",
            source="test.gif",
            widths=widths,
            contrast=1.5,
            invert=False,
            crop=None,
            directions=["left", "right"],
            base=tmp_path,
        )

    # Should generate 2 files: w30_left.ts and w30_right.ts
    assert len(fakes.commands) == 2

    # Check left variant (no flip)
    left_cmd = fakes.commands[0]
    assert "--flip" not in left_cmd
    left_output = left_cmd[left_cmd.index("--output") + 1]
    assert "w30_left.ts" in left_output

    # Check right variant (with flip)
    right_cmd = fakes.commands[1]
    assert "--flip" in right_cmd
    right_output = right_cmd[right_cmd.index("--output") + 1]
    assert "w30_right.ts" in right_output


def test_process_animated_sprite_valid(tmp_path: Path) -> None:
    """Test _process_animated_sprite processes valid animations."""
    animations: dict[str, object] = {
        "walk": {
            "source": "walk.gif",
            "widths": [30],
            "contrast": 1.5,
            "invert": False,
        },
        "jump": {
            "source": "jump.gif",
            "widths": [30],
            "contrast": 2.0,
            "invert": True,
        },
    }

    with fake_hooks_context() as fakes:
        _process_animated_sprite("bunny", animations, tmp_path)

    assert len(fakes.commands) == 2


def test_process_animated_sprite_invalid_config(tmp_path: Path) -> None:
    """Test _process_animated_sprite skips non-dict config."""
    animations: dict[str, object] = {
        "walk": "invalid",
        "jump": {
            "source": "jump.gif",
            "widths": [30],
        },
    }

    with fake_hooks_context() as fakes:
        _process_animated_sprite("bunny", animations, tmp_path)

    assert len(fakes.commands) == 1


def test_process_animated_sprite_invalid_params(tmp_path: Path) -> None:
    """Test _process_animated_sprite skips animation with None params."""
    animations: dict[str, object] = {
        "walk": {
            "widths": [30],
        },
    }

    with fake_hooks_context() as fakes:
        _process_animated_sprite("bunny", animations, tmp_path)

    assert len(fakes.commands) == 0


def test_process_static_sprite_valid(tmp_path: Path) -> None:
    """Test _process_static_sprite processes valid config."""
    config: dict[str, object] = {
        "source": "tree.gif",
        "widths": [60, 120],
        "contrast": 1.5,
        "invert": True,
    }

    with fake_hooks_context() as fakes:
        _process_static_sprite("tree", config, tmp_path)

    assert len(fakes.commands) == 2


def test_process_static_sprite_missing_source(tmp_path: Path) -> None:
    """Test _process_static_sprite returns early for missing source."""
    config: dict[str, object] = {
        "widths": [60],
    }

    with fake_hooks_context() as fakes:
        _process_static_sprite("tree", config, tmp_path)

    assert len(fakes.commands) == 0


def test_process_static_sprite_missing_widths(tmp_path: Path) -> None:
    """Test _process_static_sprite returns early for missing widths."""
    config: dict[str, object] = {
        "source": "tree.gif",
    }

    with fake_hooks_context() as fakes:
        _process_static_sprite("tree", config, tmp_path)

    assert len(fakes.commands) == 0


def test_process_static_sprite_invalid_source(tmp_path: Path) -> None:
    """Test _process_static_sprite returns early for non-string source."""
    config: dict[str, object] = {
        "source": 123,
        "widths": [60],
    }

    with fake_hooks_context() as fakes:
        _process_static_sprite("tree", config, tmp_path)

    assert len(fakes.commands) == 0


def test_process_static_sprite_invalid_widths(tmp_path: Path) -> None:
    """Test _process_static_sprite returns early for non-list widths."""
    config: dict[str, object] = {
        "source": "tree.gif",
        "widths": "60,120",
    }

    with fake_hooks_context() as fakes:
        _process_static_sprite("tree", config, tmp_path)

    assert len(fakes.commands) == 0


def test_process_static_sprite_invalid_contrast(tmp_path: Path) -> None:
    """Test _process_static_sprite defaults invalid contrast."""
    config: dict[str, object] = {
        "source": "tree.gif",
        "widths": [60],
        "contrast": "invalid",
    }

    with fake_hooks_context() as fakes:
        _process_static_sprite("tree", config, tmp_path)

    assert len(fakes.commands) == 1
    cmd = fakes.commands[0]
    contrast_idx = cmd.index("--contrast") + 1
    assert cmd[contrast_idx] == "1.5"


def test_process_static_sprite_invalid_invert(tmp_path: Path) -> None:
    """Test _process_static_sprite defaults invalid invert."""
    config: dict[str, object] = {
        "source": "tree.gif",
        "widths": [60],
        "invert": "invalid",
    }

    with fake_hooks_context() as fakes:
        _process_static_sprite("tree", config, tmp_path)

    assert len(fakes.commands) == 1
    cmd = fakes.commands[0]
    assert "--invert" not in cmd


def test_process_static_sprite_invalid_width_in_list(tmp_path: Path) -> None:
    """Test _process_static_sprite skips non-int widths."""
    config: dict[str, object] = {
        "source": "tree.gif",
        "widths": [60, "invalid", 120],
        "contrast": 1.5,
        "invert": False,
    }

    with fake_hooks_context() as fakes:
        _process_static_sprite("tree", config, tmp_path)

    assert len(fakes.commands) == 2


def test_process_static_sprite_default_base() -> None:
    """Test _process_static_sprite uses default base path."""
    config: dict[str, object] = {
        "source": "tree.gif",
        "widths": [60],
    }

    with fake_hooks_context() as fakes:
        _process_static_sprite("tree", config)

    assert len(fakes.commands) == 1
    cmd = fakes.commands[0]
    output_idx = cmd.index("--output") + 1
    # Check path components work on both Windows and Unix
    output_path = cmd[output_idx]
    assert "tree" in output_path
    assert "w60.ts" in output_path


def test_process_static_sprite_int_contrast(tmp_path: Path) -> None:
    """Test _process_static_sprite accepts int contrast."""
    config: dict[str, object] = {
        "source": "tree.gif",
        "widths": [60],
        "contrast": 2,
    }

    with fake_hooks_context() as fakes:
        _process_static_sprite("tree", config, tmp_path)

    assert len(fakes.commands) == 1
    cmd = fakes.commands[0]
    contrast_idx = cmd.index("--contrast") + 1
    assert cmd[contrast_idx] == "2.0"


def test_process_sprite_with_animations(tmp_path: Path) -> None:
    """Test process_sprite dispatches to animated sprite handler."""
    config: dict[str, object] = {
        "animations": {
            "walk": {
                "source": "walk.gif",
                "widths": [30],
            }
        }
    }

    with fake_hooks_context() as fakes:
        process_sprite("bunny", config, tmp_path)

    assert len(fakes.commands) == 1


def test_process_sprite_without_animations(tmp_path: Path) -> None:
    """Test process_sprite dispatches to static sprite handler."""
    config: dict[str, object] = {
        "source": "tree.gif",
        "widths": [60],
    }

    with fake_hooks_context() as fakes:
        process_sprite("tree", config, tmp_path)

    assert len(fakes.commands) == 1


def test_process_sprite_invalid_animations(tmp_path: Path) -> None:
    """Test process_sprite treats non-dict animations as static."""
    config: dict[str, object] = {
        "animations": "invalid",
        "source": "tree.gif",
        "widths": [60],
    }

    with fake_hooks_context() as fakes:
        process_sprite("tree", config, tmp_path)

    assert len(fakes.commands) == 1


def test_process_sprite_none_animations(tmp_path: Path) -> None:
    """Test process_sprite treats None animations as static."""
    config: dict[str, object] = {
        "animations": None,
        "source": "tree.gif",
        "widths": [60],
    }

    with fake_hooks_context() as fakes:
        process_sprite("tree", config, tmp_path)

    assert len(fakes.commands) == 1


def test_generate_index_files_with_subdirs(tmp_path: Path) -> None:
    """Test generate_index_files creates index.ts for sprites with subdirs."""
    sprites_dir = tmp_path / "src" / "sprites" / "bunny"
    walk_dir = sprites_dir / "walk"
    walk_dir.mkdir(parents=True)
    (walk_dir / "w30.ts").write_text("export const frames = [];", encoding="utf-8")
    (walk_dir / "w50.ts").write_text("export const frames = [];", encoding="utf-8")

    jump_dir = sprites_dir / "jump"
    jump_dir.mkdir(parents=True)
    (jump_dir / "w30.ts").write_text("export const frames = [];", encoding="utf-8")

    with fake_hooks_context() as fakes:
        generate_index_files(tmp_path)

    index_path = sprites_dir / "index.ts"
    assert index_path.exists()
    content = index_path.read_text(encoding="utf-8")
    assert "walkW30" in content
    assert "walkW50" in content
    assert "jumpW30" in content
    # Imports use .js extension for runtime (TypeScript convention)
    assert "./walk/w30.js" in content
    generated_msgs = [m for m in fakes.messages if "Generated" in m]
    assert len(generated_msgs) == 1


def test_generate_index_files_static_sprite(tmp_path: Path) -> None:
    """Test generate_index_files creates index.ts for static sprites with direct TS files."""
    sprites_dir = tmp_path / "src" / "sprites" / "tree"
    sprites_dir.mkdir(parents=True)
    (sprites_dir / "w60.ts").write_text("export const frames = [];", encoding="utf-8")
    (sprites_dir / "w120.ts").write_text("export const frames = [];", encoding="utf-8")

    with fake_hooks_context():
        generate_index_files(tmp_path)

    index_path = sprites_dir / "index.ts"
    assert index_path.exists()
    content = index_path.read_text(encoding="utf-8")
    assert "w120" in content
    assert "w60" in content
    # Imports use .js extension for runtime (TypeScript convention)
    assert "./w60.js" in content
    assert "./w120.js" in content


def test_generate_index_files_with_directions(tmp_path: Path) -> None:
    """Test generate_index_files handles directional sprite files."""
    sprites_dir = tmp_path / "src" / "sprites" / "bunny"
    walk_dir = sprites_dir / "walk"
    walk_dir.mkdir(parents=True)
    (walk_dir / "w30_left.ts").write_text("export const frames = [];", encoding="utf-8")
    (walk_dir / "w30_right.ts").write_text("export const frames = [];", encoding="utf-8")

    with fake_hooks_context():
        generate_index_files(tmp_path)

    index_path = sprites_dir / "index.ts"
    assert index_path.exists()
    content = index_path.read_text(encoding="utf-8")
    # Check variable names include direction suffix
    assert "walkW30Left" in content
    assert "walkW30Right" in content
    # Check imports
    assert "./walk/w30_left.js" in content
    assert "./walk/w30_right.js" in content


def test_generate_index_files_empty_sprite_dir(tmp_path: Path) -> None:
    """Test generate_index_files skips sprite dirs with no TS files."""
    sprites_dir = tmp_path / "src" / "sprites" / "empty"
    sprites_dir.mkdir(parents=True)
    # No JS files, just an empty directory

    with fake_hooks_context():
        generate_index_files(tmp_path)

    index_path = sprites_dir / "index.ts"
    assert not index_path.exists()


def test_generate_index_files_nonexistent_dir(tmp_path: Path) -> None:
    """Test generate_index_files handles nonexistent sprites directory."""
    with fake_hooks_context() as fakes:
        generate_index_files(tmp_path)

    assert len(fakes.messages) == 0


def test_generate_index_files_skips_files(tmp_path: Path) -> None:
    """Test generate_index_files skips non-directory items."""
    sprites_dir = tmp_path / "src" / "sprites"
    sprites_dir.mkdir(parents=True)
    (sprites_dir / "README.md").write_text("# Sprites", encoding="utf-8")

    with fake_hooks_context() as fakes:
        generate_index_files(tmp_path)

    assert len(fakes.messages) == 0


def test_generate_index_files_default_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test generate_index_files uses default base path."""
    # Change to a temp directory to avoid finding real files
    monkeypatch.chdir(tmp_path)

    with fake_hooks_context() as fakes:
        generate_index_files()

    # Should not crash, just return early if no sprites dir
    assert len(fakes.messages) == 0


def test_main_success(tmp_path: Path) -> None:
    """Test main function succeeds with valid config."""
    config = {
        "sprites": {
            "bunny": {
                "source": "bunny.gif",
                "widths": [30],
            }
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    with fake_hooks_context() as fakes:
        result = main(tmp_path)

    assert result == 0
    complete_msgs = [m for m in fakes.messages if "complete" in m]
    assert len(complete_msgs) == 1


def test_main_missing_sprites(tmp_path: Path) -> None:
    """Test main returns 1 when sprites key missing."""
    config: dict[str, object] = {"settings": {}}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    with fake_hooks_context() as fakes:
        result = main(tmp_path)

    assert result == 1
    error_msgs = [m for m in fakes.messages if "sprites" in m and "not found" in m]
    assert len(error_msgs) == 1


def test_main_invalid_sprites(tmp_path: Path) -> None:
    """Test main returns 1 when sprites is not a dict."""
    config: dict[str, object] = {"sprites": "invalid"}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    with fake_hooks_context():
        result = main(tmp_path)

    assert result == 1


def test_main_skips_non_dict_sprite(tmp_path: Path) -> None:
    """Test main skips sprite configs that are not dicts."""
    config: dict[str, object] = {
        "sprites": {
            "bunny": "invalid",
            "tree": {
                "source": "tree.gif",
                "widths": [60],
            },
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    with fake_hooks_context() as fakes:
        result = main(tmp_path)

    assert result == 0
    assert len(fakes.commands) == 1


def test_main_with_animated_sprites(tmp_path: Path) -> None:
    """Test main processes animated sprites correctly."""
    config = {
        "sprites": {
            "bunny": {
                "animations": {
                    "walk": {
                        "source": "walk.gif",
                        "widths": [30, 50],
                    }
                }
            }
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    with fake_hooks_context() as fakes:
        result = main(tmp_path)

    assert result == 0
    assert len(fakes.commands) == 2
