"""
Playwright-based scraper for state sheriff association directories.
Uses headless browser to handle JavaScript-rendered sites.

Usage:
    python scrape_sheriffs_playwright.py [state_name]
    python scrape_sheriffs_playwright.py  # Scrape all states
"""

import asyncio
import json
import re
import sys
from pathlib import Path

# State scraping configurations
STATE_CONFIGS = {
    'PENNSYLVANIA': {
        'url': 'https://pasheriffs.org/sheriffs/',
        'method': 'pa_sheriffs',
        'notes': 'Full directory page',
    },
    'WEST_VIRGINIA': {
        'url': 'https://www.wvsheriff.org/?page_id=21',
        'method': 'wv_sheriffs',
        'notes': 'WV Sheriffs directory page',
    },
    'KENTUCKY': {
        'url': 'https://kentuckysheriffs.org/directory-of-sheriffs/',
        'method': 'ky_sheriffs',
        'notes': 'Was updating in January 2026',
    },
    'NORTH_CAROLINA': {
        'url': 'https://ncsheriffs.org/find-a-sheriff',
        'method': 'nc_sheriffs',
        'notes': 'Blocks direct fetch, needs browser',
    },
    'SOUTH_CAROLINA': {
        'url': 'https://www.sheriffsc.org/county_map/',
        'method': 'sc_sheriffs',
        'notes': 'County map with clickable sheriffs',
    },
    'MISSOURI': {
        'url': 'https://mosheriffs.com/',
        'method': 'mo_sheriffs',
        'notes': 'May timeout, look for member directory',
    },
    'WISCONSIN': {
        'url': 'https://www.badgerstatesheriffs.org/',
        'method': 'wi_sheriffs',
        'notes': '72 counties, Wix-based site',
    },
}


