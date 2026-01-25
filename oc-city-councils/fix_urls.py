"""
Fix broken URLs by trying alternate patterns.
"""

import json
from pathlib import Path
import requests


def load_master_data():
    path = Path(__file__).parent / "oc_cities_master.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_master_data(data):
    path = Path(__file__).parent / "oc_cities_master.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def try_url(url):
    """Try to access a URL and return status."""
    try:
        response = requests.get(
            url,
            timeout=10,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        if response.status_code == 200 and len(response.text) > 1000:
            return True, response.url
    except:
        pass
    return False, None


def fix_urls():
    """Try alternate URL patterns for broken cities."""
    data = load_master_data()
    cities = data["cities"]

    # Cities with 404 errors
    broken_cities = [
        "Buena Park", "Costa Mesa", "Dana Point", "Huntington Beach",
        "La Palma", "Laguna Beach", "Laguna Hills", "Lake Forest",
        "Los Alamitos", "Orange", "Placentia", "Rancho Santa Margarita",
        "San Juan Capistrano", "Stanton", "Westminster"
    ]

    # Common URL patterns to try
    patterns = [
        "{base}/government/city-council",
        "{base}/city-hall/city-council",
        "{base}/citycouncil",
        "{base}/city-council",
        "{base}/our-city/city-council",
        "{base}/departments/city-council",
        "{base}/elected-officials",
        "{base}/government/elected-officials",
        "{base}/your-government/city-council",
    ]

    print("=" * 60)
    print("Fixing Broken URLs")
    print("=" * 60)

    fixed = []
    still_broken = []

    for city_name in broken_cities:
        city = cities[city_name]
        base = city["website"]
        print(f"\n{city_name}:")
        print(f"  Current: {city['council_url']}")

        found = False
        for pattern in patterns:
            url = pattern.format(base=base)
            print(f"  Trying: {url}... ", end="", flush=True)

            ok, final_url = try_url(url)
            if ok:
                print("OK!")
                city["council_url"] = url
                city["url_status"] = "ok"
                fixed.append(city_name)
                found = True
                break
            else:
                print("no")

        if not found:
            still_broken.append(city_name)
            print(f"  Could not find working URL")

    # Save updates
    save_master_data(data)

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Fixed: {len(fixed)}")
    for city in fixed:
        print(f"  + {city}: {cities[city]['council_url']}")

    print(f"\nStill broken: {len(still_broken)}")
    for city in still_broken:
        print(f"  - {city}")


if __name__ == "__main__":
    fix_urls()
