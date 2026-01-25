"""
Scrape NC sheriffs by intercepting network requests.
"""

import asyncio
import json
from pathlib import Path


async def scrape_nc_with_network():
    """Intercept network requests to find sheriff data API."""
    try:
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return None

    stealth = Stealth()
    captured_responses = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
        )
        page = await context.new_page()
        await stealth.apply_stealth_async(page)

        # Capture network responses
        async def handle_response(response):
            url = response.url
            if any(x in url.lower() for x in ['sheriff', 'county', 'api', 'json', 'data']):
                try:
                    body = await response.text()
                    captured_responses.append({
                        'url': url,
                        'status': response.status,
                        'body': body[:2000]  # First 2000 chars
                    })
                    print(f"  Captured: {url}")
                except:
                    pass

        page.on('response', handle_response)

        print("Loading NC Sheriffs page and capturing network requests...")
        await page.goto('https://ncsheriffs.org/find-a-sheriff', wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(3000)

        # Select a few counties to trigger data loading
        select = await page.query_selector('select#countySelect')
        if select:
            options = await select.query_selector_all('option')
            for option in options[:5]:  # Test first 5 counties
                value = await option.get_attribute('value')
                text = await option.inner_text()
                if value and value != '0':
                    print(f"Selecting {text}...")
                    await select.select_option(value=value)
                    await page.wait_for_timeout(2000)

        await browser.close()

    # Save captured responses
    output_path = Path(__file__).parent / "nc_network_captures.json"
    with open(output_path, 'w') as f:
        json.dump(captured_responses, f, indent=2)
    print(f"\nSaved {len(captured_responses)} captured responses to {output_path}")

    # Print captures
    for resp in captured_responses:
        print(f"\n--- {resp['url']} ---")
        print(resp['body'][:500])


async def main():
    await scrape_nc_with_network()


if __name__ == "__main__":
    asyncio.run(main())
