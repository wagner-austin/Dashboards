"""
Scrape Pennsylvania sheriffs from CRIMEWATCH directory using Playwright.
This version visits each county's CRIMEWATCH page to get the sheriff name.
"""

import asyncio
import json
import re
from pathlib import Path


async def scrape_pa_crimewatch():
    """Scrape PA sheriffs from CRIMEWATCH directory."""
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

        print("Loading CRIMEWATCH PA Sheriff Directory...")
        await page.goto('https://www.crimewatchpa.com/directory/sheriff', wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(3000)

        # Scroll to load all content
        for _ in range(10):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(500)

        # Get all links to sheriff agencies
        links = await page.query_selector_all('a[href*="crimewatch"]')
        print(f"Found {len(links)} links")

        sheriff_links = []
        for link in links:
            href = await link.get_attribute('href')
            text = await link.inner_text()
            if href and 'sheriff' in text.lower():
                sheriff_links.append({'text': text, 'href': href})

        print(f"Found {len(sheriff_links)} sheriff links")

        # Also try getting any elements with "Sheriff" in them
        elements = await page.query_selector_all('*')
        sheriff_elements = []
        for el in elements[:1000]:  # Limit to prevent hanging
            try:
                text = await el.inner_text()
                if 'Sheriff' in text and 'County' in text and len(text) < 200:
                    sheriff_elements.append(text)
            except:
                pass

        print(f"Found {len(sheriff_elements)} elements with Sheriff text")

        # Save the full page content
        content = await page.content()
        with open('pa_crimewatch_v2_raw.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved raw HTML ({len(content)} chars)")

        # Try to extract county-sheriff pairs from the page text
        text = await page.inner_text('body')
        print(f"Body text: {len(text)} chars")

        # Look for patterns in directory listings
        # Pattern: "County Name County Sheriff's Office" or similar
        county_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+County\s+Sheriff'
        counties_found = re.findall(county_pattern, text)
        print(f"Counties mentioned: {len(counties_found)}")
        for c in counties_found[:10]:
            print(f"  - {c}")

        # Now visit each sheriff agency page to get the actual sheriff name
        # First, get all the agency card links
        cards = await page.query_selector_all('.agency-card, .directory-listing, [class*="agency"], [class*="listing"]')
        print(f"Found {len(cards)} card elements")

        # Try finding all links that go to individual sheriff pages
        all_links = await page.query_selector_all('a')
        sheriff_page_links = []
        for link in all_links:
            try:
                href = await link.get_attribute('href') or ''
                text = await link.inner_text()
                # Look for county sheriff office links
                if 'crimewatchpa.com' in href and 'sheriff' in href.lower():
                    if href not in [l['href'] for l in sheriff_page_links]:
                        sheriff_page_links.append({'text': text.strip(), 'href': href})
            except:
                pass

        print(f"\nFound {len(sheriff_page_links)} unique sheriff page links:")
        for link in sheriff_page_links[:20]:
            print(f"  {link['text']}: {link['href']}")

        # Visit each sheriff page to extract the sheriff's name
        for i, link_info in enumerate(sheriff_page_links):
            if '/directory/' in link_info['href']:
                continue  # Skip directory links

            county_match = re.search(r'([A-Za-z]+(?:-[A-Za-z]+)?)\s*County', link_info['text'], re.IGNORECASE)
            if not county_match:
                continue

            county = county_match.group(1).title()
            print(f"\n[{i+1}/{len(sheriff_page_links)}] {county} County: {link_info['href']}")

            try:
                new_page = await context.new_page()
                if stealth:
                    await stealth.apply_stealth_async(new_page)

                await new_page.goto(link_info['href'], wait_until='domcontentloaded', timeout=30000)
                await new_page.wait_for_timeout(2000)

                page_text = await new_page.inner_text('body')

                # Look for sheriff name patterns
                patterns = [
                    r'Sheriff[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[SJ]r\.?)?)',
                    r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+),?\s+Sheriff',
                    r'Contact[:\s]*\n*([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)',
                ]

                for pattern in patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        name = match.group(1).strip()
                        # Filter bad matches
                        bad_words = ['office', 'department', 'county', 'sales', 'contact', 'email', 'phone']
                        if not any(w in name.lower() for w in bad_words) and len(name) > 4:
                            sheriffs[county] = name
                            print(f"  Found: {name}")
                            break

                await new_page.close()

            except Exception as e:
                print(f"  Error: {e}")

        await browser.close()

    # Save results
    output_path = Path(__file__).parent / "pa_sheriffs_crimewatch.json"
    with open(output_path, 'w') as f:
        json.dump(sheriffs, f, indent=2)
    print(f"\n\nSaved {len(sheriffs)} sheriffs to {output_path}")

    return sheriffs


async def main():
    sheriffs = await scrape_pa_crimewatch()
    if sheriffs:
        print("\n\nResults:")
        for county, sheriff in sorted(sheriffs.items()):
            print(f"  {county}: {sheriff}")
        print(f"\nTotal: {len(sheriffs)} counties")


if __name__ == "__main__":
    asyncio.run(main())
