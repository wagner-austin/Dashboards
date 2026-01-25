"""
Main runner for OC City Council scrapers.

Usage:
    python run_scrapers.py                        # Scrape cities with missing data
    python run_scrapers.py --city "Anaheim"       # Scrape specific city
    python run_scrapers.py --all                  # Scrape all cities
    python run_scrapers.py --browser firefox      # Use Firefox (better for bot detection)
    python run_scrapers.py --browser chromium     # Use Chromium (default)
    python run_scrapers.py --stealth              # Use Firefox with stealth settings
    python run_scrapers.py --update               # Scrape AND update master JSON
    python run_scrapers.py --update --all         # Full refresh of all data
"""
import asyncio
import json
import argparse
from datetime import datetime
from playwright.async_api import async_playwright

# Import scrapers
from scrapers.civicplus import (
    AlisoViejoScraper, LaHabraScraper, LaPalmaScraper,
    LagunaHillsScraper, BreaScraper
)
from scrapers.anaheim import AnaheimScraper
from scrapers.custom import (
    OrangeScraper, LagunaBeachScraper, MissionViejoScraper, TustinScraper
)

# Registry of available scrapers
SCRAPERS = {
    "Aliso Viejo": AlisoViejoScraper,
    "Anaheim": AnaheimScraper,
    "Brea": BreaScraper,
    "La Habra": LaHabraScraper,
    "La Palma": LaPalmaScraper,
    "Laguna Beach": LagunaBeachScraper,
    "Laguna Hills": LagunaHillsScraper,
    "Mission Viejo": MissionViejoScraper,
    "Orange": OrangeScraper,
    "Tustin": TustinScraper,
}

# Cities that need data (have null emails or generic emails)
CITIES_NEEDING_DATA = [
    "Aliso Viejo",
    "Anaheim",
    "La Habra",
    "La Palma",
    "Laguna Beach",
    "Orange",
    "Mission Viejo",
    "Tustin"
]


async def run_scraper(page, city_name):
    """Run scraper for a specific city"""
    if city_name not in SCRAPERS:
        print(f"  No scraper available for {city_name}")
        return None

    scraper_class = SCRAPERS[city_name]
    scraper = scraper_class(page)
    return await scraper.scrape()


async def main(cities_to_scrape=None, scrape_all=False, browser_type="chromium", stealth=False):
    """Main scraping function

    Args:
        cities_to_scrape: List of specific cities to scrape
        scrape_all: If True, scrape all available cities
        browser_type: "chromium" or "firefox"
        stealth: If True, use stealth settings (Firefox recommended)
    """

    if scrape_all:
        cities = list(SCRAPERS.keys())
    elif cities_to_scrape:
        cities = cities_to_scrape
    else:
        cities = CITIES_NEEDING_DATA

    print("="*70)
    print("OC CITY COUNCIL SCRAPER")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Browser: {browser_type}" + (" (stealth mode)" if stealth else ""))
    print(f"Cities to scrape: {', '.join(cities)}")
    print("="*70)

    all_results = {
        "scrape_date": datetime.now().isoformat(),
        "browser": browser_type,
        "stealth_mode": stealth,
        "cities_scraped": [],
        "results": {},
        "summary": {
            "total_cities": 0,
            "successful": 0,
            "failed": 0,
            "total_emails_found": 0,
            "total_pages_visited": 0
        }
    }

    async with async_playwright() as p:
        # Choose browser
        if browser_type == "firefox":
            browser = await p.firefox.launch(headless=True)
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        else:
            # Chromium with optional stealth args
            launch_args = []
            if stealth:
                launch_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-infobars',
                ]
            browser = await p.chromium.launch(headless=True, args=launch_args)
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'

        # Create context
        context_options = {
            'user_agent': user_agent,
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'en-US',
        }

        if stealth:
            context_options['timezone_id'] = 'America/Los_Angeles'

        context = await browser.new_context(**context_options)

        # Add stealth scripts if enabled
        if stealth:
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

        page = await context.new_page()

        for city in cities:
            print(f"\n{'='*70}")
            print(f"CITY: {city}")
            print("="*70)

            result = await run_scraper(page, city)

            if result:
                all_results["results"][city] = result
                all_results["cities_scraped"].append(city)
                all_results["summary"]["total_cities"] += 1
                all_results["summary"]["total_pages_visited"] += len(result.get("pages_visited", []))
                all_results["summary"]["total_emails_found"] += len(result.get("emails_found", []))

                if result.get("status") == "success":
                    all_results["summary"]["successful"] += 1
                else:
                    all_results["summary"]["failed"] += 1

        await browser.close()

    # Save results
    output_file = r'C:\Users\Test\PROJECTS\Dashboards\oc-city-councils\scrape_results.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    # Print summary
    print("\n" + "="*70)
    print("SCRAPE COMPLETE - SUMMARY")
    print("="*70)
    print(f"Cities scraped: {all_results['summary']['total_cities']}")
    print(f"Successful: {all_results['summary']['successful']}")
    print(f"Failed: {all_results['summary']['failed']}")
    print(f"Total pages visited: {all_results['summary']['total_pages_visited']}")
    print(f"Total emails found: {all_results['summary']['total_emails_found']}")

    print("\n" + "-"*70)
    print("EMAILS BY CITY")
    print("-"*70)

    for city, data in all_results["results"].items():
        print(f"\n{city}:")
        print(f"  Status: {data.get('status', 'unknown')}")
        print(f"  Platform: {data.get('platform', 'unknown')}")
        print(f"  Pages: {data.get('pages_success', 0)} success, {data.get('pages_failed', 0)} failed")

        if data.get("emails_found"):
            print(f"  Emails ({len(data['emails_found'])}):")
            for email in data["emails_found"]:
                print(f"    - {email}")
        else:
            print("  Emails: (none found)")

        if data.get("council_members"):
            print(f"  Council Members ({len(data['council_members'])}):")
            for m in data["council_members"]:
                email_str = m.get('email') or '(no email)'
                print(f"    - {m['name']} ({m['position']}): {email_str}")

        if data.get("errors"):
            print(f"  Errors: {data['errors']}")

    print(f"\nResults saved to: {output_file}")
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape OC City Council data")
    parser.add_argument("--city", type=str, help="Specific city to scrape")
    parser.add_argument("--all", action="store_true", help="Scrape all available cities")
    parser.add_argument(
        "--browser",
        type=str,
        choices=["chromium", "firefox"],
        default="chromium",
        help="Browser to use: chromium (default) or firefox (better for bot detection)"
    )
    parser.add_argument(
        "--stealth",
        action="store_true",
        help="Enable stealth mode to bypass bot detection (recommended with firefox)"
    )

    args = parser.parse_args()

    if args.city:
        cities = [args.city]
    else:
        cities = None

    # If stealth mode is enabled, default to firefox if not explicitly set
    browser = args.browser
    if args.stealth and args.browser == "chromium":
        print("Note: Stealth mode works best with Firefox. Use --browser firefox for best results.")

    asyncio.run(main(
        cities_to_scrape=cities,
        scrape_all=args.all,
        browser_type=browser,
        stealth=args.stealth
    ))
