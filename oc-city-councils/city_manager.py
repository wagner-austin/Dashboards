"""
City data manager for OC City Councils.

Provides utilities for:
- Loading/saving individual city files
- Combining all cities into a single file
- Syncing between JSON and YAML formats
"""
import json
import re
from pathlib import Path
from datetime import datetime

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("Warning: PyYAML not installed. YAML features disabled.")


CITIES_DIR = Path(__file__).parent / 'cities'
YAML_DIR = Path(__file__).parent / '_council_data'


def slugify(name):
    """Convert city name to slug"""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def load_city(city_name_or_slug):
    """Load a single city's data from JSON"""
    slug = slugify(city_name_or_slug)
    city_file = CITIES_DIR / f'{slug}.json'

    if not city_file.exists():
        raise FileNotFoundError(f"City file not found: {city_file}")

    with open(city_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_city(city_data):
    """Save a single city's data to JSON"""
    slug = city_data.get('slug') or slugify(city_data.get('city_name', ''))
    city_file = CITIES_DIR / f'{slug}.json'

    with open(city_file, 'w', encoding='utf-8') as f:
        json.dump(city_data, f, indent=2, ensure_ascii=False)

    return city_file


def load_all_cities():
    """Load all city JSON files into a dict"""
    cities = {}
    for city_file in sorted(CITIES_DIR.glob('*.json')):
        if city_file.name.startswith('_'):
            continue  # Skip metadata files
        with open(city_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            city_name = data.get('city_name', city_file.stem)
            cities[city_name] = data
    return cities


def combine_cities(output_file='oc_cities_master.json'):
    """Combine all city files into a single master JSON"""
    cities = load_all_cities()

    # Load metadata if exists
    meta_file = CITIES_DIR / '_metadata.json'
    if meta_file.exists():
        with open(meta_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        metadata = {}

    metadata['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    metadata['total_cities'] = len(cities)

    master = {
        '_metadata': metadata,
        'cities': cities
    }

    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(master, f, indent=2, ensure_ascii=False)

    print(f"Combined {len(cities)} cities into {output_path}")
    return output_path


def update_city_member(city_name, member_name, updates):
    """Update a specific council member's data"""
    city_data = load_city(city_name)

    for member in city_data.get('council_members', []):
        if member.get('name', '').lower() == member_name.lower():
            member.update(updates)
            save_city(city_data)
            print(f"Updated {member_name} in {city_name}")
            return True

    print(f"Member {member_name} not found in {city_name}")
    return False


def get_city_stats():
    """Get statistics about all cities"""
    cities = load_all_cities()

    stats = {
        'total_cities': len(cities),
        'total_members': 0,
        'members_with_email': 0,
        'members_with_photo': 0,
        'cities_complete': [],
        'cities_missing_emails': [],
    }

    for city_name, city_data in cities.items():
        members = city_data.get('council_members', [])
        stats['total_members'] += len(members)

        emails = sum(1 for m in members if m.get('email'))
        photos = sum(1 for m in members if m.get('photo_url'))

        stats['members_with_email'] += emails
        stats['members_with_photo'] += photos

        if emails == len(members) and len(members) > 0:
            stats['cities_complete'].append(city_name)
        elif emails < len(members):
            stats['cities_missing_emails'].append((city_name, emails, len(members)))

    return stats


def list_cities():
    """List all cities with their status"""
    cities = load_all_cities()

    print(f"\n{'City':<25} {'Members':>8} {'Emails':>8} {'Photos':>8}")
    print("-" * 55)

    for city_name in sorted(cities.keys()):
        city_data = cities[city_name]
        members = city_data.get('council_members', [])
        total = len(members)
        emails = sum(1 for m in members if m.get('email'))
        photos = sum(1 for m in members if m.get('photo_url'))
        print(f"{city_name:<25} {total:>8} {emails:>8} {photos:>8}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python city_manager.py list          - List all cities")
        print("  python city_manager.py stats         - Show statistics")
        print("  python city_manager.py combine       - Combine into master JSON")
        print("  python city_manager.py show <city>   - Show city details")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'list':
        list_cities()
    elif cmd == 'stats':
        stats = get_city_stats()
        print(f"\nTotal cities: {stats['total_cities']}")
        print(f"Total members: {stats['total_members']}")
        print(f"Members with email: {stats['members_with_email']}")
        print(f"Members with photo: {stats['members_with_photo']}")
        print(f"\nComplete cities: {len(stats['cities_complete'])}")
        if stats['cities_missing_emails']:
            print(f"\nMissing emails:")
            for city, has, total in stats['cities_missing_emails']:
                print(f"  {city}: {has}/{total}")
    elif cmd == 'combine':
        combine_cities()
    elif cmd == 'show' and len(sys.argv) > 2:
        city_name = ' '.join(sys.argv[2:])
        try:
            data = load_city(city_name)
            print(json.dumps(data, indent=2))
        except FileNotFoundError as e:
            print(e)
    else:
        print(f"Unknown command: {cmd}")
