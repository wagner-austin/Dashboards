"""
Scrape Pennsylvania sheriffs from Wikipedia list of law enforcement agencies.
"""

import asyncio
import json
import re
from pathlib import Path


async def scrape_wikipedia():
    """Scrape PA sheriffs from Wikipedia."""
    try:
        from playwright.async_api import async_playwright
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return None

    sheriffs = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        )
        page = await context.new_page()

        print("Loading Wikipedia PA law enforcement agencies...")
        url = 'https://en.wikipedia.org/wiki/List_of_law_enforcement_agencies_in_Pennsylvania'
        await page.goto(url, wait_until='networkidle', timeout=60000)

        text = await page.inner_text('body')
        print(f"Page text: {len(text)} chars")

        # Save raw content
        with open('pa_wikipedia_raw.txt', 'w', encoding='utf-8') as f:
            f.write(text)

        # Wikipedia might have county sheriff offices listed
        # Look for patterns in the text
        lines = text.split('\n')
        current_county = None

        for line in lines:
            line = line.strip()
            # Check for county sheriff office line
            match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+County\s+Sheriff', line, re.IGNORECASE)
            if match:
                county = match.group(1)
                print(f"Found: {county} County Sheriff's Office")

        await browser.close()

    return sheriffs


async def main():
    sheriffs = await scrape_wikipedia()
    print(f"\nTotal: {len(sheriffs) if sheriffs else 0}")


if __name__ == "__main__":
    asyncio.run(main())
