"""
Search MuckRock directly for Irvine PD requests and get correct URLs.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path(__file__).parent / "data" / "muckrock"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    print("Searching MuckRock for Irvine PD requests...")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        )
        page = await context.new_page()

        # Search for Irvine PD ALPR requests
        url = "https://www.muckrock.com/foi/list/?q=&agency=3274&status=done"  # Irvine PD agency ID
        print(f"Fetching: {url}")

        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

        # Screenshot
        await page.screenshot(path=str(OUTPUT_DIR / "muckrock_irvine_pd_all.png"), full_page=True)

        # Get text content
        body_text = await page.inner_text("body")
        with open(OUTPUT_DIR / "muckrock_irvine_pd_all.txt", "w", encoding="utf-8") as f:
            f.write(body_text)
        print(f"Saved: muckrock_irvine_pd_all.txt ({len(body_text)} chars)")

        # Find all request links
        links = await page.query_selector_all("a[href*='/foi/irvine']")
        print(f"\nFound {len(links)} Irvine-related links:")
        for link in links:
            href = await link.get_attribute("href")
            text = await link.inner_text()
            if href and "/foi/" in href:
                full_url = f"https://www.muckrock.com{href}" if href.startswith("/") else href
                print(f"  {text.strip()[:60]}")
                print(f"    -> {full_url}")

        # Also try the direct agency search page
        agency_url = "https://www.muckrock.com/agency/irvine-3262/"
        print(f"\nFetching agency page: {agency_url}")
        await page.goto(agency_url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)

        await page.screenshot(path=str(OUTPUT_DIR / "muckrock_irvine_agency.png"), full_page=True)

        body_text = await page.inner_text("body")
        with open(OUTPUT_DIR / "muckrock_irvine_agency.txt", "w", encoding="utf-8") as f:
            f.write(body_text)
        print(f"Saved: muckrock_irvine_agency.txt ({len(body_text)} chars)")

        # Find request links on agency page
        links = await page.query_selector_all("a[href*='/foi/']")
        print(f"\nFound {len(links)} FOI links on agency page:")
        for link in links:
            href = await link.get_attribute("href")
            text = await link.inner_text()
            if href and "irvine" in href.lower() and text.strip():
                full_url = f"https://www.muckrock.com{href}" if href.startswith("/") else href
                print(f"  {text.strip()[:70]}")
                print(f"    -> {full_url}")

        await browser.close()

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
