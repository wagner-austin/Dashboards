"""Test hooks for the guard script.

Production sets these to the real implementations at import time; tests replace
them with fakes so guard output can be asserted without capturing stdout.
"""


def _real_print(message: str) -> None:
    """Print a message to stdout.

    Args:
        message: Text to print.
    """
    print(message)


print_message = _real_print


def reset_hooks() -> None:
    """Restore every hook to its real implementation."""
    global print_message
    print_message = _real_print
