"""
Download critical Irvine PD requests from MuckRock.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import httpx

OUTPUT_DIR = Path(__file__).parent / "data" / "muckrock"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REQUESTS = [
    # ALPR Audits - 7 files
    "https://www.muckrock.com/foi/irvine-3262/alpr-audits-irvine-police-department-181267/",
    # California Police and Immigration - 35 files - CRITICAL
    "https://www.muckrock.com/foi/irvine-3262/california-police-and-immigration-irvine-police-department-184958/",
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
                await page.wait_for_timeout(3000)

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

                # Click "Expand All" if available to show all files
                try:
                    expand_btn = await page.query_selector("text=Expand All")
                    if expand_btn:
                        await expand_btn.click()
                        await page.wait_for_timeout(2000)
                except:
                    pass

                # Find and download all file links
                file_links = await page.query_selector_all("a.file-link, a[href*='cdn.muckrock.com'], a[href*='.pdf']")
                seen_urls = set()

                print(f"Found {len(file_links)} potential file links")

                for i, link in enumerate(file_links):
                    href = await link.get_attribute("href")
                    if href and href not in seen_urls and ('cdn.muckrock.com' in href or '.pdf' in href):
                        seen_urls.add(href)
                        text = await link.inner_text()

                        if not href.startswith("http"):
                            href = f"https://www.muckrock.com{href}"

                        print(f"  [{i}] {text.strip()[:50]} -> downloading...")

                        try:
                            async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                                response = await client.get(href, headers={
                                    "User-Agent": "Mozilla/5.0",
                                    "Referer": url
                                })
                                if response.status_code == 200:
                                    # Determine extension from URL or content-type
                                    if ".pdf" in href.lower():
                                        ext = ".pdf"
                                    elif ".xlsx" in href.lower():
                                        ext = ".xlsx"
                                    elif ".csv" in href.lower():
                                        ext = ".csv"
                                    elif ".txt" in href.lower():
                                        ext = ".txt"
                                    elif ".docx" in href.lower():
                                        ext = ".docx"
                                    else:
                                        ext = ".dat"

                                    doc_name = f"{req_id}_doc{i}{ext}"
                                    doc_path = OUTPUT_DIR / doc_name
                                    doc_path.write_bytes(response.content)
                                    print(f"      Saved: {doc_name} ({len(response.content)} bytes)")
                        except Exception as e:
                            print(f"      Failed: {e}")

            except Exception as e:
                print(f"Error: {e}")

        await browser.close()

    print(f"\n{'='*60}")
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
