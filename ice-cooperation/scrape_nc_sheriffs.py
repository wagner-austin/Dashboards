"""
Scrape North Carolina sheriffs from NCSA individual county pages.
NC has 100 counties - we'll visit /sheriffs/{county} for each.
"""

import asyncio
import json
import re
from pathlib import Path

# All 100 NC counties
NC_COUNTIES = [
    'alamance', 'alexander', 'alleghany', 'anson', 'ashe', 'avery', 'beaufort',
    'bertie', 'bladen', 'brunswick', 'buncombe', 'burke', 'cabarrus', 'caldwell',
    'camden', 'carteret', 'caswell', 'catawba', 'chatham', 'cherokee', 'chowan',
    'clay', 'cleveland', 'columbus', 'craven', 'cumberland', 'currituck', 'dare',
    'davidson', 'davie', 'duplin', 'durham', 'edgecombe', 'forsyth', 'franklin',
    'gaston', 'gates', 'graham', 'granville', 'greene', 'guilford', 'halifax',
    'harnett', 'haywood', 'henderson', 'hertford', 'hoke', 'hyde', 'iredell',
    'jackson', 'johnston', 'jones', 'lee', 'lenoir', 'lincoln', 'macon',
    'madison', 'martin', 'mcdowell', 'mecklenburg', 'mitchell', 'montgomery',
    'moore', 'nash', 'new-hanover', 'northampton', 'onslow', 'orange', 'pamlico',
    'pasquotank', 'pender', 'perquimans', 'person', 'pitt', 'polk', 'randolph',
    'richmond', 'robeson', 'rockingham', 'rowan', 'rutherford', 'sampson',
    'scotland', 'stanly', 'stokes', 'surry', 'swain', 'transylvania', 'tyrrell',
    'union', 'vance', 'wake', 'warren', 'washington', 'watauga', 'wayne',
    'wilkes', 'wilson', 'yadkin', 'yancey'
]


async def scrape_nc_sheriffs():
    """Scrape all NC county sheriff pages."""
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

        for i, county in enumerate(NC_COUNTIES):
            url = f'https://ncsheriffs.org/sheriffs/{county}'
            county_title = county.replace('-', ' ').title()
            print(f"[{i+1}/100] {county_title} County: {url}")

            page = await context.new_page()
            if stealth:
                await stealth.apply_stealth_async(page)

            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(2000)

                text = await page.inner_text('body')

                # Look for sheriff name patterns
                # NC pages typically show "Sheriff FirstName LastName"
                patterns = [
                    r'Sheriff\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[IVXJ]+\.?)?)',
                    r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[IVXJ]+\.?)?),?\s+Sheriff',
                ]

                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        name = match.group(1).strip()
                        # Filter bad matches
                        bad_words = ['county', 'office', 'association', 'north', 'carolina']
                        if not any(w in name.lower() for w in bad_words) and len(name) > 4:
                            sheriffs[county_title] = name
                            print(f"  Found: {name}")
                            break
                else:
                    print(f"  Could not extract name")

            except Exception as e:
                print(f"  Error: {e}")

            await page.close()

            # Small delay to be nice
            await asyncio.sleep(0.5)

        await browser.close()

    # Save results
    output_path = Path(__file__).parent / "nc_sheriffs_scraped.json"
    with open(output_path, 'w') as f:
        json.dump(sheriffs, f, indent=2)
    print(f"\n\nSaved {len(sheriffs)} sheriffs to {output_path}")

    return sheriffs


async def main():
    sheriffs = await scrape_nc_sheriffs()
    if sheriffs:
        print("\n\nResults:")
        for county, sheriff in sorted(sheriffs.items()):
            print(f"  {county}: {sheriff}")
        print(f"\nTotal: {len(sheriffs)}/100 counties")


if __name__ == "__main__":
    asyncio.run(main())
