"""Test hooks for the TankPit publisher entry point.

Production sets these to the real implementations at import time; tests
replace them with fakes so the wiring itself runs under test without a
network or a filesystem write.

Only process-level effects live here. The publisher's own collaborators
are injected as protocol implementations instead, which is how the rest
of this repo does dependency injection.
"""

from collections.abc import Callable

from .client import FleetFetcher, RequestsFleetFetcher
from .publish import Clock, DocumentWriter, FileDocumentWriter, SystemClock


def _real_print(message: str) -> None:
    """Print a message to stdout.

    Args:
        message: Text to print.
    """
    print(message)


def _real_make_fetcher() -> FleetFetcher:
    """Build the production fleet fetcher.

    Returns:
        A fetcher reading the manager over HTTP.
    """
    return RequestsFleetFetcher()


def _real_make_clock() -> Clock:
    """Build the production clock.

    Returns:
        A clock reading the system time.
    """
    return SystemClock()


def _real_make_writer() -> DocumentWriter:
    """Build the production document writer.

    Returns:
        A writer that writes to the filesystem.
    """
    return FileDocumentWriter()


# Annotated with the protocol each hook satisfies rather than with the
# concrete function, so a test may install any callable of that shape.
print_message: Callable[[str], None] = _real_print
make_fetcher: Callable[[], FleetFetcher] = _real_make_fetcher
make_clock: Callable[[], Clock] = _real_make_clock
make_writer: Callable[[], DocumentWriter] = _real_make_writer


def reset_hooks() -> None:
    """Restore every hook to its real implementation."""
    global print_message, make_fetcher, make_clock, make_writer
    print_message = _real_print
    make_fetcher = _real_make_fetcher
    make_clock = _real_make_clock
    make_writer = _real_make_writer
