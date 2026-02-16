"""
Playwright-based scraper for ALPR data sources.
Uses stealth mode to bypass Cloudflare protection.

Targets:
- deflock.me - Crowdsourced ALPR camera locations
- eyesonflock.com - Flock Safety transparency portal aggregator
- Flock transparency portals directly

Usage:
    python scrape_alpr_data.py [target]
    python scrape_alpr_data.py deflock
    python scrape_alpr_data.py eyesonflock
    python scrape_alpr_data.py flock-portals
    python scrape_alpr_data.py all
"""

import asyncio
import json
import csv
import re
import sys
from pathlib import Path
from datetime import datetime

# Target configurations
TARGETS = {
    'deflock': {
        'url': 'https://deflock.me/',
        'method': 'scrape_deflock',
        'description': 'Crowdsourced ALPR camera map',
    },
    'deflock_oc': {
        'url': 'https://deflock.me/?lat=33.7175&lng=-117.8311&zoom=10',  # Orange County center
        'method': 'scrape_deflock',
        'description': 'DeFlock Orange County area',
    },
    'eyesonflock': {
        'url': 'https://eyesonflock.com/',
        'method': 'scrape_eyesonflock',
        'description': 'Flock transparency portal aggregator',
    },
    'flock_buena_park': {
        'url': 'https://transparency.flocksafety.com/buena-park-ca-pd',
        'method': 'scrape_flock_portal',
        'description': 'Buena Park PD Flock Portal',
    },
    'flock_costa_mesa': {
        'url': 'https://transparency.flocksafety.com/costa-mesa-ca-pd',
        'method': 'scrape_flock_portal',
        'description': 'Costa Mesa PD Flock Portal',
    },
    'flock_newport_beach': {
        'url': 'https://transparency.flocksafety.com/newport-beach-pd-ca',
        'method': 'scrape_flock_portal',
        'description': 'Newport Beach PD Flock Portal',
    },
}

# Orange County cities to search for
OC_CITIES = [
    'Irvine', 'Anaheim', 'Santa Ana', 'Huntington Beach', 'Costa Mesa',
    'Newport Beach', 'Fullerton', 'Orange', 'Garden Grove', 'Buena Park',
    'Mission Viejo', 'Laguna Niguel', 'Lake Forest', 'Tustin', 'Yorba Linda',
    'San Clemente', 'Laguna Beach', 'Dana Point', 'Stanton', 'Seal Beach',
    'Westminster', 'Fountain Valley', 'La Habra', 'Brea', 'Placentia',
    'Cypress', 'La Palma', 'Los Alamitos', 'Laguna Hills', 'Aliso Viejo',
    'Rancho Santa Margarita', 'San Juan Capistrano', 'Laguna Woods', 'Villa Park'
]


async def create_stealth_browser():
    """Create a stealth browser instance."""
    from playwright.async_api import async_playwright

    # Try to import stealth
    stealth = None
    try:
        from playwright_stealth import Stealth
        stealth = Stealth()
        print("  [+] Stealth mode enabled")
    except ImportError:
        print("  [-] playwright_stealth not available, using standard mode")

    playwright = await async_playwright().start()

    # Use Firefox for better stealth (as user mentioned they have Firefox stealth)
    browser = await playwright.firefox.launch(
        headless=True,
        firefox_user_prefs={
            'dom.webdriver.enabled': False,
            'useAutomationExtension': False,
        }
    )

    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        viewport={'width': 1920, 'height': 1080},
        locale='en-US',
        timezone_id='America/Los_Angeles',
    )

    page = await context.new_page()

    # Apply stealth if available
    if stealth:
        await stealth.apply_stealth_async(page)

    return playwright, browser, context, page


async def wait_for_cloudflare(page, timeout=30000):
    """Wait for Cloudflare challenge to complete."""
    try:
        # Check if we're on a Cloudflare challenge page
        content = await page.content()
        if 'challenge-platform' in content or 'cf-browser-verification' in content:
            print("  [*] Cloudflare challenge detected, waiting...")
            # Wait for redirect or content change
            await page.wait_for_function(
                "!document.body.innerHTML.includes('challenge-platform')",
                timeout=timeout
            )
            await page.wait_for_timeout(2000)
            print("  [+] Cloudflare challenge passed")
    except Exception as e:
        print(f"  [!] Cloudflare wait error: {e}")


