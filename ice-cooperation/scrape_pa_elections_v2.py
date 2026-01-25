"""
Scrape Pennsylvania sheriff election results from PA election returns portal.
Navigate to 2023 Municipal election > Sheriff results.
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
            headless=False,  # Try non-headless to see what's happening
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
        )
        page = await context.new_page()
        if stealth:
            await stealth.apply_stealth_async(page)

        # Go directly to 2023 Municipal elections
        print("\nLoading PA 2023 Municipal Election results...")
        url = 'https://www.electionreturns.pa.gov/Home/SummaryResults?ElectionID=106&ElectionType=M&IsActive=0'
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(5000)

        text = await page.inner_text('body')
        print(f"Body text: {len(text)} chars")

        # Click on "Offices" to see list of offices
        try:
            offices_link = await page.query_selector('text=Offices')
            if offices_link:
                await offices_link.click()
                await page.wait_for_timeout(3000)
                print("Clicked Offices link")
        except Exception as e:
            print(f"Offices click error: {e}")

        # Look for Sheriff in the page
        text = await page.inner_text('body')
        if 'Sheriff' in text:
            print("Sheriff found in page text!")

        # Try direct URL for sheriff results
        print("\nTrying direct sheriff results URL...")
        sheriff_url = 'https://www.electionreturns.pa.gov/Home/CountyBreakDownResults?officeId=35&districtId=0&ElectionID=106&ElectionType=M&IsActive=0'
        await page.goto(sheriff_url, wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(5000)

        text = await page.inner_text('body')
        print(f"Sheriff results text: {len(text)} chars")
        print(f"Sample: {text[:1000]}")

        # Save content
        with open('pa_sheriff_elections.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Saved to pa_sheriff_elections.txt")

        # Parse county/winner pairs
        # Look for patterns like "County Name" followed by candidate names and vote counts
        lines = text.split('\n')
        current_county = None
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check if this is a county header
            county_match = re.match(r'^([A-Z][A-Za-z]+(?:\s+[A-Z][a-z]+)?)\s*$', line)
            if county_match and len(line) < 25:
                current_county = county_match.group(1)
                continue

            # Check if this looks like a winner (name with vote count)
            if current_county:
                # Pattern: "Name LastName 12,345 (65%)" or similar
                winner_match = re.search(r'^([A-Z][A-Za-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][A-Za-z]+(?:\s+[SJ]r\.?)?)\s+[\d,]+', line)
                if winner_match:
                    name = winner_match.group(1)
                    if current_county not in sheriffs:
                        sheriffs[current_county] = name
                        print(f"  {current_county}: {name}")
                    current_county = None  # Reset after finding winner

        await browser.close()

    # Save results
    output_path = Path(__file__).parent / "pa_sheriffs_elections.json"
    with open(output_path, 'w') as f:
        json.dump(sheriffs, f, indent=2)
    print(f"\n\nSaved {len(sheriffs)} sheriffs to {output_path}")

    return sheriffs


async def main():
    sheriffs = await scrape_pa_elections()
    if sheriffs:
        print("\n\nResults:")
        for county, sheriff in sorted(sheriffs.items()):
            print(f"  {county}: {sheriff}")
        print(f"\nTotal: {len(sheriffs)} counties")


if __name__ == "__main__":
    asyncio.run(main())
