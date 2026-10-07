"""A local HTTP server answering fixed routes, for tests that need a real site.

The scraper tests point the code under test at this server's origin, so the
real HTTP client (requests, or Chromium through Playwright) makes the request
and nothing about the transport is faked. A path with no route answers 404.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlsplit

JSON = "application/json"
HTML = "text/html; charset=utf-8"


class LocalSite:
    """The running server's origin and the request targets it has received."""

    def __init__(self, origin: str, requested: list[str]) -> None:
        """Hold the origin and the shared request log.

        Args:
            origin: e.g. "http://127.0.0.1:50123", with no trailing slash.
            requested: Each request's path and query, appended as it arrives.
        """
        self.origin = origin
        self.requested = requested


def _handler(routes: dict[str, tuple[str, str]], requested: list[str]) -> type[BaseHTTPRequestHandler]:
    """Build a handler class answering ``routes``, keyed by path without query."""

    class _RouteHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            requested.append(self.path)
            route = routes.get(urlsplit(self.path).path)
            if route is None:
                self.send_error(404, "no such route")
                return
            content_type, body = route
            payload = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return _RouteHandler


@contextmanager
def local_site(routes: dict[str, tuple[str, str]]) -> Iterator[LocalSite]:
    """Serve ``routes`` on a free localhost port for the duration of the block.

    Args:
        routes: Path (no query string) to (content type, body).

    Yields:
        LocalSite: The server's origin and request log.
    """
    requested: list[str] = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(routes, requested))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield LocalSite(f"http://127.0.0.1:{server.server_address[1]}", requested)
    finally:
        server.shutdown()
        server.server_close()
