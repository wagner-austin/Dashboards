"""
Update all city council data by running scrapers and saving to both JSON and YAML.
This is the master update script that ensures all data is fresh.

Usage:
    python update_all_data.py           # Update all cities
    python update_all_data.py --city "Anaheim"   # Update specific city
"""
import asyncio
import json
import yaml
import argparse
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# Import all scrapers
from scrapers.cities import (
    AlisoViejoScraper, AnaheimScraper, BreaScraper, BuenaParkScraper,
    CostaMesaScraper, CypressScraper, DanaPointScraper, FountainValleyScraper,
    FullertonScraper, GardenGroveScraper, HuntingtonBeachScraper, IrvineScraper,
    LaHabraScraper, LaPalmaScraper, LagunaBeachScraper, LagunaHillsScraper,
    LagunaNiguelScraper, LagunaWoodsScraper, LakeForestScraper, LosAlamitosScraper,
    MissionViejoScraper, NewportBeachScraper, OrangeScraper, PlacentiaScraper,
    RanchoSantaMargaritaScraper, SanClementeScraper, SanJuanCapistranoScraper,
    SantaAnaScraper, SealBeachScraper, StantonScraper, TustinScraper,
    VillaParkScraper, WestminsterScraper, YorbaLindaScraper,
)

SCRAPERS = {
    "Aliso Viejo": ("aliso-viejo", AlisoViejoScraper),
    "Anaheim": ("anaheim", AnaheimScraper),
    "Brea": ("brea", BreaScraper),
    "Buena Park": ("buena-park", BuenaParkScraper),
    "Costa Mesa": ("costa-mesa", CostaMesaScraper),
    "Cypress": ("cypress", CypressScraper),
    "Dana Point": ("dana-point", DanaPointScraper),
    "Fountain Valley": ("fountain-valley", FountainValleyScraper),
    "Fullerton": ("fullerton", FullertonScraper),
    "Garden Grove": ("garden-grove", GardenGroveScraper),
    "Huntington Beach": ("huntington-beach", HuntingtonBeachScraper),
    "Irvine": ("irvine", IrvineScraper),
    "La Habra": ("la-habra", LaHabraScraper),
    "La Palma": ("la-palma", LaPalmaScraper),
    "Laguna Beach": ("laguna-beach", LagunaBeachScraper),
    "Laguna Hills": ("laguna-hills", LagunaHillsScraper),
    "Laguna Niguel": ("laguna-niguel", LagunaNiguelScraper),
    "Laguna Woods": ("laguna-woods", LagunaWoodsScraper),
    "Lake Forest": ("lake-forest", LakeForestScraper),
    "Los Alamitos": ("los-alamitos", LosAlamitosScraper),
    "Mission Viejo": ("mission-viejo", MissionViejoScraper),
    "Newport Beach": ("newport-beach", NewportBeachScraper),
    "Orange": ("orange", OrangeScraper),
    "Placentia": ("placentia", PlacentiaScraper),
    "Rancho Santa Margarita": ("rancho-santa-margarita", RanchoSantaMargaritaScraper),
    "San Clemente": ("san-clemente", SanClementeScraper),
    "San Juan Capistrano": ("san-juan-capistrano", SanJuanCapistranoScraper),
    "Santa Ana": ("santa-ana", SantaAnaScraper),
    "Seal Beach": ("seal-beach", SealBeachScraper),
    "Stanton": ("stanton", StantonScraper),
    "Tustin": ("tustin", TustinScraper),
    "Villa Park": ("villa-park", VillaParkScraper),
    "Westminster": ("westminster", WestminsterScraper),
    "Yorba Linda": ("yorba-linda", YorbaLindaScraper),
}

BASE_DIR = Path(__file__).parent
CITIES_DIR = BASE_DIR / "cities"
YAML_DIR = BASE_DIR / "_council_data"


def load_yaml(yaml_path):
    """Load existing YAML file."""
    if not yaml_path.exists():
        return {}
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def save_yaml(yaml_path, data):
    """Save data to YAML with proper formatting."""
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)


def save_json(json_path, data):
    """Save data to JSON with proper formatting."""
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def merge_member_data(existing, scraped):
    """Merge scraped data into existing member data, preserving curated content."""
    merged = existing.copy() if existing else {}

    # Fields from scraper
    scraped_fields = {
        'name': scraped.get('name'),
        'position': scraped.get('position'),
        'district': scraped.get('district'),
        'email': scraped.get('email'),
        'phone': scraped.get('phone'),
        'city_page': scraped.get('profile_url'),
        'photo_url': scraped.get('photo_url'),
        'term_start': scraped.get('term_start'),
        'term_end': scraped.get('term_end'),
    }

    # Bio handling - use scraped if we don't have one or it's longer
    scraped_bio = scraped.get('bio', '')
    existing_bio = merged.get('bio', '')
    if scraped_bio and (not existing_bio or len(scraped_bio) > len(existing_bio)):
        merged['bio'] = scraped_bio

    # Update fields - scraped takes precedence for contact info, preserve curated for others
    for field, value in scraped_fields.items():
        if value is not None:
            # Always update dynamic fields
            if field in ['email', 'phone', 'position', 'district']:
                merged[field] = value
            # Only update static fields if not already set
            elif not merged.get(field):
                merged[field] = value

    return merged


