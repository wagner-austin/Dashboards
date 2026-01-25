"""Batch test all city scrapers."""
import asyncio
import sys
import importlib
from playwright.async_api import async_playwright

# All 34 OC cities
ALL_CITIES = [
    "aliso_viejo", "anaheim", "brea", "buena_park", "costa_mesa",
    "cypress", "dana_point", "fountain_valley", "fullerton", "garden_grove",
    "huntington_beach", "irvine", "la_habra", "la_palma", "laguna_beach",
    "laguna_hills", "laguna_niguel", "laguna_woods", "lake_forest", "los_alamitos",
    "mission_viejo", "newport_beach", "orange", "placentia", "rancho_santa_margarita",
    "san_clemente", "san_juan_capistrano", "santa_ana", "seal_beach", "stanton",
    "tustin", "villa_park", "westminster", "yorba_linda"
]


def get_scraper_class(city_name):
    """Dynamically import scraper class for a city."""
    # Convert city_name to class name: la_habra -> LaHabraScraper
    class_name = "".join(word.title() for word in city_name.split("_")) + "Scraper"
    module = importlib.import_module(f"scrapers.cities.{city_name}")
    return getattr(module, class_name)


async def test_city(page, city_name):
    """Test a single city scraper."""
    try:
        ScraperClass = get_scraper_class(city_name)
        scraper = ScraperClass(page)
        results = await scraper.scrape()

        members = results.get("council_members", [])
        errors = results.get("errors", [])

        # Count emails found
        emails_found = sum(1 for m in members if m.get("email"))

        return {
            "city": city_name,
            "status": "OK" if members else "FAIL",
            "members": len(members),
            "emails": emails_found,
            "errors": errors,
            "data": members,
        }
    except Exception as e:
        return {
            "city": city_name,
            "status": "ERROR",
            "members": 0,
            "emails": 0,
            "errors": [str(e)],
            "data": [],
        }


async def run_tests(cities=None, verbose=False):
    """Run tests for specified cities or all cities."""
    cities = cities or ALL_CITIES

    results = []

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for city in cities:
            print(f"\n{'='*60}")
            print(f"Testing: {city}")
            print('='*60)

            result = await test_city(page, city)
            results.append(result)

            if verbose and result["data"]:
                for m in result["data"]:
                    print(f"  {m['name']} | {m['position']} | {m.get('email', 'None')}")

        await browser.close()

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"{'City':<30} {'Status':<8} {'Members':<8} {'Emails':<8}")
    print("-"*70)

    ok_count = 0
    fail_count = 0
    total_members = 0
    total_emails = 0

    for r in results:
        status_icon = "OK" if r["status"] == "OK" else "FAIL"
        print(f"{r['city']:<30} {status_icon:<8} {r['members']:<8} {r['emails']:<8}")

        if r["status"] == "OK":
            ok_count += 1
        else:
            fail_count += 1
        total_members += r["members"]
        total_emails += r["emails"]

    print("-"*70)
    print(f"{'TOTAL':<30} {ok_count}/{len(results):<5} {total_members:<8} {total_emails:<8}")

    if fail_count > 0:
        print(f"\nFAILED CITIES ({fail_count}):")
        for r in results:
            if r["status"] != "OK":
                print(f"  - {r['city']}: {r['errors']}")

    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            cities = ALL_CITIES
        else:
            cities = sys.argv[1:]
    else:
        # Default: test all
        cities = ALL_CITIES

    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    if verbose:
        cities = [c for c in cities if c not in ["-v", "--verbose"]]

    asyncio.run(run_tests(cities, verbose))
