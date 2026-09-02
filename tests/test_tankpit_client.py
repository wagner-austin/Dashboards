"""Client tests for the TankPit publisher.

The typed reads run against a fetcher serving captured bodies. The
requests-backed fetcher runs against a real HTTP server on loopback, so
the production path is exercised end to end rather than stood in for.
"""

import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
import requests
from tankpit.client import REQUEST_TIMEOUT_SECONDS, FleetClient, RequestsFleetFetcher

from tests.tankpit_payloads import (
    DEAD_BOT_ROSTER_TEXT,
    EMPTY_ROSTER_TEXT,
    HUD_ABSENT_TEXT,
    HUD_PRESENT_TEXT,
)

# Path the failure test asks for, answered with a 500.
FAILING_PATH = "/boom"


class RecordingFetcher:
    """A fetcher serving captured bodies and recording what was asked for."""

    def __init__(self, bodies: dict[str, str]) -> None:
        """Bind the fetcher to its canned bodies.

        Args:
            bodies: Response text keyed by the exact URL requested.
        """
        self._bodies = bodies
        self.requested: list[str] = []

    def get_text(self, url: str) -> str:
        """Return the canned body for a URL.

        Args:
            url: Absolute URL to read.

        Returns:
            The canned body.

        Raises:
            KeyError: If the test did not arrange a body for this URL.
        """
        self.requested.append(url)
        return self._bodies[url]


class _CapturedHandler(BaseHTTPRequestHandler):
    """Serves one captured roster, and a 500 on :data:`FAILING_PATH`."""

    def do_GET(self) -> None:
        """Answer a GET with a captured body or a deliberate failure."""
        if self.path == FAILING_PATH:
            self.send_response(500)
            self.end_headers()
            return
        body = EMPTY_ROSTER_TEXT.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Silence the default stderr request log.

        The parameter name matches :class:`BaseHTTPRequestHandler`, which
        this must override exactly to stay silent.

        Args:
            format: Printf-style template the base class would log.
            args: Template arguments.
        """


@pytest.fixture
def live_server() -> Iterator[str]:
    """Run a real HTTP server on loopback for the duration of one test.

    Yields:
        The server's base URL.
    """
    server = HTTPServer(("127.0.0.1", 0), _CapturedHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[0], server.server_address[1]
    # server_address is widened to cover every address family; this server
    # is bound to an IPv4 loopback pair, so narrow it rather than format
    # whatever turns up.
    if not isinstance(host, str) or not isinstance(port, int):
        raise AssertionError(f"expected an IPv4 host/port pair, got {host!r}:{port!r}")
    yield f"http://{host}:{port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def test_read_roster_decodes_a_captured_body() -> None:
    fetcher = RecordingFetcher({"http://fleet/bots": DEAD_BOT_ROSTER_TEXT})
    client = FleetClient(fetcher, "http://fleet")
    roster = client.read_roster()
    assert roster["bots"][0]["instance"] == "probe-1"


def test_read_roster_requests_the_documented_path() -> None:
    fetcher = RecordingFetcher({"http://fleet/bots": EMPTY_ROSTER_TEXT})
    FleetClient(fetcher, "http://fleet").read_roster()
    assert fetcher.requested == ["http://fleet/bots"]


def test_a_trailing_slash_on_the_base_url_does_not_double_up() -> None:
    fetcher = RecordingFetcher({"http://fleet/bots": EMPTY_ROSTER_TEXT})
    FleetClient(fetcher, "http://fleet/").read_roster()
    assert fetcher.requested == ["http://fleet/bots"]


def test_read_hud_returns_none_when_the_bot_has_written_no_frame() -> None:
    fetcher = RecordingFetcher({"http://fleet/bots/probe-1/hud": HUD_ABSENT_TEXT})
    assert FleetClient(fetcher, "http://fleet").read_hud("probe-1") is None


def test_read_hud_decodes_a_real_frame() -> None:
    fetcher = RecordingFetcher({"http://fleet/bots/probe-1/hud": HUD_PRESENT_TEXT})
    hud = FleetClient(fetcher, "http://fleet").read_hud("probe-1")
    if hud is None:
        raise AssertionError("the captured frame decodes to a HUD, not to absent")
    assert hud["state_text"] == "COLLECTING"


def test_the_requests_fetcher_reads_a_real_server(live_server: str) -> None:
    body = RequestsFleetFetcher().get_text(f"{live_server}/bots")
    assert body == EMPTY_ROSTER_TEXT


def test_the_requests_fetcher_raises_on_an_error_status(live_server: str) -> None:
    with pytest.raises(requests.HTTPError):
        RequestsFleetFetcher().get_text(f"{live_server}{FAILING_PATH}")


def test_the_client_reads_a_real_server_end_to_end(live_server: str) -> None:
    roster = FleetClient(RequestsFleetFetcher(), live_server).read_roster()
    assert roster == {"boot": "1788341122781", "draining": False, "bots": []}


def test_the_default_timeout_is_bounded() -> None:
    assert REQUEST_TIMEOUT_SECONDS == 10
