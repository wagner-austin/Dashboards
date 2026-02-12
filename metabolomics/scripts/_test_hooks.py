"""Test hooks for metabolomics scripts module.

Production code sets these to real implementations at startup.
Tests set them to fakes.
"""

import sys


def _real_print(msg: str) -> None:
    """Print a message to stdout."""
    print(msg)


def _real_exit(code: int) -> None:
    """Exit the process with the given code."""
    sys.exit(code)


# Hooks that can be replaced in tests
print_message = _real_print
exit_process = _real_exit


def reset_hooks() -> None:
    """Reset all hooks to their real implementations."""
    global print_message, exit_process
    print_message = _real_print
    exit_process = _real_exit
