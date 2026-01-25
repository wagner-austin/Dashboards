"""
Scrape Pennsylvania sheriff election results from PA election returns portal.
This gets the official winners from state election data.
"""

import asyncio
import json
import re
from pathlib import Path


async def scrape_pa_elections():
    """Scrape PA sheriff election results."""
    try:
        from playwright.async_api import async_playwright
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return None

    # Try stealth
    stealth = None
    try:
        from playwright_stealth import Stealth
        stealth = Stealth()
        print("Using playwright-stealth")
    except ImportError:
        print("No stealth mode")

    sheriffs = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
        )
        page = await context.new_page()
        if stealth:
            await stealth.apply_stealth_async(page)

        # Try PA election returns
        print("\nLoading PA Election Returns portal...")
        await page.goto('https://www.electionreturns.pa.gov/', wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(3000)

        # Save screenshot and content
        content = await page.content()
        with open('pa_elections_raw.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved raw HTML ({len(content)} chars)")

        text = await page.inner_text('body')
        print(f"Body text: {len(text)} chars")
        print(f"Sample: {text[:500]}")

        # Look for election year selection
        print("\nLooking for election selector...")

        # Try to find and select 2023 Municipal election (when sheriffs were elected)
        try:
            # Click on any dropdown or selector for election
            selectors = await page.query_selector_all('select, [role="listbox"], .dropdown')
            print(f"Found {len(selectors)} potential selectors")

            # Try clicking on 2023 election if visible
            election_2023 = await page.query_selector('text=2023')
            if election_2023:
                await election_2023.click()
                await page.wait_for_timeout(2000)
                print("Clicked 2023")

            # Look for "Sheriff" option
            sheriff_link = await page.query_selector('text=Sheriff')
            if sheriff_link:
                await sheriff_link.click()
                await page.wait_for_timeout(2000)
                print("Clicked Sheriff")

        except Exception as e:
            print(f"Navigation error: {e}")

        # Get updated content
        text2 = await page.inner_text('body')
        print(f"\nAfter navigation: {len(text2)} chars")

        # Look for county/candidate patterns
        county_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+County'
        counties = re.findall(county_pattern, text2)
        print(f"\nCounties found: {len(set(counties))}")

        # Save for analysis
        with open('pa_elections_text.txt', 'w', encoding='utf-8') as f:
            f.write(text2)

        await browser.close()

    return sheriffs


async def main():
    sheriffs = await scrape_pa_elections()
    print(f"\nTotal sheriffs found: {len(sheriffs) if sheriffs else 0}")


if __name__ == "__main__":
    asyncio.run(main())
