"""
Batch scraper for multiple OC cities.

Usage:
    python scrape_batch.py           # Scrape all pending cities
    python scrape_batch.py --south   # South OC cities only
    python scrape_batch.py --north   # North OC cities only
"""

import sys
import time
from scrape_city import scrape_city, load_master_data

# Geographic groupings
SOUTH_OC = [
    "Aliso Viejo", "Dana Point", "Laguna Beach", "Laguna Hills",
    "Laguna Niguel", "Laguna Woods", "Lake Forest", "Mission Viejo",
    "Rancho Santa Margarita", "San Clemente", "San Juan Capistrano"
]

CENTRAL_OC = [
    "Costa Mesa", "Irvine", "Newport Beach", "Santa Ana", "Tustin"
]

NORTH_OC = [
    "Anaheim", "Brea", "Buena Park", "Cypress", "Fountain Valley",
    "Fullerton", "Garden Grove", "Huntington Beach", "La Habra",
    "La Palma", "Los Alamitos", "Orange", "Placentia", "Seal Beach",
    "Stanton", "Villa Park", "Westminster", "Yorba Linda"
]


def main():
    master = load_master_data()

    # Determine which cities to scrape
    if "--south" in sys.argv:
        cities = SOUTH_OC
        print("Scraping South OC cities...")
    elif "--north" in sys.argv:
        cities = NORTH_OC
        print("Scraping North OC cities...")
    elif "--central" in sys.argv:
        cities = CENTRAL_OC
        print("Scraping Central OC cities...")
    else:
        # All pending cities
        cities = [
            name for name, info in master["cities"].items()
            if info.get("status") in ["needs_research", None]
        ]
        print(f"Scraping all {len(cities)} pending cities...")

    results = {"success": [], "failed": [], "skipped": []}

    for i, city in enumerate(cities):
        if city not in master["cities"]:
            print(f"Skipping unknown city: {city}")
            results["skipped"].append(city)
            continue

        status = master["cities"][city].get("status")
        if status == "complete":
            print(f"[{i+1}/{len(cities)}] Skipping {city} (already complete)")
            results["skipped"].append(city)
            continue

        print(f"\n[{i+1}/{len(cities)}] Processing {city}...")

        try:
            result = scrape_city(city)
            if result and len(result.get("council_members", [])) > 0:
                results["success"].append(city)
            else:
                results["failed"].append(city)
        except Exception as e:
            print(f"ERROR: {e}")
            results["failed"].append(city)

        # Be nice to servers
        time.sleep(3)

    # Final summary
    print("\n" + "=" * 60)
    print("BATCH COMPLETE")
    print("=" * 60)
    print(f"Successful: {len(results['success'])}")
    for city in results["success"]:
        print(f"  - {city}")

    print(f"\nFailed/No data: {len(results['failed'])}")
    for city in results["failed"]:
        print(f"  - {city}")

    print(f"\nSkipped: {len(results['skipped'])}")


if __name__ == "__main__":
    main()
