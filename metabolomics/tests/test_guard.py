"""Tests for the guard module."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from scripts import _test_hooks as hooks
from scripts.guard import (
    _get_forbidden_patterns,
    check_config_valid,
    check_no_type_ignore,
    check_pipeline_modules,
    check_required_files,
    main,
)


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary project directory with minimal valid structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create required files
        (base / "pyproject.toml").write_text("[tool.poetry]\nname = 'test'")
        (base / "Emily_Data_Pruned_Labeled.xlsx").write_bytes(b"fake excel")

        # Create valid config.json
        config: dict[str, object] = {
            "input": {"file": "test.xlsx", "sheet": "Sheet1", "formula_file": ""},
            "output": {"html": "dashboard.html", "intermediate_dir": "intermediate"},
            "samples": {
                "leaf": {"drought": [], "ambient": [], "watered": []},
                "root": {"drought": [], "ambient": [], "watered": []},
            },
            "blanks": {"leaf": [], "root": []},
            "thresholds": {
                "blank_filter": {
                    "fold_change": 20.0,
                    "p_value": 0.05,
                    "fdr_correction": True,
                },
                "cumulative_filter": {"threshold": 0.80},
                "detection": {"min_value": 0.0},
            },
            "references": {
                "blank_subtraction": {"name": "", "url": "", "citation": ""},
                "shannon_diversity": {"name": "", "url": "", "citation": ""},
                "fdr_correction": {"name": "", "url": "", "citation": ""},
            },
        }
        (base / "config.json").write_text(json.dumps(config))

        # Create pipeline directory with modules
        pipeline_dir = base / "scripts" / "pipeline"
        pipeline_dir.mkdir(parents=True)
        for module in [
            "__init__.py",
            "types.py",
            "loader.py",
            "blank_filter.py",
            "cumulative_filter.py",
            "diversity.py",
            "overlap.py",
        ]:
            (pipeline_dir / module).write_text("# placeholder")

        yield base


def test_get_forbidden_patterns_returns_type_ignore_patterns() -> None:
    """Test that forbidden patterns include type: ignore variations."""
    patterns = _get_forbidden_patterns()
    assert len(patterns) == 3
    assert all("type" in p and "ignore" in p for p in patterns)


def test_check_required_files_all_present(temp_project_dir: Path) -> None:
    """Test that no errors when all required files present."""
    errors = check_required_files(temp_project_dir)
    assert errors == []


def test_check_required_files_missing_config(temp_project_dir: Path) -> None:
    """Test error when config.json is missing."""
    (temp_project_dir / "config.json").unlink()
    errors = check_required_files(temp_project_dir)
    assert len(errors) == 1
    assert "config.json" in errors[0]


def test_check_required_files_missing_excel(temp_project_dir: Path) -> None:
    """Test error when Excel file is missing."""
    (temp_project_dir / "Emily_Data_Pruned_Labeled.xlsx").unlink()
    errors = check_required_files(temp_project_dir)
    assert len(errors) == 1
    assert "Emily_Data_Pruned_Labeled.xlsx" in errors[0]


def test_check_config_valid_success(temp_project_dir: Path) -> None:
    """Test no errors with valid config."""
    errors = check_config_valid(temp_project_dir)
    assert errors == []


def test_check_config_valid_missing_file(temp_project_dir: Path) -> None:
    """Test error when config.json doesn't exist."""
    (temp_project_dir / "config.json").unlink()
    errors = check_config_valid(temp_project_dir)
    assert len(errors) == 1
    assert "does not exist" in errors[0]


def test_check_config_valid_invalid_json(temp_project_dir: Path) -> None:
    """Test error with invalid JSON."""
    (temp_project_dir / "config.json").write_text("{invalid json")
    errors = check_config_valid(temp_project_dir)
    assert len(errors) == 1
    assert "invalid JSON" in errors[0]


def test_check_config_valid_missing_section(temp_project_dir: Path) -> None:
    """Test error when required section is missing."""
    (temp_project_dir / "config.json").write_text('{"input": {}}')
    errors = check_config_valid(temp_project_dir)
    # Should have errors for missing output, samples, blanks, thresholds
    assert len(errors) >= 4


def test_check_config_valid_missing_threshold_keys(temp_project_dir: Path) -> None:
    """Test error when threshold keys are missing."""
    config: dict[str, object] = {
        "input": {},
        "output": {},
        "samples": {},
        "blanks": {},
        "thresholds": {
            "blank_filter": {},  # Missing fold_change, p_value, fdr_correction
            "cumulative_filter": {},  # Missing threshold
        },
    }
    (temp_project_dir / "config.json").write_text(json.dumps(config))
    errors = check_config_valid(temp_project_dir)
    assert any("fold_change" in e for e in errors)
    assert any("p_value" in e for e in errors)
    assert any("fdr_correction" in e for e in errors)
    assert any("threshold" in e for e in errors)


def test_check_pipeline_modules_all_present(temp_project_dir: Path) -> None:
    """Test no errors when all pipeline modules present."""
    errors = check_pipeline_modules(temp_project_dir)
    assert errors == []


def test_check_pipeline_modules_missing_module(temp_project_dir: Path) -> None:
    """Test error when a module is missing."""
    (temp_project_dir / "scripts" / "pipeline" / "types.py").unlink()
    errors = check_pipeline_modules(temp_project_dir)
    assert len(errors) == 1
    assert "types.py" in errors[0]


def test_check_no_type_ignore_clean(temp_project_dir: Path) -> None:
    """Test no errors when no type: ignore comments."""
    errors = check_no_type_ignore(temp_project_dir)
    assert errors == []


def test_check_no_type_ignore_found_in_scripts(temp_project_dir: Path) -> None:
    """Test error when type: ignore found in scripts."""
    py_file = temp_project_dir / "scripts" / "pipeline" / "types.py"
    # Build the forbidden pattern dynamically to avoid self-detection
    forbidden = "# " + "type" + ": " + "ignore"
    py_file.write_text(f"x = 1  {forbidden}")
    errors = check_no_type_ignore(temp_project_dir)
    assert len(errors) == 1
    assert "type" in errors[0] and "ignore" in errors[0]


def test_check_no_type_ignore_found_in_tests(temp_project_dir: Path) -> None:
    """Test error when type: ignore found in tests."""
    tests_dir = temp_project_dir / "tests"
    tests_dir.mkdir()
    # Build the forbidden pattern dynamically to avoid self-detection
    forbidden = "#" + "type" + ":" + "ignore"
    (tests_dir / "test_foo.py").write_text(f"y = 2  {forbidden}")
    errors = check_no_type_ignore(temp_project_dir)
    assert len(errors) == 1


def test_main_success(temp_project_dir: Path) -> None:
    """Test main returns 0 when all checks pass."""
    messages: list[str] = []
    hooks.print_message = lambda msg: messages.append(msg)

    result = main(temp_project_dir)

    assert result == 0
    assert any("passed" in m for m in messages)
    hooks.reset_hooks()


def test_main_failure(temp_project_dir: Path) -> None:
    """Test main returns 1 when checks fail."""
    (temp_project_dir / "config.json").unlink()
    messages: list[str] = []
    hooks.print_message = lambda msg: messages.append(msg)

    result = main(temp_project_dir)

    assert result == 1
    assert any("FAILED" in m for m in messages)
    hooks.reset_hooks()
