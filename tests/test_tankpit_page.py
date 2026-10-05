"""Exercise the TankPit bots page and its caption timing in real Chromium."""

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
    headings = page.locator("#about h3").all_inner_texts()
    assert headings == ["TankPit", "The bot", "Practice room only"]
    about = page.locator("#about").inner_text()
    assert "multiplayer tank game played in the web browser" in about
    assert "driven by a program, not a person" in about
    assert "The bots play only in TankPit's practice room" in about
    assert "sound is off until you turn it on" in about
    page.locator("#state").filter(has_text="offline").wait_for()
    scroll_width: int = page.evaluate("document.documentElement.scrollWidth")
    assert scroll_width == width


def test_the_caption_shown_is_the_one_in_force_at_the_frame(site: tuple[Page, str]) -> None:
    """The caption follows the frame on screen, not the bot's newest decision.

    Args:
        site (tuple[Page, str]): Browser page and the local site root.
    """
    page, root = site
    page.goto(f"{root}tankpit/")
    picks: list[str | None] = page.evaluate(
        """async () => {
            const { captionAt } = await import("./captions.js");
            const captions = [
                { at_ms: 1000, doing: "Searching for enemies" },
                { at_ms: 4000, doing: "Teleporting to an enemy" },
                { at_ms: 9000, doing: "Shooting at an enemy" },
            ];
            return [500, 1000, 3999, 4000, 8999, 20000].map(
                (moment) => captionAt(captions, moment)?.doing ?? null
            );
        }"""
    )
    assert picks == [
        None,
        "Searching for enemies",
        "Searching for enemies",
        "Teleporting to an enemy",
        "Teleporting to an enemy",
        "Shooting at an enemy",
    ]


def test_the_frame_moment_comes_from_whichever_player_is_playing(site: tuple[Page, str]) -> None:
    """hls.js reports a playing date; a native player its start date plus position.

    Args:
        site (tuple[Page, str]): Browser page and the local site root.
    """
    page, root = site
    page.goto(f"{root}tankpit/")
    moments: list[float | None] = page.evaluate(
        """async () => {
            const { frameMomentMs } = await import("./captions.js");
            const video = document.createElement("video");
            const dated = { getStartDate: () => new Date(50000), currentTime: 2.5 };
            const undated = { getStartDate: () => new Date(NaN), currentTime: 0 };
            return [
                frameMomentMs(video, { playingDate: new Date(7000) }),
                frameMomentMs(video, { playingDate: null }),
                frameMomentMs(dated, null),
                frameMomentMs(undated, null),
                frameMomentMs({ currentTime: 1 }, null),
            ];
        }"""
    )
    assert moments == [7000, None, 52500, None, None]
