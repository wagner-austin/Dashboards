"""Generate sprite JS modules from config.json.

Reads the sprite configuration and generates JavaScript modules
containing frame data at multiple widths for depth effects.
"""

import json
import sys
from pathlib import Path

from scripts import _test_hooks as hooks


def load_config(base: Path | None = None) -> dict[str, object]:
    """Load and return config.json."""
    if base is None:
        base = Path(".")

    config_path = base / "config.json"
    if not config_path.exists():
        hooks.print_message("Error: config.json not found")
        hooks.exit_process(1)
        raise SystemExit(1)

    with config_path.open(encoding="utf-8") as f:
        result: dict[str, object] = json.load(f)
        return result


def generate_sprite_module(
    source: str,
    output_path: Path,
    width: int,
    contrast: float,
    invert: bool,
    crop: str | None = None,
    flip: bool = False,
    trim_rows: int = 0,
) -> None:
    """Generate a single sprite JS module using gif_to_ascii.py."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "tools/gif_to_ascii.py",
        source,
        "--width",
        str(width),
        "--contrast",
        str(contrast),
        "--output",
        str(output_path),
        "--format",
        "js",
    ]

    if invert:
        cmd.append("--invert")

    if flip:
        cmd.append("--flip")

    if crop is not None:
        cmd.extend(["--crop", crop])

    if trim_rows > 0:
        cmd.extend(["--trim-rows", str(trim_rows)])

    hooks.print_message(f"Generating {output_path}...")
    result = hooks.run_command(cmd)

    if result.returncode != 0:
        hooks.print_message(f"Error generating {output_path}:")
        hooks.print_message(result.stderr)
        hooks.exit_process(1)


def _extract_animation_params(
    anim_config: dict[str, object],
) -> tuple[str, list[int], float, bool, str | None, list[str], int] | None:
    """Extract and validate animation parameters from config."""
    source = anim_config.get("source")
    widths = anim_config.get("widths")
    contrast = anim_config.get("contrast", 1.5)
    invert = anim_config.get("invert", False)
    crop = anim_config.get("crop")
    directions = anim_config.get("directions", ["left"])
    trim_rows = anim_config.get("trim_rows", 0)

    if not isinstance(source, str):
        return None
    if not isinstance(widths, list):
        return None
    if not isinstance(contrast, int | float):
        contrast = 1.5
    if not isinstance(invert, bool):
        invert = False
    if crop is not None and not isinstance(crop, str):
        crop = None
    if not isinstance(directions, list):
        directions = ["left"]
    if not isinstance(trim_rows, int):
        trim_rows = 0

    # Validate directions are strings
    valid_directions = [d for d in directions if isinstance(d, str)]
    if not valid_directions:
        valid_directions = ["left"]

    return source, widths, float(contrast), invert, crop, valid_directions, trim_rows


def _process_animation(
    sprite_name: str,
    anim_name: str,
    source: str,
    widths: list[int],
    contrast: float,
    invert: bool,
    crop: str | None,
    directions: list[str],
    trim_rows: int = 0,
    base: Path | None = None,
) -> None:
    """Process a single animation's width and direction variants."""
    if base is None:
        base = Path(".")

    for w in widths:
        if not isinstance(w, int):
            continue
        for direction in directions:
            # Left-facing is the default (no flip), right-facing needs flip
            flip = direction == "right"
            suffix = f"_{direction}" if len(directions) > 1 else ""
            output_path = base / f"src/sprites/{sprite_name}/{anim_name}/w{w}{suffix}.ts"
            generate_sprite_module(source, output_path, w, contrast, invert, crop, flip, trim_rows)


def _process_animated_sprite(
    name: str, animations: dict[str, object], base: Path | None = None
) -> None:
    """Process a sprite with multiple animations."""
    for anim_name, anim_config in animations.items():
        if not isinstance(anim_config, dict):
            continue

        params = _extract_animation_params(anim_config)
        if params is None:
            continue

        source, widths, contrast, invert, crop, directions, trim_rows = params
        _process_animation(
            name, anim_name, source, widths, contrast, invert, crop, directions, trim_rows, base
        )


