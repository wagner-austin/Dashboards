"""
Scrape Pennsylvania sheriffs from individual county websites using Playwright.
PA has 67 counties - we'll visit each county's official sheriff page.
"""

import asyncio
import json
import re
from pathlib import Path

# PA County Sheriff websites - official county government pages
PA_COUNTY_URLS = {
    'Adams': 'https://www.adamscountypa.gov/departments/sheriff/',
    'Allegheny': 'https://www.alleghenycounty.us/sheriff/',
    'Armstrong': 'https://www.co.armstrong.pa.us/index.php/county-departments-a-to-l/sheriff',
    'Beaver': 'https://www.beavercountypa.gov/Departments/Sheriff',
    'Bedford': 'https://www.bedfordcountypa.org/sheriff.html',
    'Berks': 'https://www.countyofberks.com/departments/sheriff',
    'Blair': 'https://www.blaircountypa.gov/sheriff/',
    'Bradford': 'https://www.bradfordcountypa.org/sheriff.html',
    'Bucks': 'https://www.buckscounty.gov/government/RowOfficers/Sheriff/',
    'Butler': 'https://www.butlercountypa.gov/179/Sheriff',
    'Cambria': 'https://www.co.cambria.pa.us/departments/sheriff/',
    'Cameron': 'https://www.cameroncountypa.com/sheriff.html',
    'Carbon': 'https://www.carboncounty.com/index.php/sheriff',
    'Centre': 'https://centrecountypa.gov/401/Sheriff',
    'Chester': 'https://www.chesco.org/174/Sheriff',
    'Clarion': 'https://www.co.clarion.pa.us/departments/sheriff/',
    'Clearfield': 'https://www.clearfieldco.org/sheriff/',
    'Clinton': 'https://www.clintoncountypa.com/sheriff',
    'Columbia': 'https://www.columbiapa.org/sheriff/',
    'Crawford': 'https://www.crawfordcountypa.net/Sheriff/',
    'Cumberland': 'https://www.ccpa.net/259/Sheriff',
    'Dauphin': 'https://www.dauphincounty.gov/government/row-offices/sheriff/',
    'Delaware': 'https://www.delcopa.gov/sheriff/',
    'Elk': 'https://www.co.elk.pa.us/sheriff/',
    'Erie': 'https://eriecountypa.gov/departments/sheriff/',
    'Fayette': 'https://www.fayettecountypa.org/185/Sheriff',
    'Forest': 'https://www.co.forest.pa.us/sheriff.html',
    'Franklin': 'https://www.franklincountypa.gov/index.php?section=sheriff',
    'Fulton': 'https://www.fultoncountypa.gov/sheriff/',
    'Greene': 'https://www.co.greene.pa.us/departments/sheriff/',
    'Huntingdon': 'https://www.huntingdoncounty.net/sheriff/',
    'Indiana': 'https://www.indianacountypa.gov/departments/sheriff/',
    'Jefferson': 'https://jeffersoncountypa.com/departments/sheriff/',
    'Juniata': 'https://www.juniataco.org/sheriff/',
    'Lackawanna': 'https://www.lackawannacounty.org/sheriff/',
    'Lancaster': 'https://lancastercountypa.gov/1491/Sheriffs-Office',
    'Lawrence': 'https://lawrencecountypa.gov/gov/sheriff/',
    'Lebanon': 'https://www.lebcounty.org/depts/sheriff/',
    'Lehigh': 'https://www.lehighcounty.org/Departments/Sheriff',
    'Luzerne': 'https://www.luzernecounty.org/319/Sheriff',
    'Lycoming': 'https://www.lyco.org/Departments/Sheriff',
    'McKean': 'https://www.mckeancountypa.org/sheriff/',
    'Mercer': 'https://www.mcc.co.mercer.pa.us/sheriff/',
    'Mifflin': 'https://www.co.mifflin.pa.us/sheriff/',
    'Monroe': 'https://www.monroecountypa.gov/departments/sheriff/',
    'Montgomery': 'https://www.montgomerycountypa.gov/397/Sheriffs-Office',
    'Montour': 'https://www.montourco.org/sheriff/',
    'Northampton': 'https://www.northamptoncounty.org/SHERIFF/',
    'Northumberland': 'https://www.norrycopa.net/row-offices/sheriff/',
    'Perry': 'https://www.perryco.org/sheriff/',
    'Philadelphia': 'https://www.phila.gov/departments/sheriff/',
    'Pike': 'https://www.pikepa.org/sheriff/',
    'Potter': 'https://www.pottercountypa.net/sheriff/',
    'Schuylkill': 'https://www.co.schuylkill.pa.us/Offices/Sheriff/',
    'Snyder': 'https://www.snydercounty.org/departments/sheriff/',
    'Somerset': 'https://www.co.somerset.pa.us/sheriff/',
    'Sullivan': 'https://www.sullivancounty-pa.us/sheriff/',
    'Susquehanna': 'https://www.susqco.com/sheriff/',
    'Tioga': 'https://www.tiogacountypa.us/Departments/Sheriff/',
    'Union': 'https://www.unionco.org/sheriff/',
    'Venango': 'https://www.venangocountypa.gov/268/County-Sheriff',
    'Warren': 'https://www.warrencountypa.net/sheriff/',
    'Washington': 'https://www.washingtoncountypa.gov/sheriff/',
    'Wayne': 'https://www.waynecountypa.gov/174/Sheriff',
    'Westmoreland': 'https://www.co.westmoreland.pa.us/260/Sheriff',
    'Wyoming': 'https://wycopa.org/sheriff/',
    'York': 'https://yorkcountypa.gov/sheriff/',
}


