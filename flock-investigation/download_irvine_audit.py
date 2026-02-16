"""
Download the new Irvine PD ALPR Audits request from MuckRock (completed March 2025).
Also get any other relevant California Flock audit requests.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import httpx

OUTPUT_DIR = Path(__file__).parent / "data" / "muckrock"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REQUESTS = [
    # NEW: Irvine ALPR Audits - Joey Scott - March 2025
    "https://www.muckrock.com/foi/irvine-3262/alpr-audits-irvine-police-department-180285/",

    # California Flock Network Audits from other agencies for comparison
    "https://www.muckrock.com/foi/san-jose-1543/flock-network-audit-184968/",
    "https://www.muckrock.com/foi/bakersfield-2671/three-flock-safety-network-audit-records-bakersfield-police-department-179802/",
    "https://www.muckrock.com/foi/california-52/flock-safety-search-audits-network-sharing-and-images-california-highway-patrol-181461/",

    # Orange County specific
    "https://www.muckrock.com/foi/orange-county-394/automated-license-plate-readers-orange-county-sheriffs-office-136291/",
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

            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(2000)

                # Get the request ID from URL
                req_id = url.split("/")[-2]

                # Screenshot
                await page.screenshot(path=str(OUTPUT_DIR / f"{req_id}.png"), full_page=True)
                print(f"Screenshot saved: {req_id}.png")

                # Get text content
                body_text = await page.inner_text("body")
                with open(OUTPUT_DIR / f"{req_id}.txt", "w", encoding="utf-8") as f:
                    f.write(body_text)
                print(f"Text saved: {req_id}.txt ({len(body_text)} chars)")

                # Find and download PDFs/documents
                pdf_links = await page.query_selector_all("a[href*='.pdf'], a[href*='cdn.muckrock.com'], a.file-link")
                seen_urls = set()

                for i, link in enumerate(pdf_links):
                    href = await link.get_attribute("href")
                    if href and href not in seen_urls:
                        seen_urls.add(href)
                        text = await link.inner_text()
                        print(f"  Found doc: {text.strip()[:50]} -> {href[:80]}...")

                        if not href.startswith("http"):
                            href = f"https://www.muckrock.com{href}"

                        try:
                            async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                                response = await client.get(href, headers={
                                    "User-Agent": "Mozilla/5.0",
                                    "Referer": url
                                })
                                if response.status_code == 200:
                                    # Determine extension
                                    if ".pdf" in href.lower():
                                        ext = ".pdf"
                                    elif ".xlsx" in href.lower():
                                        ext = ".xlsx"
                                    elif ".csv" in href.lower():
                                        ext = ".csv"
                                    else:
                                        ext = ".dat"

                                    doc_name = f"{req_id}_doc{i}{ext}"
                                    doc_path = OUTPUT_DIR / doc_name
                                    doc_path.write_bytes(response.content)
                                    print(f"  Downloaded: {doc_name} ({len(response.content)} bytes)")
                        except Exception as e:
                            print(f"  Failed to download: {e}")

            except Exception as e:
                print(f"Error: {e}")

        await browser.close()

    print(f"\n{'='*60}")
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
