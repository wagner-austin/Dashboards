"""
Get ACLU FOIA documents and blog post that names the vendors.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import httpx

OUTPUT_DIR = Path(__file__).parent / "data" / "ice_evidence"


async def download_pdf_with_browser(page, url: str, filename: str):
    """Download a PDF using the browser (handles 403s from direct download)."""
    filepath = OUTPUT_DIR / filename

    # Navigate to the PDF
    await page.goto(url, wait_until="load", timeout=60000)
    await page.wait_for_timeout(2000)

    # Get the PDF content via the browser
    response = await page.evaluate("""async (url) => {
        const response = await fetch(url);
        const blob = await response.blob();
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.readAsDataURL(blob);
        });
    }""", url)

    if response and response.startswith("data:"):
        import base64
        # Extract base64 data
        data = response.split(",")[1]
        filepath.write_bytes(base64.b64decode(data))
        print(f"Downloaded: {filepath}")
        return True
    return False


async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        )
        page = await context.new_page()

        # Get the ACLU blog post with the document analysis
        print("Fetching ACLU blog post...")
        blog_url = "https://www.aclunorcal.org/blog/documents-reveal-ice-using-driver-location-data-local-police-deportations"
        await page.goto(blog_url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)

        await page.screenshot(path=str(OUTPUT_DIR / "aclu_blog_post.png"), full_page=True)

        content = await page.content()
        with open(OUTPUT_DIR / "aclu_blog_post.html", "w", encoding="utf-8") as f:
            f.write(content)

        # Get the text
        body_text = await page.inner_text("body")
        with open(OUTPUT_DIR / "aclu_blog_post.txt", "w", encoding="utf-8") as f:
            f.write(body_text)

        print(f"Blog post saved: {len(body_text)} characters")

        # Find all links to documents
        links = await page.query_selector_all("a")
        doc_links = []
        for link in links:
            href = await link.get_attribute("href")
            text = await link.inner_text()
            if href and (".pdf" in href.lower() or "document" in href.lower() or "record" in href.lower()):
                doc_links.append({"text": text, "url": href})
                print(f"Found doc link: {text} -> {href}")

        # Download the FOIA request PDFs
        pdf_urls = [
            ("https://www.aclunorcal.org/docs/2018.03.19_FOIA_ICE_re_ALPR_contracts.pdf",
             "aclu_foia_request_2018_03_19.pdf"),
            ("https://www.aclunorcal.org/docs/2018.03.21_FOIA_request_to_ICE_re_ALPR_information.pdf",
             "aclu_foia_request_2018_03_21.pdf"),
        ]

        for url, filename in pdf_urls:
            try:
                # Try direct download first
                async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                    response = await client.get(url, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
                    })
                    response.raise_for_status()
                    filepath = OUTPUT_DIR / filename
                    filepath.write_bytes(response.content)
                    print(f"Downloaded: {filepath}")
            except Exception as e:
                print(f"Failed direct download of {url}: {e}")
                # Try via browser
                try:
                    await download_pdf_with_browser(page, url, filename)
                except Exception as e2:
                    print(f"Browser download also failed: {e2}")

        # Also get the June 2019 update blog post
        print("\nFetching June 2019 update...")
        june_url = "https://www.aclunorcal.org/news/records-reveal-ice-agents-run-thousands-license-plate-queries-month-massive-location-database"
        try:
            await page.goto(june_url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(2000)

            await page.screenshot(path=str(OUTPUT_DIR / "aclu_june2019_update.png"), full_page=True)

            content = await page.content()
            with open(OUTPUT_DIR / "aclu_june2019_update.html", "w", encoding="utf-8") as f:
                f.write(content)

            body_text = await page.inner_text("body")
            with open(OUTPUT_DIR / "aclu_june2019_update.txt", "w", encoding="utf-8") as f:
                f.write(body_text)
            print(f"June 2019 update saved: {len(body_text)} characters")
        except Exception as e:
            print(f"Failed to get June 2019 update: {e}")

        await browser.close()

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