async def scrape_with_playwright(state, config):
    """Scrape a state sheriff directory using Playwright with stealth."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright not installed. Run: pip install playwright && playwright install")
        return None

    # Try to use stealth plugin
    stealth = None
    try:
        from playwright_stealth import Stealth
        stealth = Stealth()
    except Exception as e:
        print(f"  Note: stealth mode not available: {e}")

    url = config['url']
    print(f"\nScraping {state} from {url}")

    async with async_playwright() as p:
        # Launch browser with more realistic settings
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,
            java_script_enabled=True,
            locale='en-US',
        )
        page = await context.new_page()

        # Apply stealth if available
        if stealth:
            await stealth.apply_stealth_async(page)

        try:
            # Navigate with timeout
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for dynamic content

            # Get page content
            content = await page.content()

            # Save raw HTML for debugging
            output_dir = Path(__file__).parent
            raw_file = output_dir / f"{state.lower()}_raw_playwright.html"
            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Saved raw HTML to {raw_file}")

            # Parse based on state-specific method
            sheriffs = await parse_sheriffs(page, state, config)

            return sheriffs

        except Exception as e:
            print(f"  Error scraping {state}: {e}")
            return None

        finally:
            await browser.close()


async def parse_sheriffs(page, state, config):
    """Parse sheriff data from page based on state-specific patterns."""
    sheriffs = {}

    # Get raw HTML for regex parsing
    html = await page.content()

    if state == 'PENNSYLVANIA':
        # PA sheriffs - look for table rows or specific patterns
        # Try table first
        elements = await page.query_selector_all('table tr')
        if elements:
            for el in elements:
                text = await el.inner_text()
                if 'County' in text:
                    parts = text.split('\t')
                    if len(parts) >= 2:
                        county = parts[0].replace('County', '').strip()
                        sheriff = parts[1].strip()
                        if county and sheriff:
                            sheriffs[county] = sheriff
        # Fallback: parse text
        if not sheriffs:
            text = await page.inner_text('body')
            # Look for patterns like "County Name: Sheriff Name"
            pattern = r'(\w+(?:\s+\w+)?)\s+County[:\s]+(?:Sheriff\s+)?([A-Za-z][A-Za-z\s\.\-,\']+)'
            matches = re.findall(pattern, text)
            for county, sheriff in matches:
                sheriffs[county.strip()] = sheriff.strip()

    elif state == 'WEST_VIRGINIA':
        # WV sheriffs - format: "County County Sheriff Name<br>"
        # Parse from HTML for accuracy
        pattern = r'<p>(\w+(?:\s+\w+)?)\s+County\s+Sheriff\s+([A-Za-z][A-Za-z\s\.\"\-\(\),\']+?)<br'
        matches = re.findall(pattern, html)
        for county, sheriff in matches:
            # Clean up sheriff name
            sheriff_clean = re.sub(r'\s+', ' ', sheriff.strip())
            # Remove appointment notes
            sheriff_clean = re.sub(r'\s*\(Appointed[^\)]+\)', '', sheriff_clean)
            sheriffs[county.strip()] = sheriff_clean

    elif state == 'KENTUCKY':
        # KY sheriffs - 120 counties
        text = await page.inner_text('body')
        if 'Updating' in text:
            print("  KY directory still updating...")
        # Try to find county/sheriff patterns anyway
        pattern = r'(\w+)\s+County[:\s]+(?:Sheriff\s+)?([A-Za-z][A-Za-z\s\.\-,\']+)'
        matches = re.findall(pattern, text)
        for county, sheriff in matches:
            sheriffs[county.strip()] = sheriff.strip()

    elif state == 'NORTH_CAROLINA':
        # NC sheriffs - 100 counties
        # Try multiple selector strategies
        elements = await page.query_selector_all('.county-item, .sheriff-card, [data-county]')
        for el in elements:
            text = await el.inner_text()
            if 'County' in text:
                parts = [p.strip() for p in text.split('\n') if p.strip()]
                if len(parts) >= 2:
                    county = parts[0].replace('County', '').replace('Sheriff', '').strip()
                    sheriff = parts[1].strip()
                    if county and sheriff and len(sheriff) > 2:
                        sheriffs[county] = sheriff
        # Fallback: text parsing
        if not sheriffs:
            text = await page.inner_text('body')
            pattern = r'(\w+)\s+County\s+Sheriff[:\s]+([A-Za-z][A-Za-z\s\.\-,\']+)'
            matches = re.findall(pattern, text)
            for county, sheriff in matches:
                sheriffs[county.strip()] = sheriff.strip()

    elif state == 'SOUTH_CAROLINA':
        # SC sheriffs - 46 counties
        text = await page.inner_text('body')
        # Look for county patterns
        pattern = r'(\w+)\s+County[:\s]+Sheriff\s+([A-Za-z][A-Za-z\s\.\-,\']+)'
        matches = re.findall(pattern, text)
        for county, sheriff in matches:
            sheriffs[county.strip()] = sheriff.strip()

    elif state == 'MISSOURI':
        # MO sheriffs - 114 counties + St. Louis City
        text = await page.inner_text('body')
        pattern = r'(\w+)\s+County[:\s]+(?:Sheriff\s+)?([A-Za-z][A-Za-z\s\.\-,\']+)'
        matches = re.findall(pattern, text)
        for county, sheriff in matches:
            sheriffs[county.strip()] = sheriff.strip()

    elif state == 'WISCONSIN':
        # WI sheriffs - 72 counties, Wix site
        text = await page.inner_text('body')
        pattern = r'(\w+)\s+County[:\s]+Sheriff\s+([A-Za-z][A-Za-z\s\.\-,\']+)'
        matches = re.findall(pattern, text)
        for county, sheriff in matches:
            sheriffs[county.strip()] = sheriff.strip()

    # Clean up sheriff names - remove phone numbers and other artifacts
    cleaned_sheriffs = {}
    for county, sheriff in sheriffs.items():
        # Remove phone numbers and trailing junk
        sheriff = re.sub(r'\s*Phone.*$', '', sheriff, flags=re.IGNORECASE)
        sheriff = re.sub(r'\s*\d{3}[-\s]\d{3}.*$', '', sheriff)
        sheriff = sheriff.strip()
        if county and sheriff and len(sheriff) > 2:
            cleaned_sheriffs[county] = sheriff

    # If we found sheriffs, print summary
    if cleaned_sheriffs:
        print(f"  Found {len(cleaned_sheriffs)} sheriffs for {state}")
        for county, sheriff in list(cleaned_sheriffs.items())[:5]:
            print(f"    {county}: {sheriff}")
        if len(cleaned_sheriffs) > 5:
            print(f"    ... and {len(cleaned_sheriffs) - 5} more")

    return cleaned_sheriffs


async def scrape_all_states():
    """Scrape all configured states."""
    all_results = {}

    for state, config in STATE_CONFIGS.items():
        print(f"\n{'=' * 60}")
        print(f"Scraping {state}")
        print('=' * 60)

        sheriffs = await scrape_with_playwright(state, config)
        if sheriffs:
            all_results[state] = sheriffs

    return all_results


async def main():
    """Main function."""
    # Check for specific state argument
    if len(sys.argv) > 1:
        state = sys.argv[1].upper().replace(' ', '_')
        if state in STATE_CONFIGS:
            result = await scrape_with_playwright(state, STATE_CONFIGS[state])
            if result:
                print(f"\nResults for {state}:")
                print(json.dumps(result, indent=2))
        else:
            print(f"Unknown state: {state}")
            print(f"Available states: {', '.join(STATE_CONFIGS.keys())}")
    else:
        # Scrape all states
        results = await scrape_all_states()

        # Save results
        output_path = Path(__file__).parent / "scraped_sheriffs.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved all results to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
