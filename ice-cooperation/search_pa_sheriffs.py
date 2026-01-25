"""
Compile PA sheriff names by searching for each county individually.
Uses web search to find current sheriff for each of PA's 67 counties.
"""

import asyncio
import json
import re
from pathlib import Path


# All 67 PA counties
PA_COUNTIES = [
    'Adams', 'Allegheny', 'Armstrong', 'Beaver', 'Bedford', 'Berks', 'Blair',
    'Bradford', 'Bucks', 'Butler', 'Cambria', 'Cameron', 'Carbon', 'Centre',
    'Chester', 'Clarion', 'Clearfield', 'Clinton', 'Columbia', 'Crawford',
    'Cumberland', 'Dauphin', 'Delaware', 'Elk', 'Erie', 'Fayette', 'Forest',
    'Franklin', 'Fulton', 'Greene', 'Huntingdon', 'Indiana', 'Jefferson',
    'Juniata', 'Lackawanna', 'Lancaster', 'Lawrence', 'Lebanon', 'Lehigh',
    'Luzerne', 'Lycoming', 'McKean', 'Mercer', 'Mifflin', 'Monroe', 'Montgomery',
    'Montour', 'Northampton', 'Northumberland', 'Perry', 'Philadelphia', 'Pike',
    'Potter', 'Schuylkill', 'Snyder', 'Somerset', 'Sullivan', 'Susquehanna',
    'Tioga', 'Union', 'Venango', 'Warren', 'Washington', 'Wayne', 'Westmoreland',
    'Wyoming', 'York'
]


async def search_sheriff(page, county):
    """Search for sheriff of a specific county."""
    try:
        query = f'"{county} County Pennsylvania" sheriff 2024 2025'
        search_url = f'https://www.bing.com/search?q={query.replace(" ", "+")}'

        await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(2000)

        text = await page.inner_text('body')

        # Look for sheriff name patterns
        patterns = [
            rf'Sheriff\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[SJ]r\.?)?)',
            rf'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[SJ]r\.?)?),?\s+(?:is|serves?\s+as)?\s*(?:the)?\s*Sheriff',
            rf'{county}\s+County\s+Sheriff\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.strip()
                # Filter out bad matches
                bad_words = ['office', 'department', 'county', 'sales', 'contact', 'the', 'pennsylvania', 'pa']
                if not any(w in name.lower() for w in bad_words) and len(name) > 4 and len(name) < 35:
                    return name

        return None

    except Exception as e:
        print(f"  Error: {e}")
        return None


async def search_all_sheriffs():
    """Search for all PA county sheriffs."""
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

        for i, county in enumerate(PA_COUNTIES):
            print(f"[{i+1}/67] {county} County...")
            name = await search_sheriff(page, county)
            if name:
                sheriffs[county] = name
                print(f"  Found: {name}")
            else:
                print(f"  Not found")

            # Add delay to avoid rate limiting
            await page.wait_for_timeout(1000)

        await browser.close()

    # Save results
    output_path = Path(__file__).parent / "pa_sheriffs_searched.json"
    with open(output_path, 'w') as f:
        json.dump(sheriffs, f, indent=2)
    print(f"\n\nSaved {len(sheriffs)} sheriffs to {output_path}")

    return sheriffs


async def main():
    sheriffs = await search_all_sheriffs()
    if sheriffs:
        print("\n\nResults:")
        for county, sheriff in sorted(sheriffs.items()):
            print(f"  {county}: {sheriff}")
        print(f"\nTotal: {len(sheriffs)}/67 counties")


if __name__ == "__main__":
    asyncio.run(main())
