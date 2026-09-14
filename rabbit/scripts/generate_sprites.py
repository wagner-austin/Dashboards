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
    brightness: float = 1.0,
    gradient: str = "minimalist",
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
        "--gradient",
        gradient,
    ]

    if invert:
        cmd.append("--invert")

    if flip:
        cmd.append("--flip")

    if crop is not None:
        cmd.extend(["--crop", crop])

    if trim_rows > 0:
        cmd.extend(["--trim-rows", str(trim_rows)])

    if brightness != 1.0:
        cmd.extend(["--brightness", str(brightness)])

    hooks.print_message(f"Generating {output_path}...")
    result = hooks.run_command(cmd)

    if result.returncode != 0:
        hooks.print_message(f"Error generating {output_path}:")
        hooks.print_message(result.stderr)
        hooks.exit_process(1)


def _coerce_float(value: object, default: float) -> float:
    """Coerce a value to float, returning default if not numeric."""
    return float(value) if isinstance(value, int | float) else default


def _coerce_bool(value: object, default: bool) -> bool:
    """Coerce a value to bool, returning default if not boolean."""
    return value if isinstance(value, bool) else default


def _coerce_str(value: object, default: str) -> str:
    """Coerce a value to str, returning default if not string."""
    return value if isinstance(value, str) else default


def _coerce_optional_str(value: object) -> str | None:
    """Coerce a value to optional str."""
    return value if isinstance(value, str) else None


def _coerce_int(value: object, default: int) -> int:
    """Coerce a value to int, returning default if not int."""
    return value if isinstance(value, int) else default


def _coerce_directions(value: object) -> list[str]:
    """Coerce a value to list of direction strings."""
    if not isinstance(value, list):
        return ["left"]
    valid = [d for d in value if isinstance(d, str)]
    return valid if valid else ["left"]


def _extract_animation_params(
    anim_config: dict[str, object],
) -> tuple[str, list[int], float, bool, str | None, list[str], int, float, str] | None:
    """Extract and validate animation parameters from config."""
    source = anim_config.get("source")
    widths = anim_config.get("widths")
    if not isinstance(source, str) or not isinstance(widths, list):
        return None

    return (
        source,
        widths,
        _coerce_float(anim_config.get("contrast", 1.5), 1.5),
        _coerce_bool(anim_config.get("invert", False), False),
        _coerce_optional_str(anim_config.get("crop")),
        _coerce_directions(anim_config.get("directions", ["left"])),
        _coerce_int(anim_config.get("trim_rows", 0), 0),
        _coerce_float(anim_config.get("brightness", 1.0), 1.0),
        _coerce_str(anim_config.get("gradient", "minimalist"), "minimalist"),
    )


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
    brightness: float = 1.0,
    gradient: str = "minimalist",
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
            generate_sprite_module(
                source,
                output_path,
                w,
                contrast,
                invert,
                crop,
                flip,
                trim_rows,
                brightness,
                gradient,
            )


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

        source, widths, contrast, invert, crop, directions, trim_rows, brightness, gradient = params
        _process_animation(
            name,
            anim_name,
            source,
            widths,
            contrast,
            invert,
            crop,
            directions,
            trim_rows,
            base,
            brightness,
            gradient,
        )


def _process_static_sprite(
    name: str, sprite_config: dict[str, object], base: Path | None = None
) -> None:
    """Process a static sprite without animations."""
    if base is None:
        base = Path(".")

    source = sprite_config.get("source")
    widths = sprite_config.get("widths")
    if not isinstance(source, str) or not isinstance(widths, list):
        return

    contrast = _coerce_float(sprite_config.get("contrast", 1.5), 1.5)
    invert = _coerce_bool(sprite_config.get("invert", False), False)
    crop = _coerce_optional_str(sprite_config.get("crop"))
    brightness = _coerce_float(sprite_config.get("brightness", 1.0), 1.0)
    gradient = _coerce_str(sprite_config.get("gradient", "minimalist"), "minimalist")

    for w in widths:
        if not isinstance(w, int):
            continue
        output_path = base / f"src/sprites/{name}/w{w}.ts"
        generate_sprite_module(
            source,
            output_path,
            w,
            contrast,
            invert,
            crop,
            brightness=brightness,
            gradient=gradient,
        )


def process_sprite(name: str, sprite_config: dict[str, object], base: Path | None = None) -> None:
    """Process a single sprite definition."""
    animations = sprite_config.get("animations")

    if animations is not None and isinstance(animations, dict):
        _process_animated_sprite(name, animations, base)
    else:
        _process_static_sprite(name, sprite_config, base)


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

    hooks.print_message("Sprite generation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
