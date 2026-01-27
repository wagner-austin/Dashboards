#!/usr/bin/env python3
"""
YAML Standardization Script for OC City Council Data

This script standardizes all YAML files in the _council_data directory to follow
a canonical schema with consistent field ordering, naming, and formatting.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional


# Canonical field order for top-level fields
TOP_LEVEL_ORDER = [
    'city',           # required - slug
    'city_name',      # required - display name
    'website',        # required - main city website
    'council_url',    # required - council page URL
    'last_updated',   # required - date string
    'members',        # required - array of council members
    'meetings',       # required - meeting info object
    'portals',        # online portal links
    'broadcast',      # TV broadcast info
    'clerk',          # city clerk contact
    'public_comment', # public comment procedures
    'council',        # required - council structure
    'elections',      # election info
]

# Canonical field order for member records
MEMBER_ORDER = [
    'name',           # required
    'position',       # required - Mayor, Vice Mayor, Councilmember, Mayor Pro Tem
    'district',       # District X, Ward X, At-Large, or null
    'email',
    'phone',          # format: (XXX) XXX-XXXX
    'city_page',      # standardized (not city_profile)
    'photo_url',
    'bio',            # empty string if not available
    'term_start',
    'term_end',
    'website',        # optional personal website
    'instagram',      # optional
]


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """
    Normalize phone number to (XXX) XXX-XXXX format.
    Returns None if input is None or empty.
    """
    if not phone:
        return phone

    # Convert to string if not already
    phone = str(phone)

    # Extract digits only
    digits = re.sub(r'\D', '', phone)

    # Handle 10-digit phone numbers
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

    # Handle 11-digit (with leading 1)
    if len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"

    # If we can't normalize, return original
    return phone


def generate_city_name(city_slug: str) -> str:
    """
    Generate a display name from a city slug.
    e.g., 'fountain-valley' -> 'Fountain Valley'
    """
    # Special cases
    special_cases = {
        'la-habra': 'La Habra',
        'la-palma': 'La Palma',
    }

    if city_slug in special_cases:
        return special_cases[city_slug]

    # General case: capitalize each word
    return ' '.join(word.capitalize() for word in city_slug.split('-'))


def order_dict(data: Dict[str, Any], order: List[str]) -> Dict[str, Any]:
    """
    Reorder dictionary keys according to specified order.
    Keys not in order list are appended at the end.
    """
    result = {}

    # Add keys in specified order
    for key in order:
        if key in data:
            result[key] = data[key]

    # Add any remaining keys not in the order list
    for key in data:
        if key not in result:
            result[key] = data[key]

    return result


def normalize_member(member: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a single member record:
    - Rename city_profile to city_page if city_page doesn't exist
    - Remove city_profile if city_page exists (duplicate)
    - Normalize phone number format
    - Add missing bio field with empty string
    - Reorder fields
    """
    result = dict(member)

    # Handle city_profile -> city_page rename
    if 'city_profile' in result:
        if 'city_page' not in result or not result['city_page']:
            result['city_page'] = result['city_profile']
        del result['city_profile']

    # Normalize phone number
    if 'phone' in result:
        result['phone'] = normalize_phone(result['phone'])

    # Ensure bio field exists (empty string if not present)
    if 'bio' not in result:
        result['bio'] = ''

    # Reorder fields
    return order_dict(result, MEMBER_ORDER)


