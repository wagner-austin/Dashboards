"""Tests for the ASUCI HTTP transport.

These run the real RequestsFetcher against a local HTTP server rather than a
stand-in, so the session wiring, status handling, and error translation are all
exercised as they run in production.
"""

import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
import requests
from asuci.client import (
    AsuciFetchError,
    ChainCompletingAdapter,
    RequestsFetcher,
    create_fetcher,
    create_ssl_context,
)


class _Handler(BaseHTTPRequestHandler):
    """Serves a fixed body, or a chosen status for /missing."""

    def do_GET(self) -> None:
        """Answer a GET request."""
        if self.path.startswith("/missing"):
            self.send_response(404)
            self.end_headers()
            return
        body = f"path={self.path}".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Silence the default request logging."""


@pytest.fixture
def server() -> Iterator[str]:
    """Run a local HTTP server for the duration of a test.

    Yields:
        The server's base URL.
    """
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def test_get_text_returns_the_body(server: str) -> None:
    """A successful response is returned as text."""
    fetcher = RequestsFetcher(requests.Session())

    assert fetcher.get_text(f"{server}/hello", {}) == "path=/hello"


def test_get_text_sends_query_parameters(server: str) -> None:
    """Query parameters reach the server."""
    fetcher = RequestsFetcher(requests.Session())

    body = fetcher.get_text(f"{server}/view", {"year": "20242025"})

    assert body == "path=/view?year=20242025"


def test_get_text_rejects_a_non_success_status(server: str) -> None:
    """A 404 raises with the status in the message."""
    fetcher = RequestsFetcher(requests.Session())

    with pytest.raises(AsuciFetchError, match="returned HTTP 404"):
        fetcher.get_text(f"{server}/missing", {})


def test_get_text_translates_a_connection_failure() -> None:
    """An unreachable host raises the project's error, not requests'."""
    fetcher = RequestsFetcher(requests.Session())

    with pytest.raises(AsuciFetchError, match="failed"):
        fetcher.get_text("http://127.0.0.1:1/unreachable", {})


def test_create_fetcher_mounts_the_chain_completing_adapter() -> None:
    """The production fetcher verifies through the chain-completing adapter."""
    fetcher = create_fetcher()

    adapter = fetcher._session.get_adapter("https://asuci.uci.edu/")
    assert isinstance(adapter, ChainCompletingAdapter)


def test_create_fetcher_sends_a_browser_user_agent() -> None:
    """The session identifies as a browser for the upstream WAF."""
    fetcher = create_fetcher()

    assert "Mozilla/5.0" in str(fetcher._session.headers["User-Agent"])
    assert fetcher._session.headers["Referer"] == "https://asuci.uci.edu/"


def test_adapter_applies_its_context_to_new_pools(server: str) -> None:
    """The adapter's context reaches the pool manager and still serves traffic."""
    adapter = ChainCompletingAdapter(create_ssl_context())
    session = requests.Session()
    session.mount("http://", adapter)

    assert session.get(f"{server}/ok", timeout=10).text == "path=/ok"