async def scrape_deflock(page, url):
    """Scrape DeFlock camera map data."""
    print(f"\n[*] Scraping DeFlock: {url}")

    try:
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await wait_for_cloudflare(page)
        await page.wait_for_timeout(3000)

        # Save screenshot for debugging
        output_dir = Path(__file__).parent / 'data'
        output_dir.mkdir(exist_ok=True)
        await page.screenshot(path=str(output_dir / 'deflock_screenshot.png'))
        print(f"  [+] Screenshot saved to {output_dir / 'deflock_screenshot.png'}")

        # Save HTML for analysis
        html = await page.content()
        with open(output_dir / 'deflock_raw.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  [+] HTML saved to {output_dir / 'deflock_raw.html'}")

        # Try to extract map data
        # DeFlock uses a map interface - we need to find camera markers
        cameras = []

        # Look for map markers or data in the page
        # Try to find any JSON data embedded in the page
        scripts = await page.query_selector_all('script')
        for script in scripts:
            content = await script.inner_text()
            # Look for coordinate patterns or camera data
            if 'lat' in content.lower() and 'lng' in content.lower():
                # Try to extract JSON objects
                json_matches = re.findall(r'\{[^{}]*"lat"[^{}]*"lng"[^{}]*\}', content)
                for match in json_matches:
                    try:
                        data = json.loads(match)
                        cameras.append(data)
                    except:
                        pass

        # Try to interact with the map to get data
        # Look for any API calls in network requests
        await page.evaluate('''() => {
            // Try to trigger any data loading
            window.scrollTo(0, document.body.scrollHeight);
        }''')
        await page.wait_for_timeout(2000)

        # Extract any visible camera info from the page
        text = await page.inner_text('body')

        # Look for Orange County mentions
        oc_mentions = []
        for city in OC_CITIES:
            if city.lower() in text.lower():
                oc_mentions.append(city)

        result = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'cameras_found': len(cameras),
            'cameras': cameras[:50],  # Limit for now
            'oc_cities_mentioned': oc_mentions,
            'page_text_preview': text[:2000] if text else None
        }

        print(f"  [+] Found {len(cameras)} camera entries")
        print(f"  [+] OC cities mentioned: {oc_mentions}")

        return result

    except Exception as e:
        print(f"  [!] Error scraping DeFlock: {e}")
        return {'error': str(e), 'url': url}


async def scrape_eyesonflock(page, url):
    """Scrape Eyes on Flock aggregator."""
    print(f"\n[*] Scraping Eyes on Flock: {url}")

    try:
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await wait_for_cloudflare(page)
        await page.wait_for_timeout(3000)

        output_dir = Path(__file__).parent / 'data'
        output_dir.mkdir(exist_ok=True)

        # Save screenshot
        await page.screenshot(path=str(output_dir / 'eyesonflock_screenshot.png'))
        print(f"  [+] Screenshot saved")

        # Save HTML
        html = await page.content()
        with open(output_dir / 'eyesonflock_raw.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  [+] HTML saved")

        # Try to extract agency data
        agencies = []

        # Look for tables or lists of agencies
        tables = await page.query_selector_all('table')
        for table in tables:
            rows = await table.query_selector_all('tr')
            for row in rows:
                cells = await row.query_selector_all('td, th')
                row_data = []
                for cell in cells:
                    text = await cell.inner_text()
                    row_data.append(text.strip())
                if row_data:
                    agencies.append(row_data)

        # Look for any links to agency portals
        links = await page.query_selector_all('a[href*="transparency.flocksafety.com"]')
        portal_links = []
        for link in links:
            href = await link.get_attribute('href')
            text = await link.inner_text()
            portal_links.append({'url': href, 'text': text})

        # Extract any statistics
        text = await page.inner_text('body')

        # Look for numbers that might be statistics
        stats = re.findall(r'(\d{1,3}(?:,\d{3})*)\s*(cameras?|agencies?|departments?|searches?)', text, re.I)

        result = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'agencies_found': len(agencies),
            'agencies': agencies[:100],
            'portal_links': portal_links,
            'statistics': stats,
            'page_text_preview': text[:3000] if text else None
        }

        print(f"  [+] Found {len(agencies)} agency entries")
        print(f"  [+] Found {len(portal_links)} portal links")

        return result

    except Exception as e:
        print(f"  [!] Error scraping Eyes on Flock: {e}")
        return {'error': str(e), 'url': url}


