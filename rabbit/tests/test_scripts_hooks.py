"""Tests for scripts/_test_hooks module."""

from __future__ import annotations

import pytest
from scripts import _test_hooks as hooks
from scripts._test_hooks import (
    _real_exit,
    _real_print,
    _real_run_command,
    reset_hooks,
)


def test_real_print(capsys: pytest.CaptureFixture[str]) -> None:
    """Test _real_print outputs to stdout."""
    _real_print("test message")
    captured = capsys.readouterr()
    assert "test message" in captured.out


def test_real_run_command() -> None:
    """Test _real_run_command executes a command."""
    # Use a simple cross-platform command
    result = _real_run_command(["python", "-c", "print('hello')"])
    assert result.returncode == 0
    assert "hello" in result.stdout


def test_real_run_command_failure() -> None:
    """Test _real_run_command captures failure."""
    result = _real_run_command(["python", "-c", "import sys; sys.exit(1)"])
    assert result.returncode == 1


def test_real_exit() -> None:
    """Test _real_exit raises SystemExit."""
    with pytest.raises(SystemExit) as exc_info:
        _real_exit(42)
    assert exc_info.value.code == 42


def test_reset_hooks() -> None:
    """Test reset_hooks restores original implementations."""
    # Save originals
    original_print = hooks.print_message
    original_exit = hooks.exit_process
    original_run = hooks.run_command

    # Modify hooks
    def fake_print(msg: str) -> None:
        pass

    def fake_exit(code: int) -> None:
        pass

    def fake_run(cmd: list[str]) -> hooks.SubprocessResult:
        import subprocess

        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    hooks.print_message = fake_print
    hooks.exit_process = fake_exit
    hooks.run_command = fake_run

    # Reset
    reset_hooks()

    # Verify they are the real implementations
    assert hooks.print_message == _real_print
    assert hooks.exit_process == _real_exit
    assert hooks.run_command == _real_run_command

    # Cleanup
    hooks.print_message = original_print
    hooks.exit_process = original_exit
    hooks.run_command = original_run


def test_subprocess_result_type() -> None:
    """Test SubprocessResult is correct type."""
    import subprocess

    # Verify type alias is correct
    result: hooks.SubprocessResult = subprocess.CompletedProcess(
        args=["test"],
        returncode=0,
        stdout="out",
        stderr="err",
    )
    assert result.returncode == 0
    assert result.stdout == "out"
    assert result.stderr == "err"
