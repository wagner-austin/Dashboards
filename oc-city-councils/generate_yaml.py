#!/usr/bin/env python3
"""
Orange County City Council Dashboard Generator

Generates dashboards for all 34 OC cities using shared templates.

Usage:
    python generate.py                 # Generate all configured cities
    python generate.py --city irvine   # Generate single city
    python generate.py --quick         # Skip Playwright scraping
    python generate.py --list          # List all configured cities
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.scrapers import GranicusScraper, LegistarClient
from shared.utils import calculate_next_meeting


ROOT = Path(__file__).parent
CONFIG_DIR = ROOT / "_config"
COUNCIL_DATA_DIR = ROOT / "_council_data"
TEMPLATE_DIR = Path(__file__).parent.parent / "shared" / "templates"


def load_city_config(city_slug: str) -> dict:
    """Load city configuration from YAML file."""
    config_path = CONFIG_DIR / f"{city_slug}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_council_data(city_slug: str) -> dict:
    """Load council member data from YAML file."""
    data_path = COUNCIL_DATA_DIR / f"{city_slug}.yaml"
    if not data_path.exists():
        return {"members": []}

    with open(data_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"members": []}


def get_scraper(config: dict):
    """Get the appropriate scraper based on city configuration."""
    system = config.get("scraping", {}).get("system", "manual")

    if system == "granicus":
        return GranicusScraper(config)
    elif system == "legistar":
        return LegistarClient(config)
    else:
        return None


def generate_city_dashboard(city_slug: str, quick_mode: bool = False) -> str:
    """Generate dashboard for a single city.

    Args:
        city_slug: City identifier (e.g., 'irvine', 'anaheim')
        quick_mode: If True, skip Playwright scraping

    Returns:
        Path to generated index.html
    """
    print(f"\n[*] Generating dashboard for: {city_slug}")

    # Load configuration
    config = load_city_config(city_slug)
    council_data = load_council_data(city_slug)

    print(f"    City: {config['city']['name']}")
    print(f"    System: {config.get('scraping', {}).get('system', 'manual')}")

    # Fetch meetings
    meetings = []
    if not quick_mode:
        scraper = get_scraper(config)
        if scraper:
            print(f"    Fetching meetings...")
            try:
                meeting_objs = scraper.fetch_meetings()
                meetings = [m.to_dict() for m in meeting_objs]
                print(f"    Found {len(meetings)} meetings")
            except Exception as e:
                print(f"    Warning: Failed to fetch meetings: {e}")
        else:
            print(f"    No scraper configured, skipping meeting fetch")
    else:
        print(f"    Quick mode - skipping meeting fetch")

    # Prepare template data
    council_members = council_data.get("members", [])
    # Convert photo_url to photo for template compatibility
    for member in council_members:
        if "photo_url" in member and "photo" not in member:
            member["photo"] = member["photo_url"]

    data = {
        "meetings": meetings,
        "council_members": council_members,
    }

    template_context = {
        "city": config.get("city", {}),
        "theme": config.get("theme", {}),
        "council": config.get("council", {}),
        "meetings": config.get("meetings", {}),
        "links": config.get("links", {}),
        "contact": config.get("contact", {}),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_json": json.dumps(data, ensure_ascii=False),
        "meeting_schedule_json": json.dumps({
            "schedule": config.get("meetings", {}).get("schedule", ""),
            "time": config.get("meetings", {}).get("time", ""),
        }),
    }

    # Render template
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("city_council.html.j2")
    html = template.render(**template_context)

    # Create city directory and save
    city_dir = ROOT / city_slug
    city_dir.mkdir(exist_ok=True)

    output_path = city_dir / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"    Saved to: {output_path}")
    return str(output_path)


def list_configured_cities() -> list[str]:
    """List all cities that have configuration files."""
    cities = []
    if CONFIG_DIR.exists():
        for config_file in sorted(CONFIG_DIR.glob("*.yaml")):
            cities.append(config_file.stem)
    return cities


def generate_all_cities(quick_mode: bool = False) -> dict:
    """Generate dashboards for all configured cities.

    Returns:
        Dict with 'success' and 'failed' lists of city slugs.
    """
    cities = list_configured_cities()

    if not cities:
        print("[!] No city configurations found in _config/")
        return {"success": [], "failed": []}

    print(f"[*] Found {len(cities)} configured cities")

    success = []
    failed = []

    for city_slug in cities:
        try:
            generate_city_dashboard(city_slug, quick_mode=quick_mode)
            success.append(city_slug)
        except Exception as e:
            print(f"    [!] Error: {e}")
            failed.append(city_slug)

    return {"success": success, "failed": failed}


def main():
    parser = argparse.ArgumentParser(
        description="Generate Orange County City Council Dashboards"
    )
    parser.add_argument(
        "--city",
        type=str,
        help="Generate dashboard for a specific city (slug name)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode - skip Playwright scraping",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all configured cities",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Orange County City Council Dashboard Generator")
    print("=" * 60)

    if args.list:
        cities = list_configured_cities()
        if cities:
            print(f"\nConfigured cities ({len(cities)}):")
            for city in cities:
                print(f"  - {city}")
        else:
            print("\nNo configured cities found.")
        return

    if args.city:
        try:
            output = generate_city_dashboard(args.city, quick_mode=args.quick)
            print(f"\n[+] Dashboard generated: {output}")
        except FileNotFoundError as e:
            print(f"\n[!] Error: {e}")
            sys.exit(1)
    else:
        result = generate_all_cities(quick_mode=args.quick)

        print("\n" + "=" * 60)
        print(f"[+] Success: {len(result['success'])} cities")
        if result["failed"]:
            print(f"[!] Failed: {len(result['failed'])} cities")
            for city in result["failed"]:
                print(f"    - {city}")
            sys.exit(1)
        print("=" * 60)


if __name__ == "__main__":
    main()
