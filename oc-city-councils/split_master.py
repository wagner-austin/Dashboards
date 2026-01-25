"""
Split master JSON into per-city files and generate YAML templates.

This script:
1. Splits oc_cities_master.json into cities/{slug}.json files
2. Generates YAML templates for cities that don't have them yet
3. Creates a combine script to merge them back if needed
"""
import json
import os
import re
from pathlib import Path


def slugify(name):
    """Convert city name to slug (e.g., 'Aliso Viejo' -> 'aliso-viejo')"""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def split_master_json():
    """Split master JSON into individual city files"""
    master_path = Path('oc_cities_master.json')
    cities_dir = Path('cities')
    cities_dir.mkdir(exist_ok=True)

    with open(master_path, 'r', encoding='utf-8') as f:
        master = json.load(f)

    metadata = master.get('_metadata', {})
    cities = master.get('cities', {})

    print(f"Splitting {len(cities)} cities...")

    for city_name, city_data in cities.items():
        slug = slugify(city_name)
        city_file = cities_dir / f'{slug}.json'

        # Add city name to data
        city_data['city_name'] = city_name
        city_data['slug'] = slug

        with open(city_file, 'w', encoding='utf-8') as f:
            json.dump(city_data, f, indent=2, ensure_ascii=False)

        members = city_data.get('council_members', [])
        emails = sum(1 for m in members if m.get('email'))
        print(f"  {city_name} -> {city_file.name} ({len(members)} members, {emails} emails)")

    # Save metadata separately
    meta_file = cities_dir / '_metadata.json'
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nCreated {len(cities)} city files in {cities_dir}/")
    return cities


def generate_yaml_template(city_name, city_data):
    """Generate a YAML template for a city"""
    slug = slugify(city_name)
    members = city_data.get('council_members', [])

    lines = [
        f'# {city_name} City Council',
        f'# Last updated: 2026-01-24',
        '',
        f'city: "{slug}"',
        f'city_name: "{city_name}"',
        f'last_updated: "2026-01-24"',
        '',
        '# Election info (fill in)',
        'next_election: null',
        'seats_up: []',
        '',
        '# City info',
        f'website: "{city_data.get("website", "")}"',
        f'council_url: "{city_data.get("council_url", "")}"',
        f'email: "{city_data.get("email", "")}"',
        f'phone: "{city_data.get("phone", "")}"',
        f'instagram: "{city_data.get("instagram", "")}"',
        '',
        '# Council members',
        'members:',
    ]

    for member in members:
        lines.append(f'  - name: "{member.get("name", "")}"')
        lines.append(f'    position: "{member.get("position", "")}"')
        lines.append(f'    district: {json.dumps(member.get("district"))}')
        lines.append(f'    email: {json.dumps(member.get("email"))}')
        lines.append(f'    phone: {json.dumps(member.get("phone"))}')
        lines.append(f'    city_profile: {json.dumps(member.get("city_profile"))}')
        lines.append(f'    # Rich data (fill in)')
        lines.append(f'    photo_url: null')
        lines.append(f'    bio: null')
        lines.append(f'    term_start: null')
        lines.append(f'    term_end: null')
        lines.append(f'    website: null')
        lines.append(f'    instagram: null')
        lines.append('')

    return '\n'.join(lines)


def generate_yaml_templates():
    """Generate YAML templates for cities that don't have them"""
    master_path = Path('oc_cities_master.json')
    yaml_dir = Path('_council_data')
    yaml_dir.mkdir(exist_ok=True)

    with open(master_path, 'r', encoding='utf-8') as f:
        master = json.load(f)

    cities = master.get('cities', {})
    existing = {f.stem for f in yaml_dir.glob('*.yaml')}

    created = 0
    for city_name, city_data in cities.items():
        slug = slugify(city_name)
        if slug not in existing:
            yaml_content = generate_yaml_template(city_name, city_data)
            yaml_file = yaml_dir / f'{slug}.yaml'
            with open(yaml_file, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            print(f"  Created {yaml_file.name}")
            created += 1

    print(f"\nCreated {created} new YAML templates")
    print(f"Total YAML files: {len(list(yaml_dir.glob('*.yaml')))}")


if __name__ == '__main__':
    print("=" * 60)
    print("SPLITTING MASTER JSON")
    print("=" * 60)
    split_master_json()

    print("\n" + "=" * 60)
    print("GENERATING YAML TEMPLATES")
    print("=" * 60)
    generate_yaml_templates()
