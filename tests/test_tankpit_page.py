"""Exercise the TankPit video page in real Chromium."""

from collections.abc import Iterator
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from os import PathLike
from pathlib import Path
from threading import Thread

import pytest
from playwright.sync_api import Page, Route, sync_playwright

FLEET_ORIGIN = "https://tankpit.austinwagner.org"


class _ModuleHandler(SimpleHTTPRequestHandler):
    """Serve the repository with JavaScript typed as JavaScript.

    A module script is refused unless its response says it is JavaScript,
    and on Windows the standard library reads that mapping from the
    registry, which does not always say so.
    """

    def guess_type(self, path: str | PathLike[str]) -> str:
        """Type a ``.js`` file as JavaScript, everything else as the stdlib does.

        Args:
            path (str | PathLike[str]): The file being served.

        Returns:
            str: Its media type.
        """
        if str(path).endswith(".js"):
            return "text/javascript"
        return super().guess_type(path)


def _refuse(route: Route) -> None:
    """Fail a request to the live fleet, so the test never depends on it.

    Args:
        route (Route): The intercepted request.
    """
    route.abort()


@pytest.fixture
def site() -> Iterator[tuple[Page, str]]:
    """Serve the repository and yield a Chromium page with no route to the fleet.

    Yields:
        tuple[Page, str]: The page and the local site's root URL.
    """
    root = Path(__file__).resolve().parents[1]
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_ModuleHandler, directory=str(root)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.route(f"{FLEET_ORIGIN}/**", _refuse)
            yield page, f"http://127.0.0.1:{server.server_port}/"
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("width", [360, 1280])
def test_the_page_explains_the_game_the_bot_and_the_practice_room(site: tuple[Page, str], width: int) -> None:
    """A visitor who has never played reads what TankPit and the bot are.

    Args:
        site (tuple[Page, str]): Browser page and the local site root.
        width (int): Viewport width in CSS pixels.
    """
    page, root = site
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(f"{root}tankpit/")
    start = page.locator("#start").bounding_box()
    assert start is not None
    assert start["y"] + start["height"] < 600
    architecture = page.locator("#architecture")
    assert architecture.get_attribute("open") is None
    assert not architecture.locator(".modes").is_visible()
    architecture.locator("summary").click()
    assert architecture.locator(".modes").is_visible()
    assert architecture.locator("h2").all_inner_texts() == ["Collect supplies", "Hunt an opponent"]
    assert "hierarchical finite-state machine" in architecture.inner_text()
    assert page.locator("#about").get_attribute("open") is None
    page.locator("#about summary").click()
    about = page.locator("#about").inner_text()
    assert "multiplayer tank game" in about
    assert "reads the game's messages and sends its own commands" in about
    assert "practice room" in about
    assert "Sound starts off" in page.locator(".session-note").inner_text()
    page.locator("#state").filter(has_text="offline").wait_for()
    scroll_width: int = page.evaluate("document.documentElement.scrollWidth")
    assert scroll_width == width


def test_status_is_in_the_video_without_a_second_caption_panel(site: tuple[Page, str]) -> None:
    """A listed bot keeps video and sound controls without external captions.

    Args:
        site (tuple[Page, str]): Browser page and the local site root.
    """
    page, root = site
    page.route(
        f"{FLEET_ORIGIN}/demo/fleet",
        lambda route: route.fulfill(
            json={
                "running": 1,
                "capacity": 5,
                "draining": False,
                "bots": [{"slot": "demo-1", "alive": True, "uptime_seconds": 12}],
            }
        ),
    )
    page.goto(f"{root}tankpit/")
    page.locator("#views video").wait_for()
    assert page.locator("#views video").get_attribute("aria-label") == "Live view of demo-1"
    assert page.locator("#views .sound").inner_text() == "Sound off"
    assert page.locator("#views .say").count() == 0
    assert page.locator("#views .cap b").inner_text() == "demo-1"
    assert "in-game status panel" in page.locator(".watch-hint").inner_text()
