"""
Scrape all 120 Kentucky sheriffs from KACO directory.
"""

import asyncio
import json
import re
from pathlib import Path


async def scrape_ky_sheriffs():
    """Scrape Kentucky sheriffs from KACO."""
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

        print("Loading KACO County Officials Directory...")
        url = 'https://kaco.org/county-information/county-officials-directory/'
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(2000)

        # Select "Sheriff" from position dropdown
        position_select = await page.query_selector('select[name="position"], #position')
        if position_select:
            print("Selecting Sheriff position...")
            await position_select.select_option(label='Sheriff')
            await page.wait_for_timeout(3000)

        # Scroll to load all content
        print("Scrolling to load all results...")
        for _ in range(10):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(500)

        # Get all county/sheriff entries
        content = await page.content()

        # Save raw HTML for debugging
        with open('ky_kaco_raw.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Saved raw HTML to ky_kaco_raw.html")

        # Parse county and sheriff pairs
        # Look for table rows or list items with county/sheriff info
        rows = await page.query_selector_all('tr, .official-item, .county-row, [data-county]')
        print(f"Found {len(rows)} potential entries")

        for row in rows:
            text = await row.inner_text()
            # Look for pattern: County Name ... Sheriff Name
            # KACO format seems to be table with County | Position | Name

            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if len(lines) >= 1:
                # Try to extract county and name
                for line in lines:
                    # Pattern: "Adair Gary Roy" or "Adair\tGary Roy"
                    parts = re.split(r'\t+|\s{2,}', line)
                    if len(parts) >= 2:
                        county = parts[0].strip()
                        name = parts[-1].strip()
                        if county and name and len(county) < 20 and len(name) < 40:
                            if county not in sheriffs:
                                sheriffs[county] = name

        # Also try regex on full content
        text = await page.inner_text('body')

        # Pattern for KACO table: County | Sheriff | Name
        pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+Sheriff\s+([A-Za-z\s\.]+?)(?:\n|$)'
        matches = re.findall(pattern, text)
        for county, name in matches:
            county = county.strip()
            name = name.strip()
            if county and name and len(name) > 2:
                sheriffs[county] = name

        await browser.close()

    print(f"\nTotal sheriffs found: {len(sheriffs)}")
    return sheriffs


async def main():
    sheriffs = await scrape_ky_sheriffs()
    if sheriffs:
        output_path = Path(__file__).parent / "ky_sheriffs_scraped.json"
        with open(output_path, 'w') as f:
            json.dump(sheriffs, f, indent=2)
        print(f"Saved to {output_path}")

        # Print results
        print("\nResults:")
        for county, sheriff in sorted(sheriffs.items()):
            print(f"  {county}: {sheriff}")


if __name__ == "__main__":
    asyncio.run(main())
