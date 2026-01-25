"""
Scrape Pennsylvania sheriffs from PA Sheriffs Association with aggressive stealth.
"""

import asyncio
import json
import re
from pathlib import Path


async def scrape_pa_sheriffs():
    """Scrape PA sheriffs from pasheriffs.org with stealth mode."""
    try:
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return None

    stealth = Stealth(
        navigator_webdriver=True,
        navigator_plugins=True,
        navigator_permissions=True,
        webgl_vendor=True,
        navigator_platform=True,
    )
    sheriffs = {}

    async with async_playwright() as p:
        # Use Chromium with stealth settings
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
        )
        page = await context.new_page()

        print("Loading PA Sheriffs Association directory...")
        try:
            await page.goto('https://pasheriffs.org/sheriffs/', wait_until='networkidle', timeout=60000)
        except Exception as e:
            print(f"First attempt failed: {e}")
            # Try the main page instead
            await page.goto('https://pasheriffs.org/', wait_until='networkidle', timeout=60000)

        await page.wait_for_timeout(5000)

        # Scroll to load all content
        for _ in range(10):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(500)

        # Save raw HTML
        content = await page.content()
        with open('pa_sheriffs_raw.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved raw HTML ({len(content)} chars)")

        # Get all text
        text = await page.inner_text('body')
        print(f"Page text length: {len(text)} chars")

        # Look for county/sheriff patterns in text
        # PA patterns might be: "County Name County Sheriff's Office" followed by "Sheriff: Name"
        # Or table format

        # Check for 403 or blocking
        if '403' in text or 'Forbidden' in text or 'Access Denied' in text:
            print("Site is blocking access")
        else:
            # Try various patterns
            patterns = [
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+County.*?Sheriff[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                r'Sheriff\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+).*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+County',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
                print(f"Pattern found {len(matches)} matches")
                for match in matches:
                    if len(match) == 2:
                        # Determine which is county and which is sheriff
                        if 'County' in match[0]:
                            county = match[0].replace('County', '').strip()
                            sheriff = match[1].strip()
                        else:
                            county = match[1].replace('County', '').strip()
                            sheriff = match[0].strip()

                        if county and sheriff and len(sheriff) > 3:
                            if county not in sheriffs:
                                sheriffs[county] = sheriff

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
    else:
        print("\nNo sheriffs found - try checking pa_sheriffs_raw.html manually")


if __name__ == "__main__":
    asyncio.run(main())