def normalize_portals(portals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize portal field names to standard fields.
    Migrations:
      granicus, granicus_archive -> video_archive
      wtv_stream, facebook (if live) -> live_stream
      agendalink, meetings, destiny, legistar -> agendas
      ecomment_live, online_comment -> ecomment
    """
    result = dict(portals)

    # Migrate granicus -> video_archive
    if 'granicus' in result and 'video_archive' not in result:
        result['video_archive'] = result['granicus']
    if 'granicus' in result:
        del result['granicus']

    if 'granicus_archive' in result and 'video_archive' not in result:
        result['video_archive'] = result['granicus_archive']
    if 'granicus_archive' in result:
        del result['granicus_archive']

    # Migrate agendalink -> agendas
    if 'agendalink' in result and 'agendas' not in result:
        result['agendas'] = result['agendalink']
    if 'agendalink' in result:
        del result['agendalink']

    # Migrate meetings -> agendas (if it's a URL)
    if 'meetings' in result and 'agendas' not in result:
        result['agendas'] = result['meetings']
    if 'meetings' in result:
        del result['meetings']

    # Migrate destiny -> agendas
    if 'destiny' in result and 'agendas' not in result:
        result['agendas'] = result['destiny']
    if 'destiny' in result:
        del result['destiny']

    # Migrate legistar -> agendas
    if 'legistar' in result and 'agendas' not in result:
        result['agendas'] = result['legistar']
    if 'legistar' in result:
        del result['legistar']

    # Migrate ecomment_live, online_comment -> ecomment
    if 'ecomment_live' in result and 'ecomment' not in result:
        result['ecomment'] = result['ecomment_live']
    if 'ecomment_live' in result:
        del result['ecomment_live']

    if 'online_comment' in result and 'ecomment' not in result:
        result['ecomment'] = result['online_comment']
    if 'online_comment' in result:
        del result['online_comment']

    # Reorder: agendas, live_stream, video_archive, youtube, ecomment, then others
    ordered = {}
    for key in ['agendas', 'live_stream', 'video_archive', 'youtube', 'ecomment']:
        if key in result:
            ordered[key] = result[key]
    for key in result:
        if key not in ordered:
            ordered[key] = result[key]

    return ordered


def normalize_yaml_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize the entire YAML data structure:
    - Add missing city_name if needed
    - Normalize all member records
    - Normalize phone numbers in clerk section
    - Reorder all fields
    """
    result = dict(data)

    # Ensure city_name exists
    if 'city_name' not in result or not result['city_name']:
        if 'city' in result:
            result['city_name'] = generate_city_name(result['city'])

    # Normalize members
    if 'members' in result and isinstance(result['members'], list):
        result['members'] = [normalize_member(m) for m in result['members']]

    # Normalize clerk phone
    if 'clerk' in result and isinstance(result['clerk'], dict):
        if 'phone' in result['clerk']:
            result['clerk']['phone'] = normalize_phone(result['clerk']['phone'])

    # Normalize portals
    if 'portals' in result and isinstance(result['portals'], dict):
        result['portals'] = normalize_portals(result['portals'])

    # Reorder top-level fields
    return order_dict(result, TOP_LEVEL_ORDER)


class CustomDumper(yaml.SafeDumper):
    """Custom YAML dumper with improved formatting."""
    pass


def str_representer(dumper, data):
    """Use literal block style for multi-line strings."""
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    # Use quotes for strings that might be interpreted as other types
    if data.lower() in ('true', 'false', 'yes', 'no', 'on', 'off', 'null', 'none', '~'):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


def none_representer(dumper, data):
    """Represent None as null."""
    return dumper.represent_scalar('tag:yaml.org,2002:null', 'null')


CustomDumper.add_representer(str, str_representer)
CustomDumper.add_representer(type(None), none_representer)


def process_file(filepath: Path, dry_run: bool = False) -> bool:
    """
    Process a single YAML file.
    Returns True if the file was modified, False otherwise.
    """
    print(f"Processing: {filepath.name}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Parse YAML
        data = yaml.safe_load(original_content)

        if not isinstance(data, dict):
            print(f"  Warning: {filepath.name} does not contain a YAML dict, skipping")
            return False

        # Normalize the data
        normalized = normalize_yaml_data(data)

        # Dump to YAML string
        new_content = yaml.dump(
            normalized,
            Dumper=CustomDumper,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120
        )

        # Check if content changed
        if original_content.strip() == new_content.strip():
            print(f"  No changes needed")
            return False

        if dry_run:
            print(f"  Would update (dry run)")
            return True

        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"  Updated")
        return True

    except Exception as e:
        print(f"  Error processing {filepath.name}: {e}")
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Standardize YAML files for OC City Council data')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without modifying files')
    parser.add_argument('--file', type=str, help='Process only a specific file')
    args = parser.parse_args()

    # Find the _council_data directory
    script_dir = Path(__file__).parent
    council_data_dir = script_dir / '_council_data'

    if not council_data_dir.exists():
        print(f"Error: {council_data_dir} not found")
        return 1

    # Get list of YAML files to process
    if args.file:
        yaml_files = [council_data_dir / args.file]
        if not yaml_files[0].exists():
            print(f"Error: {args.file} not found")
            return 1
    else:
        yaml_files = sorted(council_data_dir.glob('*.yaml'))

    if not yaml_files:
        print("No YAML files found")
        return 1

    print(f"Found {len(yaml_files)} YAML file(s) to process")
    if args.dry_run:
        print("DRY RUN - no files will be modified\n")
    print()

    modified_count = 0
    for filepath in yaml_files:
        if process_file(filepath, dry_run=args.dry_run):
            modified_count += 1

    print()
    print(f"Summary: {modified_count} of {len(yaml_files)} files {'would be ' if args.dry_run else ''}modified")

    return 0


if __name__ == '__main__':
    exit(main())