async def scrape_flock_portal(page, url):
    """Scrape an individual Flock Safety transparency portal."""
    print(f"\n[*] Scraping Flock Portal: {url}")

    try:
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(3000)

        output_dir = Path(__file__).parent / 'data'
        output_dir.mkdir(exist_ok=True)

        # Get agency name from URL
        agency_slug = url.split('/')[-1]

        # Save screenshot
        await page.screenshot(path=str(output_dir / f'flock_{agency_slug}_screenshot.png'))
        print(f"  [+] Screenshot saved")

        # Save HTML
        html = await page.content()
        with open(output_dir / f'flock_{agency_slug}_raw.html', 'w', encoding='utf-8') as f:
            f.write(html)

        # Extract data from the portal
        result = {
            'url': url,
            'agency_slug': agency_slug,
            'timestamp': datetime.now().isoformat(),
        }

        # Look for policy information
        policy_sections = await page.query_selector_all('[class*="policy"], [class*="Policy"]')
        policies = []
        for section in policy_sections:
            text = await section.inner_text()
            policies.append(text[:500])
        result['policies'] = policies

        # Look for statistics
        stat_elements = await page.query_selector_all('[class*="stat"], [class*="Stat"], [class*="metric"], [class*="Metric"]')
        stats = []
        for elem in stat_elements:
            text = await elem.inner_text()
            stats.append(text)
        result['statistics'] = stats

        # Look for usage/prohibited uses
        text = await page.inner_text('body')

        # Extract prohibited uses (common in Flock portals)
        prohibited_patterns = [
            r'prohibited.*?(?:use|purpose)s?[:\s]*(.*?)(?:\.|$)',
            r'will not.*?(?:use|access).*?for[:\s]*(.*?)(?:\.|$)',
        ]
        prohibited_uses = []
        for pattern in prohibited_patterns:
            matches = re.findall(pattern, text, re.I | re.S)
            prohibited_uses.extend(matches)
        result['prohibited_uses'] = prohibited_uses[:10]

        # Extract retention period
        retention_match = re.search(r'(\d+)\s*(days?|months?|years?)\s*(?:retention|stored|kept)', text, re.I)
        if retention_match:
            result['retention_period'] = f"{retention_match.group(1)} {retention_match.group(2)}"

        # Extract camera count if mentioned
        camera_match = re.search(r'(\d+)\s*(?:cameras?|devices?|readers?)', text, re.I)
        if camera_match:
            result['camera_count'] = int(camera_match.group(1))

        result['page_text'] = text[:5000]

        print(f"  [+] Extracted data for {agency_slug}")
        if 'retention_period' in result:
            print(f"  [+] Retention: {result['retention_period']}")
        if 'camera_count' in result:
            print(f"  [+] Cameras: {result['camera_count']}")

        return result

    except Exception as e:
        print(f"  [!] Error scraping Flock portal: {e}")
        return {'error': str(e), 'url': url}


async def scrape_all_oc_flock_portals(page):
    """Scrape all known Orange County Flock transparency portals."""
    oc_portals = [
        'buena-park-ca-pd',
        'costa-mesa-ca-pd',
        'newport-beach-pd-ca',
        'fountain-valley-ca-pd',
        'westminster-ca-pd',
        # Santa Ana uses Motorola but may have Flock too
        # Add more as discovered
    ]

    results = []
    for portal in oc_portals:
        url = f'https://transparency.flocksafety.com/{portal}'
        result = await scrape_flock_portal(page, url)
        results.append(result)
        await page.wait_for_timeout(2000)  # Be nice to servers

    return results


async def main(targets=None):
    """Main scraping function."""
    print("=" * 60)
    print("ALPR Data Scraper - Orange County Focus")
    print("=" * 60)

    if targets is None:
        targets = ['deflock', 'eyesonflock']

    playwright, browser, context, page = await create_stealth_browser()

    try:
        all_results = {}

        for target in targets:
            if target == 'all':
                # Scrape everything
                for name, config in TARGETS.items():
                    method = globals()[config['method']]
                    result = await method(page, config['url'])
                    all_results[name] = result
                    await page.wait_for_timeout(2000)
            elif target == 'flock-portals':
                # Scrape all OC Flock portals
                results = await scrape_all_oc_flock_portals(page)
                all_results['flock_portals'] = results
            elif target in TARGETS:
                config = TARGETS[target]
                method = globals()[config['method']]
                result = await method(page, config['url'])
                all_results[target] = result
            else:
                print(f"Unknown target: {target}")

        # Save combined results
        output_dir = Path(__file__).parent / 'data'
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / f'scraped_alpr_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, default=str)

        print(f"\n{'=' * 60}")
        print(f"Results saved to: {output_file}")
        print(f"{'=' * 60}")

        return all_results

    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else ['deflock', 'eyesonflock', 'flock-portals']
    asyncio.run(main(targets))