def _process_static_sprite(
    name: str, sprite_config: dict[str, object], base: Path | None = None
) -> None:
    """Process a static sprite without animations."""
    if base is None:
        base = Path(".")

    source = sprite_config.get("source")
    widths = sprite_config.get("widths")
    contrast = sprite_config.get("contrast", 1.5)
    invert = sprite_config.get("invert", False)

    if not isinstance(source, str):
        return
    if not isinstance(widths, list):
        return
    if not isinstance(contrast, int | float):
        contrast = 1.5
    if not isinstance(invert, bool):
        invert = False

    for w in widths:
        if not isinstance(w, int):
            continue
        output_path = base / f"src/sprites/{name}/w{w}.ts"
        generate_sprite_module(source, output_path, w, float(contrast), invert)


def process_sprite(name: str, sprite_config: dict[str, object], base: Path | None = None) -> None:
    """Process a single sprite definition."""
    animations = sprite_config.get("animations")

    if animations is not None and isinstance(animations, dict):
        _process_animated_sprite(name, animations, base)
    else:
        _process_static_sprite(name, sprite_config, base)


def _parse_sprite_filename(stem: str) -> tuple[str, str | None]:
    """Parse sprite filename to extract width and optional direction.

    Examples:
        "w50" -> ("50", None)
        "w50_left" -> ("50", "left")
        "w50_right" -> ("50", "right")
    """
    # Check for direction suffix
    for direction in ["_left", "_right"]:
        if stem.endswith(direction):
            width_part = stem[1 : -len(direction)]  # Remove 'w' prefix and direction suffix
            return width_part, direction[1:]  # Remove underscore from direction
    # No direction suffix
    return stem[1:], None  # Remove 'w' prefix


def generate_index_files(base: Path | None = None) -> None:
    """Generate index.ts files for sprite modules."""
    if base is None:
        base = Path(".")

    sprites_dir = base / "src/sprites"
    if not sprites_dir.exists():
        return

    for sprite_dir in sprites_dir.iterdir():
        if not sprite_dir.is_dir():
            continue

        exports: list[str] = []

        # Check for animated sprite (has subdirectories with TS files)
        subdirs = [d for d in sprite_dir.iterdir() if d.is_dir()]
        for subdir in subdirs:
            ts_files = list(subdir.glob("w*.ts"))
            for ts_file in ts_files:
                width, direction = _parse_sprite_filename(ts_file.stem)
                # Import with .js extension (TypeScript ES module convention)
                rel_path = f"./{subdir.name}/{ts_file.stem}.js"
                # Build variable name: walkW50 or walkW50Left
                dir_suffix = direction.capitalize() if direction else ""
                var_name = f"{subdir.name}W{width}{dir_suffix}"
                exports.append(f'export {{ frames as {var_name} }} from "{rel_path}";')

        # Check for static sprite (TS files directly in sprite dir)
        direct_ts_files = list(sprite_dir.glob("w*.ts"))
        for ts_file in direct_ts_files:
            width, direction = _parse_sprite_filename(ts_file.stem)
            # Import with .js extension (TypeScript ES module convention)
            rel_path = f"./{ts_file.stem}.js"
            # Build variable name: w50 or w50Left
            dir_suffix = direction.capitalize() if direction else ""
            var_name = f"w{width}{dir_suffix}"
            exports.append(f'export {{ frames as {var_name} }} from "{rel_path}";')

        if exports:
            index_content = "\n".join(sorted(exports)) + "\n"
            index_path = sprite_dir / "index.ts"
            index_path.write_text(index_content, encoding="utf-8")
            hooks.print_message(f"Generated {index_path}")


def main(base: Path | None = None) -> int:
    """Generate all sprite modules from config."""
    config = load_config(base)
    sprites = config.get("sprites")

    if not isinstance(sprites, dict):
        hooks.print_message("Error: 'sprites' not found in config.json")
        return 1

    for name, sprite_config in sprites.items():
        if isinstance(sprite_config, dict):
            process_sprite(name, sprite_config, base)

    generate_index_files(base)

    hooks.print_message("Sprite generation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