async def extract_sheriff_name(page, county):
    """Extract sheriff name from page using various patterns."""
    text = await page.inner_text('body')

    # Common patterns for sheriff names on county websites
    patterns = [
        # "Sheriff John Smith" or "Sheriff: John Smith"
        r'Sheriff[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[SJ]r\.?)?)',
        # "John Smith, Sheriff"
        r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[SJ]r\.?)?),?\s+Sheriff',
        # "The Honorable John Smith"
        r'(?:The\s+)?Honorable\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)',
        # Title patterns like "Sheriff\nJohn Smith"
        r'Sheriff\s*\n\s*([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            # Filter out generic words
            if name.lower() not in ['the sheriff', 'county sheriff', 'office of']:
                if len(name) > 4 and len(name) < 40:
                    return name

    # Also try looking at page title or h1/h2
    try:
        title = await page.title()
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1).strip()
    except:
        pass

    return None


async def scrape_pa_counties():
    """Scrape all PA county sheriff websites."""
    try:
        from playwright.async_api import async_playwright
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return None

    # Try to import stealth
    stealth = None
    try:
        from playwright_stealth import Stealth
        stealth = Stealth()
        print("Using playwright-stealth for anti-detection")
    except ImportError:
        print("playwright-stealth not available, proceeding without it")

    sheriffs = {}
    failed = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
        )

        for county, url in PA_COUNTY_URLS.items():
            print(f"\n{county} County: {url}")
            page = await context.new_page()

            if stealth:
                await stealth.apply_stealth_async(page)

            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(2000)

                # Scroll a bit to trigger lazy loading
                await page.evaluate('window.scrollTo(0, 500)')
                await page.wait_for_timeout(1000)

                sheriff = await extract_sheriff_name(page, county)

                if sheriff:
                    sheriffs[county] = sheriff
                    print(f"  Found: {sheriff}")
                else:
                    # Save page content for manual review
                    content = await page.inner_text('body')
                    failed.append({'county': county, 'url': url, 'sample': content[:500]})
                    print(f"  Could not extract name automatically")

            except Exception as e:
                print(f"  Error: {e}")
                failed.append({'county': county, 'url': url, 'error': str(e)})

            await page.close()

        await browser.close()

    # Save results
    output_path = Path(__file__).parent / "pa_sheriffs_scraped.json"
    with open(output_path, 'w') as f:
        json.dump(sheriffs, f, indent=2)
    print(f"\n\nSaved {len(sheriffs)} sheriffs to {output_path}")

    # Save failed for review
    if failed:
        failed_path = Path(__file__).parent / "pa_sheriffs_failed.json"
        with open(failed_path, 'w') as f:
            json.dump(failed, f, indent=2)
        print(f"Saved {len(failed)} failed counties to {failed_path}")

    return sheriffs


async def main():
    sheriffs = await scrape_pa_counties()
    if sheriffs:
        print("\n\nResults:")
        for county, sheriff in sorted(sheriffs.items()):
            print(f"  {county}: {sheriff}")
        print(f"\nTotal: {len(sheriffs)}/67 counties")


if __name__ == "__main__":
    asyncio.run(main())
