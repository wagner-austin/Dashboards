"""Exercise the real homepage layout and disclosure controls in Chromium."""

from collections.abc import Iterator
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
from playwright.sync_api import Page, sync_playwright


@pytest.fixture
def homepage() -> Iterator[Page]:
    """Serve repository assets and yield a real browser page.

    Yields:
        Page: Chromium page connected to the local static site.
    """
    root = Path(__file__).resolve().parents[1]
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(root)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{server.server_port}/")
            yield page
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("width", [320, 390, 768, 1440])
def test_homepage_preserves_desktop_composition(homepage: Page, width: int) -> None:
    """Keep the desktop canvas, gradient and forest at every screen size.

    Args:
        homepage (Page): Browser page serving the actual repository.
        width (int): Viewport width in CSS pixels.
    """
    homepage.set_viewport_size({"width": width, "height": 900})
    assert homepage.locator('meta[name="viewport"]').get_attribute("content") == "width=1200"
    assert homepage.locator(".dashboards > li").count() == 6
    assert homepage.locator(".dashboards a").first.get_attribute("href") == "https://search.austinwagner.org"
    assert homepage.locator("details").count() == 5
    assert homepage.locator("details[open]").count() == 0
    assert homepage.locator("details a").count() == 14
    for summary in homepage.locator("details > summary").all():
        summary.focus()
        homepage.keyboard.press("Enter")
    assert homepage.locator("details[open]").count() == 5
    scroll_width: int = homepage.evaluate("document.documentElement.scrollWidth")
    canvas_width = max(width, 1200)
    assert scroll_width == canvas_width
    gradient: str = homepage.locator(".page").evaluate(
        "(element) => getComputedStyle(element).backgroundImage"
    )
    assert gradient.startswith("linear-gradient(")
    assert "rgb(10, 10, 10) 79%" in gradient
    for panel in homepage.locator(".work .panel, .dashboards .panel").all():
        bounds = panel.bounding_box()
        assert bounds is not None
        assert bounds["x"] >= 0
        assert bounds["x"] + bounds["width"] <= canvas_width
        background: str = panel.evaluate("(element) => getComputedStyle(element).backgroundColor")
        assert background == "rgba(0, 0, 0, 0)"
        fill: str = panel.evaluate("(element) => getComputedStyle(element).backgroundImage")
        assert fill.startswith("linear-gradient(")
        font_size: str = panel.locator("p").evaluate("(element) => getComputedStyle(element).fontSize")
        assert font_size == "18px"
    upper = homepage.locator(".upper").bounding_box()
    forest = homepage.locator("#backdrop").bounding_box()
    assert upper is not None
    assert forest is not None
    assert forest["height"] == 1360
    assert forest["y"] == pytest.approx(upper["y"] + upper["height"] - 942, abs=0.01)
    mask: str = homepage.locator("#backdrop").evaluate("(element) => getComputedStyle(element).maskImage")
    assert mask.startswith("linear-gradient(")
    assert "rgba(0, 0, 0, 0.12) 40%" in mask
    for summary in homepage.locator("details.workcat > summary").all():
        summary_background: str = summary.evaluate("(element) => getComputedStyle(element).backgroundColor")
        assert summary_background == "rgba(0, 0, 0, 0)"
        summary_fill: str = summary.evaluate("(element) => getComputedStyle(element).backgroundImage")
        assert summary_fill.startswith("linear-gradient(")
    cards = homepage.locator(".dashboards a")
    first = cards.nth(0).bounding_box()
    second = cards.nth(1).bounding_box()
    assert first is not None
    assert second is not None
    assert first["y"] == second["y"]
    assert second["x"] >= first["x"] + first["width"]


def test_homepage_is_promoted_to_the_site_root(homepage: Page) -> None:
    """Serve the homepage indexable at /, redirect /preview/ to it, and link articles home.

    Args:
        homepage (Page): Browser page serving the actual repository.
    """
    assert homepage.locator('meta[name="robots"]').count() == 0
    root = homepage.url
    homepage.goto(f"{root}preview/")
    homepage.wait_for_url(root)
    assert homepage.locator("h1").inner_text() == "Austin Wagner"
    article_href = homepage.locator("details a").first.get_attribute("href")
    assert article_href == "/preview/measuring-what-a-corpus-installs/"
    homepage.goto(f"{root}preview/measuring-what-a-corpus-installs/")
    assert homepage.locator('meta[name="robots"]').count() == 0
    assert homepage.locator('a[href="/preview/"]').count() == 0
    assert homepage.locator('a[href="/"]').count() == 3
