"""
Update master JSON with verified URLs from web search.
"""

import json
from pathlib import Path

# Verified URLs from web search (January 2025)
URL_UPDATES = {
    "Aliso Viejo": {
        "website": "https://avcity.org",
        "council_url": "https://avcity.org/222/City-Council"
    },
    "Brea": {
        "website": "https://www.cityofbrea.gov",
        "council_url": "https://www.cityofbrea.gov/511/City-Council"
    },
    "Buena Park": {
        "website": "https://www.buenapark.com",
        "council_url": "https://www.buenapark.com/city_departments/city_council/council_members.php"
    },
    "Costa Mesa": {
        "website": "https://www.costamesaca.gov",
        "council_url": "https://www.costamesaca.gov/citycouncil"
    },
    "Dana Point": {
        "website": "https://www.danapoint.org",
        "council_url": "https://www.danapoint.org/departments/city-council"
    },
    "Huntington Beach": {
        "website": "https://www.huntingtonbeachca.gov",
        "council_url": "https://www.huntingtonbeachca.gov/citycouncil"
    },
    "La Habra": {
        "website": "https://www.lahabraca.gov",
        "council_url": "https://www.lahabraca.gov/153/City-Council"
    },
    "La Palma": {
        "website": "https://www.lapalmaca.gov",
        "council_url": "https://www.lapalmaca.gov/66/City-Council"
    },
    "Laguna Beach": {
        "website": "https://www.lagunabeachcity.net",
        "council_url": "https://www.lagunabeachcity.net/live-here/city-council"
    },
    "Laguna Hills": {
        "website": "https://www.lagunahillsca.gov",
        "council_url": "https://www.lagunahillsca.gov/129/City-Council"
    },
    "Lake Forest": {
        "website": "https://www.lakeforestca.gov",
        "council_url": "https://www.lakeforestca.gov/citycouncil"
    },
    "Los Alamitos": {
        "website": "https://cityoflosalamitos.org",
        "council_url": "https://cityoflosalamitos.org/165/City-Council"
    },
    "Orange": {
        "website": "https://www.cityoforange.org",
        "council_url": "https://www.cityoforange.org/citycouncil"
    },
    "Placentia": {
        "website": "https://www.placentia.org",
        "council_url": "https://www.placentia.org/268/Mayor-City-Council"
    },
    "Rancho Santa Margarita": {
        "website": "https://www.cityofrsm.org",
        "council_url": "https://www.cityofrsm.org/160/Mayor-City-Council"
    },
    "San Juan Capistrano": {
        "website": "https://sanjuancapistrano.org",
        "council_url": "https://sanjuancapistrano.org/318/City-Council"
    },
    "Stanton": {
        "website": "https://www.stantonca.gov",
        "council_url": "https://www.stantonca.gov/government/city_council.php"
    },
    "Villa Park": {
        "website": "https://villapark.org",
        "council_url": "https://villapark.org/council-and-committees/city-council"
    },
    "Westminster": {
        "website": "https://www.westminster-ca.gov",
        "council_url": "https://www.westminster-ca.gov/government/mayor-and-city-council-members"
    },
}


def update_urls():
    """Update master JSON with verified URLs."""
    path = Path(__file__).parent / "oc_cities_master.json"

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    updated = []
    for city_name, updates in URL_UPDATES.items():
        if city_name in data["cities"]:
            city = data["cities"][city_name]
            old_url = city.get("council_url", "")
            city["website"] = updates["website"]
            city["council_url"] = updates["council_url"]
            city["url_status"] = "verified"
            city["status"] = "needs_research" if city.get("status") != "complete" else city["status"]

            if old_url != updates["council_url"]:
                updated.append(f"{city_name}: {old_url} -> {updates['council_url']}")
            else:
                updated.append(f"{city_name}: URL verified (no change)")

    # Update metadata
    data["_metadata"]["last_updated"] = "2026-01-24"
    data["_metadata"]["urls_verified"] = "2026-01-24"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Updated URLs:")
    for msg in updated:
        print(f"  {msg}")

    print(f"\nTotal updated: {len(updated)}")
    print(f"Saved to: {path}")


if __name__ == "__main__":
    update_urls()
