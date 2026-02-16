"""
Download the actual MuckRock FOIA responses for Irvine PD ALPR.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import httpx

OUTPUT_DIR = Path(__file__).parent / "data" / "muckrock"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REQUESTS = [
    # 2020 Vigilant Data Sharing
    "https://www.muckrock.com/foi/irvine-3262/2020-vigilant-data-sharing-information-automated-license-plate-reader-alpr-irvine-police-department-86954/",
    # General ALPR request
    "https://www.muckrock.com/foi/irvine-3262/automated-license-plate-readers-irvine-police-department-136259/",
    # Flock damage costs (shows they use Flock now)
    "https://www.muckrock.com/foi/irvine-3262/flock-damage-costs-irvine-police-department-181097/",
]


async def main():
    print(f"Output directory: {OUTPUT_DIR}")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        )
        page = await context.new_page()

        for url in REQUESTS:
            print(f"\n{'='*60}")
            print(f"Fetching: {url}")

            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(2000)

            # Get the request ID from URL
            req_id = url.split("/")[-2]

            # Screenshot
            await page.screenshot(path=str(OUTPUT_DIR / f"{req_id}.png"), full_page=True)
            print(f"Screenshot saved: {req_id}.png")

            # Save HTML
            content = await page.content()
            with open(OUTPUT_DIR / f"{req_id}.html", "w", encoding="utf-8") as f:
                f.write(content)

            # Get text content
            body_text = await page.inner_text("body")
            with open(OUTPUT_DIR / f"{req_id}.txt", "w", encoding="utf-8") as f:
                f.write(body_text)

            # Find PDF links
            pdf_links = await page.query_selector_all("a[href*='.pdf']")
            for i, link in enumerate(pdf_links):
                href = await link.get_attribute("href")
                text = await link.inner_text()
                print(f"Found PDF: {text} -> {href}")

                # Download the PDF
                if href:
                    if not href.startswith("http"):
                        href = f"https://www.muckrock.com{href}"

                    try:
                        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                            response = await client.get(href, headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                                "Referer": url
                            })
                            if response.status_code == 200:
                                pdf_name = f"{req_id}_doc{i}.pdf"
                                pdf_path = OUTPUT_DIR / pdf_name
                                pdf_path.write_bytes(response.content)
                                print(f"Downloaded: {pdf_name}")
                    except Exception as e:
                        print(f"Failed to download PDF: {e}")

            # Also look for file links in the documents section
            file_links = await page.query_selector_all(".file-link a, .document-link a, a[href*='cdn.muckrock.com']")
            for i, link in enumerate(file_links):
                href = await link.get_attribute("href")
                if href:
                    print(f"Found file link: {href}")

        await browser.close()

    print(f"\n{'='*60}")
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
