#!/usr/bin/env python3
"""Quick Playwright script to fetch a page that blocks direct requests."""
import asyncio
import sys
from playwright.async_api import async_playwright

async def fetch_page(url):
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        )
        page = await context.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            # Get page text
            text = await page.inner_text("body")
            print(text[:5000])  # First 5000 chars

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.cypressca.org/government/city-council"
    asyncio.run(fetch_page(url))
