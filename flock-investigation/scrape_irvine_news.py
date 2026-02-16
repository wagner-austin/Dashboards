"""
Scrape news articles about Irvine PD and ALPR/ICE.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import json

OUTPUT_DIR = Path(__file__).parent / "data" / "news"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ARTICLES = [
    # EFF article about Irvine PD racist searches
    ("https://www.eff.org/deeplinks/2025/11/license-plate-surveillance-logs-reveal-racist-policing-against-romani-people",
     "eff_romani_irvine.txt"),
    # New University - ICE in Irvine
    ("https://newuniversity.org/2025/06/12/breaking-irvine-council-member-confirms-ice-is-in-irvine/",
     "newu_ice_irvine.txt"),
    # Voice of OC year on ICE
    ("https://voiceofoc.org/2025/12/orange-countys-year-on-ice/",
     "voiceofoc_year_on_ice.txt"),
    # City of Irvine immigration response
    ("https://cityofirvine.org/news-media/news-article/city-irvine-immigration-response",
     "irvine_immigration_response.txt"),
    # Irvine immigration enforcement updates
    ("https://cityofirvine.org/immigration-enforcement-updates",
     "irvine_enforcement_updates.txt"),
    # CalMatters - CA police sharing with ICE
    ("https://calmatters.org/economy/technology/2025/06/california-police-sharing-license-plate-reader-data/",
     "calmatters_ca_police_ice.txt"),
    # The Markup - every agency enforcing for ICE
    ("https://themarkup.org/tools/2025/04/16/law-enforcement-ice-cooperation-tracker",
     "markup_ice_tracker.txt"),
]


async def main():
    print(f"Output directory: {OUTPUT_DIR}")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        )
        page = await context.new_page()

        results = {}

        for url, filename in ARTICLES:
            print(f"\n{'='*60}")
            print(f"Fetching: {url}")

            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(2000)

                # Get text content
                body_text = await page.inner_text("body")

                # Save
                filepath = OUTPUT_DIR / filename
                filepath.write_text(body_text, encoding="utf-8")
                print(f"Saved: {filename} ({len(body_text)} chars)")

                # Also save screenshot
                screenshot_name = filename.replace(".txt", ".png")
                await page.screenshot(path=str(OUTPUT_DIR / screenshot_name), full_page=True)

                results[url] = {"file": filename, "chars": len(body_text), "status": "ok"}

            except Exception as e:
                print(f"Error: {e}")
                results[url] = {"error": str(e), "status": "failed"}

        await browser.close()

    # Save results
    with open(OUTPUT_DIR / "scrape_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
