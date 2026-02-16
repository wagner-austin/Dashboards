"""
Search for more Irvine PD ALPR/Flock evidence on MuckRock and other sources.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import json

OUTPUT_DIR = Path(__file__).parent / "data" / "search_results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SEARCHES = [
    # MuckRock searches for Irvine
    ("https://www.muckrock.com/foi/list/?q=irvine+flock&status=done", "muckrock_irvine_flock.txt"),
    ("https://www.muckrock.com/foi/list/?q=irvine+alpr&status=done", "muckrock_irvine_alpr.txt"),
    ("https://www.muckrock.com/foi/list/?q=irvine+police+ice&status=done", "muckrock_irvine_ice.txt"),
    ("https://www.muckrock.com/foi/list/?q=irvine+police+immigration&status=done", "muckrock_irvine_immigration.txt"),

    # MuckRock searches for Orange County
    ("https://www.muckrock.com/foi/list/?q=orange+county+flock&status=done", "muckrock_oc_flock.txt"),
    ("https://www.muckrock.com/foi/list/?q=orange+county+sheriff+ice&status=done", "muckrock_oc_sheriff_ice.txt"),

    # MuckRock searches for Flock + ICE generally
    ("https://www.muckrock.com/foi/list/?q=flock+ice+california&status=done", "muckrock_flock_ice_ca.txt"),
    ("https://www.muckrock.com/foi/list/?q=flock+network+audit&status=done", "muckrock_flock_audit.txt"),

    # EFF Atlas of Surveillance - Irvine
    ("https://atlasofsurveillance.org/search?utf8=%E2%9C%93&location=Irvine%2C+CA", "eff_atlas_irvine.txt"),

    # Oakland Privacy (they got the Flock audit logs)
    ("https://oaklandprivacy.org/?s=flock", "oakland_privacy_flock.txt"),
]


async def main():
    print(f"Output directory: {OUTPUT_DIR}")
    results = {}

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        )
        page = await context.new_page()

        for url, filename in SEARCHES:
            print(f"\n{'='*60}")
            print(f"Searching: {url}")

            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(2000)

                # Get text content
                body_text = await page.inner_text("body")

                # Save
                filepath = OUTPUT_DIR / filename
                filepath.write_text(body_text, encoding="utf-8")
                print(f"Saved: {filename} ({len(body_text)} chars)")

                # Screenshot
                screenshot_name = filename.replace(".txt", ".png")
                await page.screenshot(path=str(OUTPUT_DIR / screenshot_name), full_page=True)

                results[url] = {"file": filename, "chars": len(body_text), "status": "ok"}

                # For MuckRock results, try to find and list the request links
                if "muckrock.com" in url:
                    links = await page.query_selector_all("a.title")
                    request_urls = []
                    for link in links[:10]:  # First 10 results
                        href = await link.get_attribute("href")
                        text = await link.inner_text()
                        if href:
                            full_url = f"https://www.muckrock.com{href}" if href.startswith("/") else href
                            request_urls.append({"title": text.strip(), "url": full_url})
                            print(f"  Found: {text.strip()[:60]}")
                    results[url]["requests"] = request_urls

            except Exception as e:
                print(f"Error: {e}")
                results[url] = {"error": str(e), "status": "failed"}

        await browser.close()

    # Save results
    with open(OUTPUT_DIR / "search_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print("Done! Results saved to search_results.json")


if __name__ == "__main__":
    asyncio.run(main())