def find_member_by_name(name, members):
    """Find a member in a list by name (case-insensitive)."""
    name_lower = name.lower()
    for m in members:
        if m.get('name', '').lower() == name_lower:
            return m
    return None


def position_sort_key(m):
    """Sort key: Mayor first, then Pro Tem/Vice, then others."""
    pos = m.get('position', '').lower()
    if pos == 'mayor':
        return (0, m.get('name', ''))
    elif 'pro tem' in pos or 'vice' in pos:
        return (1, m.get('name', ''))
    else:
        return (2, m.get('name', ''))


async def update_city(page, city_name, slug, scraper_class):
    """Run scraper for a city and update both JSON and YAML."""
    print(f"\n  Scraping {city_name}...")

    # Run scraper
    scraper = scraper_class(page)
    result = await scraper.scrape()

    if not result or result.get('status') != 'success':
        print(f"    FAILED: {result.get('errors', ['Unknown error'])}")
        return None

    members = result.get('council_members', [])
    print(f"    Found {len(members)} members")

    # Load existing data
    json_path = CITIES_DIR / f"{slug}.json"
    yaml_path = YAML_DIR / f"{slug}.yaml"

    existing_json = {}
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            existing_json = json.load(f)

    existing_yaml = load_yaml(yaml_path)
    existing_yaml_members = existing_yaml.get('members', [])

    # Build new members list by merging scraped with existing YAML (preserves bios etc)
    new_members = []
    seen_names = set()

    for scraped in members:
        name = scraped.get('name', '')
        if not name or name.lower() in seen_names:
            continue
        seen_names.add(name.lower())

        existing = find_member_by_name(name, existing_yaml_members)
        merged = merge_member_data(existing, scraped)
        new_members.append(merged)

    # Sort members
    new_members.sort(key=position_sort_key)

    # Count emails
    emails = sum(1 for m in new_members if m.get('email'))

    # Update JSON
    json_data = existing_json.copy()
    json_data['city_name'] = city_name
    json_data['slug'] = slug
    json_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    json_data['council_members'] = [
        {
            'name': m.get('name'),
            'position': m.get('position'),
            'district': m.get('district'),
            'email': m.get('email'),
            'phone': m.get('phone'),
            'city_profile': m.get('city_page'),
            'photo_url': m.get('photo_url'),
        }
        for m in new_members
    ]
    save_json(json_path, json_data)

    # Update YAML
    yaml_data = existing_yaml.copy()
    yaml_data['city'] = slug
    yaml_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    if 'next_election' not in yaml_data:
        yaml_data['next_election'] = None
    if 'seats_up' not in yaml_data:
        yaml_data['seats_up'] = []
    yaml_data['members'] = new_members
    save_yaml(yaml_path, yaml_data)

    print(f"    Saved: {len(new_members)} members, {emails} emails")
    return {
        'members': len(new_members),
        'emails': emails,
    }


async def main(cities_to_update=None):
    """Main update function."""
    cities = cities_to_update or list(SCRAPERS.keys())

    print("=" * 70)
    print("OC CITY COUNCIL DATA UPDATE")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Cities: {len(cities)}")
    print("=" * 70)

    CITIES_DIR.mkdir(exist_ok=True)
    YAML_DIR.mkdir(exist_ok=True)

    results = {}
    total_members = 0
    total_emails = 0

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/Los_Angeles",
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = await context.new_page()

        for city_name in cities:
            if city_name not in SCRAPERS:
                print(f"\n  Skipping {city_name} - no scraper")
                continue

            slug, scraper_class = SCRAPERS[city_name]
            result = await update_city(page, city_name, slug, scraper_class)

            if result:
                results[city_name] = result
                total_members += result['members']
                total_emails += result['emails']

        await browser.close()

    # Summary
    print("\n" + "=" * 70)
    print("UPDATE COMPLETE")
    print("=" * 70)
    print(f"Cities updated: {len(results)}/{len(cities)}")
    print(f"Total members: {total_members}")
    print(f"Total emails: {total_emails} ({total_emails*100//total_members if total_members else 0}%)")

    # Show any cities with missing emails
    missing = [(city, r) for city, r in results.items() if r['emails'] < r['members']]
    if missing:
        print("\nCities with missing emails:")
        for city, r in missing:
            print(f"  {city}: {r['emails']}/{r['members']}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Update OC City Council data")
    parser.add_argument("--city", type=str, help="Specific city to update")
    args = parser.parse_args()

    cities = [args.city] if args.city else None
    asyncio.run(main(cities))
