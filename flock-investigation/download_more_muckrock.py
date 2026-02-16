"""
Download additional MuckRock FOIA responses for OC ALPR investigation.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import httpx

OUTPUT_DIR = Path(__file__).parent / "data" / "muckrock"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REQUESTS = [
    # OC Sheriff 2020 Vigilant Data Sharing
    "https://www.muckrock.com/foi/orange-county-394/2020-vigilant-data-sharing-information-automated-license-plate-reader-alpr-orange-county-sheriffs-office-86943/",
    # OC Sheriff general ALPR
    "https://www.muckrock.com/foi/orange-county-394/automated-license-plate-readers-orange-county-sheriffs-office-136291/",
    # Orange PD ALPR
    "https://www.muckrock.com/foi/orange-3354/automated-license-plate-readers-orange-police-department-136054/",
    # ICE Flock Lookup Tool - THIS IS KEY
    "https://www.muckrock.com/foi/united-states-of-america-10/foia-request-lookup-tool-176401/",
    # Flock data sharing policies (California)
    "https://www.muckrock.com/foi/california-52/flock-safety-and-alpr-data-and-policies-200784/",
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

            # Find and download PDFs
            pdf_links = await page.query_selector_all("a[href*='.pdf'], a[href*='cdn.muckrock.com']")
            seen_urls = set()
            for i, link in enumerate(pdf_links):
                href = await link.get_attribute("href")
                if href and href not in seen_urls and ('.pdf' in href or 'cdn.muckrock.com' in href):
                    seen_urls.add(href)
                    text = await link.inner_text()
                    print(f"Found: {text.strip()[:50]} -> {href}")

                    if not href.startswith("http"):
                        href = f"https://www.muckrock.com{href}"

                    try:
                        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                            response = await client.get(href, headers={
                                "User-Agent": "Mozilla/5.0",
                                "Referer": url
                            })
                            if response.status_code == 200:
                                ext = ".pdf" if ".pdf" in href else ".dat"
                                doc_name = f"{req_id}_doc{i}{ext}"
                                doc_path = OUTPUT_DIR / doc_name
                                doc_path.write_bytes(response.content)
                                print(f"Downloaded: {doc_name}")
                    except Exception as e:
                        print(f"Failed: {e}")

        await browser.close()

    print(f"\n{'='*60}")
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
