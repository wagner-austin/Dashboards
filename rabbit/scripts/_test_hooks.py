"""Test hooks for generate_sprites module.

Production code sets these to real implementations at startup.
Tests set them to fakes.
"""

import subprocess
import sys

# Type for subprocess run result
SubprocessResult = subprocess.CompletedProcess[str]


def _real_run_command(cmd: list[str]) -> SubprocessResult:
    """Run a subprocess command and return the result."""
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _real_exit(code: int) -> None:
    """Exit the process with the given code."""
    sys.exit(code)


def _real_print(msg: str) -> None:
    """Print a message to stdout."""
    print(msg)


# Hooks that can be replaced in tests
run_command = _real_run_command
exit_process = _real_exit
print_message = _real_print


def reset_hooks() -> None:
    """Reset all hooks to their real implementations."""
    global run_command, exit_process, print_message
    run_command = _real_run_command
    exit_process = _real_exit
    print_message = _real_print
