"""
Scrape North Carolina sheriffs by clicking through the interactive map.
Each county on the map reveals the sheriff's name when clicked.
"""

import asyncio
import json
import re
from pathlib import Path


NC_COUNTIES = [
    'Alamance', 'Alexander', 'Alleghany', 'Anson', 'Ashe', 'Avery', 'Beaufort', 'Bertie',
    'Bladen', 'Brunswick', 'Buncombe', 'Burke', 'Cabarrus', 'Caldwell', 'Camden', 'Carteret',
    'Caswell', 'Catawba', 'Chatham', 'Cherokee', 'Chowan', 'Clay', 'Cleveland', 'Columbus',
    'Craven', 'Cumberland', 'Currituck', 'Dare', 'Davidson', 'Davie', 'Duplin', 'Durham',
    'Edgecombe', 'Forsyth', 'Franklin', 'Gaston', 'Gates', 'Graham', 'Granville', 'Greene',
    'Guilford', 'Halifax', 'Harnett', 'Haywood', 'Henderson', 'Hertford', 'Hoke', 'Hyde',
    'Iredell', 'Jackson', 'Johnston', 'Jones', 'Lee', 'Lenoir', 'Lincoln', 'Macon',
    'Madison', 'Martin', 'McDowell', 'Mecklenburg', 'Mitchell', 'Montgomery', 'Moore', 'Nash',
    'New Hanover', 'Northampton', 'Onslow', 'Orange', 'Pamlico', 'Pasquotank', 'Pender',
    'Perquimans', 'Person', 'Pitt', 'Polk', 'Randolph', 'Richmond', 'Robeson', 'Rockingham',
    'Rowan', 'Rutherford', 'Sampson', 'Scotland', 'Stanly', 'Stokes', 'Surry', 'Swain',
    'Transylvania', 'Tyrrell', 'Union', 'Vance', 'Wake', 'Warren', 'Washington', 'Watauga',
    'Wayne', 'Wilkes', 'Wilson', 'Yadkin', 'Yancey'
]


async def scrape_nc_sheriffs():
    """Click through NC interactive map to get all sheriffs."""
    try:
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return None

    stealth = Stealth()
    sheriffs = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
        )
        page = await context.new_page()
        await stealth.apply_stealth_async(page)

        print("Loading NC Sheriffs page...")
        await page.goto('https://ncsheriffs.org/find-a-sheriff', wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(3000)

        # Try to find county select dropdown
        select = await page.query_selector('select#countySelect, select[name="county"]')
        if select:
            print("Found county dropdown, iterating through options...")
            options = await select.query_selector_all('option')

            for option in options:
                value = await option.get_attribute('value')
                text = await option.inner_text()

                if value and value != '0' and text.strip():
                    county = text.strip()
                    print(f"  Selecting {county}...")

                    await select.select_option(value=value)
                    await page.wait_for_timeout(1500)

                    # Look for sheriff info that appears
                    content = await page.inner_text('body')

                    # Try to find sheriff name pattern
                    patterns = [
                        rf'{county}.*?Sheriff[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                        rf'Sheriff[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                        rf'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),?\s+Sheriff',
                    ]

                    for pattern in patterns:
                        match = re.search(pattern, content)
                        if match:
                            sheriff_name = match.group(1).strip()
                            if len(sheriff_name) > 3 and len(sheriff_name) < 50:
                                sheriffs[county] = sheriff_name
                                print(f"    Found: {sheriff_name}")
                                break
        else:
            print("No dropdown found, trying to click on map paths...")
            # Try clicking on SVG path elements (county shapes)
            paths = await page.query_selector_all('path[id], path[aria-label*="County"]')
            print(f"Found {len(paths)} clickable county paths")

            for path in paths[:10]:  # Test with first 10
                county_id = await path.get_attribute('id')
                aria = await path.get_attribute('aria-label')
                county_name = aria.replace(' County', '') if aria else county_id

                if county_name:
                    print(f"  Clicking {county_name}...")
                    try:
                        await path.click()
                        await page.wait_for_timeout(1500)

                        # Look for popup/modal with sheriff info
                        content = await page.inner_text('body')

                        # Save sample for debugging
                        if len(sheriffs) == 0:
                            with open('nc_sample_content.txt', 'w') as f:
                                f.write(content)

                        # Try to extract sheriff name
                        match = re.search(r'Sheriff[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', content)
                        if match:
                            sheriffs[county_name] = match.group(1)
                            print(f"    Found: {match.group(1)}")
                    except Exception as e:
                        print(f"    Error clicking: {e}")

        await browser.close()

    print(f"\nTotal sheriffs found: {len(sheriffs)}")
    return sheriffs


async def main():
    sheriffs = await scrape_nc_sheriffs()
    if sheriffs:
        output_path = Path(__file__).parent / "nc_sheriffs_scraped.json"
        with open(output_path, 'w') as f:
            json.dump(sheriffs, f, indent=2)
        print(f"Saved to {output_path}")

        # Print results
        print("\nResults:")
        for county, sheriff in sorted(sheriffs.items()):
            print(f"  {county}: {sheriff}")


if __name__ == "__main__":
    asyncio.run(main())
