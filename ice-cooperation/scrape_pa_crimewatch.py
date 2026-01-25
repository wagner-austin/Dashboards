"""
Scrape Pennsylvania sheriffs from CRIMEWATCH directory.
"""

import asyncio
import json
import re
from pathlib import Path


async def scrape_pa_sheriffs():
    """Scrape PA sheriffs from CRIMEWATCH."""
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
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
        )
        page = await context.new_page()
        await stealth.apply_stealth_async(page)

        print("Loading CRIMEWATCH PA Sheriff Directory...")
        url = 'https://www.crimewatchpa.com/directory/sheriff'
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(3000)

        # Scroll to load all content
        for _ in range(5):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(1000)

        # Save raw HTML
        content = await page.content()
        with open('pa_crimewatch_raw.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Saved raw HTML to pa_crimewatch_raw.html")

        # Get all text
        text = await page.inner_text('body')
        print(f"Page text length: {len(text)} chars")

        # Look for sheriff entries
        # Pattern variations
        patterns = [
            r'(\w+(?:\s+\w+)?)\s+County\s+Sheriff[\'s]*\s+(?:Office|Department)?.*?Sheriff[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+County.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),?\s+Sheriff',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            for county, name in matches:
                county = county.strip()
                name = name.strip()
                if len(county) < 25 and len(name) > 3 and len(name) < 40:
                    if county not in sheriffs:
                        sheriffs[county] = name

        # Also try looking for directory items
        items = await page.query_selector_all('.directory-item, .sheriff-item, .agency-card, [data-agency]')
        print(f"Found {len(items)} directory items")

        for item in items:
            item_text = await item.inner_text()
            # Parse county and sheriff from item
            if 'County' in item_text and 'Sheriff' in item_text:
                lines = [l.strip() for l in item_text.split('\n') if l.strip()]
                for i, line in enumerate(lines):
                    if 'County' in line:
                        county = line.replace('County', '').replace("Sheriff's Office", '').replace('Sheriff', '').strip()
                        # Look for sheriff name in nearby lines
                        for j in range(max(0, i-2), min(len(lines), i+3)):
                            if lines[j].startswith('Sheriff') or 'Sheriff:' in lines[j]:
                                name = lines[j].replace('Sheriff:', '').replace('Sheriff', '').strip()
                                if name and len(name) > 3:
                                    sheriffs[county] = name
                                    break

        await browser.close()

    print(f"\nTotal sheriffs found: {len(sheriffs)}")
    return sheriffs


async def main():
    sheriffs = await scrape_pa_sheriffs()
    if sheriffs:
        output_path = Path(__file__).parent / "pa_sheriffs_scraped.json"
        with open(output_path, 'w') as f:
            json.dump(sheriffs, f, indent=2)
        print(f"Saved to {output_path}")

        print("\nResults:")
        for county, sheriff in sorted(sheriffs.items()):
            print(f"  {county}: {sheriff}")


if __name__ == "__main__":
    asyncio.run(main())
