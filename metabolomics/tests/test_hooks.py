"""Tests for the _test_hooks module."""

from __future__ import annotations

import pytest

from scripts import _test_hooks as hooks


def test_real_print_calls_print(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that _real_print outputs to stdout."""
    hooks._real_print("test message")
    captured = capsys.readouterr()
    assert captured.out == "test message\n"


def test_real_exit_raises_system_exit() -> None:
    """Test that _real_exit raises SystemExit."""
    with pytest.raises(SystemExit) as exc_info:
        hooks._real_exit(42)
    assert exc_info.value.code == 42


def test_default_hooks_are_real_implementations() -> None:
    """Test that default hooks point to real implementations."""
    hooks.reset_hooks()
    assert hooks.print_message is hooks._real_print
    assert hooks.exit_process is hooks._real_exit


def test_hooks_can_be_replaced() -> None:
    """Test that hooks can be replaced with fakes."""
    messages: list[str] = []
    exit_codes: list[int] = []

    def fake_print(msg: str) -> None:
        messages.append(msg)

    def fake_exit(code: int) -> None:
        exit_codes.append(code)

    hooks.print_message = fake_print
    hooks.exit_process = fake_exit

    hooks.print_message("hello")
    hooks.exit_process(0)

    assert messages == ["hello"]
    assert exit_codes == [0]

    # Clean up
    hooks.reset_hooks()


def test_reset_hooks_restores_real_implementations() -> None:
    """Test that reset_hooks restores the real implementations."""
    # Replace with fakes
    hooks.print_message = lambda msg: None
    hooks.exit_process = lambda code: None

    # Verify they're fakes
    assert hooks.print_message is not hooks._real_print
    assert hooks.exit_process is not hooks._real_exit

    # Reset
    hooks.reset_hooks()

    # Verify they're real again
    assert hooks.print_message is hooks._real_print
    assert hooks.exit_process is hooks._real_exit
