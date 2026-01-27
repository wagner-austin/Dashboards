#!/usr/bin/env python3
"""
YAML Validation Script for OC City Council Data

Validates all YAML files against the canonical schema and reports:
- Missing required fields
- Data quality issues
- Summary of what needs to be collected
"""

import yaml
import re
from pathlib import Path
from collections import defaultdict
from schema import SCHEMA, get_required_fields


def validate_phone(phone: str) -> bool:
    """Check if phone matches (XXX) XXX-XXXX format."""
    if not phone:
        return False
    return bool(re.match(r'^\(\d{3}\) \d{3}-\d{4}$', str(phone)))


def validate_url(url: str) -> bool:
    """Check if URL looks valid."""
    if not url:
        return False
    return str(url).startswith(('http://', 'https://'))


def validate_date(date: str) -> bool:
    """Check if date matches YYYY-MM-DD format."""
    if not date:
        return False
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', str(date)))


def is_empty(value, allow_empty_list=False) -> bool:
    """Check if a value is effectively empty."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == '':
        return True
    if isinstance(value, list) and len(value) == 0 and not allow_empty_list:
        return True
    return False


def validate_file(filepath: Path) -> dict:
    """
    Validate a single YAML file.
    Returns dict with 'errors' and 'warnings' lists.
    """
    issues = {
        'errors': [],      # Missing required fields
        'warnings': [],    # Data quality issues
        'missing': [],     # Specific missing data to collect
    }

    try:
        data = yaml.safe_load(filepath.read_text(encoding='utf-8'))
    except Exception as e:
        issues['errors'].append(f"Failed to parse YAML: {e}")
        return issues

    city = filepath.stem

    # -------------------------------------------------------------------------
    # Validate top-level fields
    # -------------------------------------------------------------------------
    for field in get_required_fields('top_level'):
        if field not in data or is_empty(data.get(field)):
            issues['errors'].append(f"Missing required field: {field}")
            issues['missing'].append(('top_level', field))

    # -------------------------------------------------------------------------
    # Validate members
    # -------------------------------------------------------------------------
    members = data.get('members', [])
    if not members:
        issues['errors'].append("No members defined")
    else:
        for i, member in enumerate(members):
            member_name = member.get('name', f'Member {i+1}')

            for field in get_required_fields('member'):
                if field not in member:
                    issues['errors'].append(f"Member '{member_name}': missing {field}")
                    issues['missing'].append(('member', field, member_name))
                elif field == 'bio' and is_empty(member.get(field)):
                    issues['warnings'].append(f"Member '{member_name}': bio is empty")
                    issues['missing'].append(('member', 'bio', member_name))
                elif field == 'phone' and not validate_phone(member.get(field)):
                    issues['warnings'].append(f"Member '{member_name}': phone format should be (XXX) XXX-XXXX")

    # -------------------------------------------------------------------------
    # Validate meetings
    # -------------------------------------------------------------------------
    meetings = data.get('meetings', {})
    for field in get_required_fields('meetings'):
        if field not in meetings or is_empty(meetings.get(field)):
            issues['errors'].append(f"meetings.{field} missing")
            issues['missing'].append(('meetings', field))

    location = meetings.get('location', {})
    for field in get_required_fields('meetings.location'):
        if field not in location or is_empty(location.get(field)):
            issues['errors'].append(f"meetings.location.{field} missing")
            issues['missing'].append(('meetings.location', field))

    # -------------------------------------------------------------------------
    # Validate portals
    # -------------------------------------------------------------------------
    portals = data.get('portals', {})
    for field in get_required_fields('portals'):
        if field not in portals or is_empty(portals.get(field)):
            issues['errors'].append(f"portals.{field} missing")
            issues['missing'].append(('portals', field))

    # -------------------------------------------------------------------------
    # Validate broadcast
    # -------------------------------------------------------------------------
    broadcast = data.get('broadcast', {})
    if not broadcast:
        issues['errors'].append("broadcast section missing entirely")
        issues['missing'].append(('broadcast', 'cable_channels'))
        issues['missing'].append(('broadcast', 'live_stream'))
    else:
        for field in get_required_fields('broadcast'):
            # Allow empty list for cable_channels (some cities only stream online)
            allow_empty = (field == 'cable_channels')
            if field not in broadcast or is_empty(broadcast.get(field), allow_empty_list=allow_empty):
                issues['errors'].append(f"broadcast.{field} missing")
                issues['missing'].append(('broadcast', field))

    # -------------------------------------------------------------------------
    # Validate clerk
    # -------------------------------------------------------------------------
    clerk = data.get('clerk', {})
    for field in get_required_fields('clerk'):
        if field not in clerk or is_empty(clerk.get(field)):
            issues['errors'].append(f"clerk.{field} missing")
            issues['missing'].append(('clerk', field))

    # -------------------------------------------------------------------------
    # Validate public_comment
    # -------------------------------------------------------------------------
    public_comment = data.get('public_comment', {})
    for field in get_required_fields('public_comment'):
        if field not in public_comment:
            issues['errors'].append(f"public_comment.{field} missing")
            issues['missing'].append(('public_comment', field))

    # -------------------------------------------------------------------------
    # Validate council
    # -------------------------------------------------------------------------
    council = data.get('council', {})
    for field in get_required_fields('council'):
        # Special case: districts OR wards is acceptable
        if field == 'districts':
            if 'districts' not in council and 'wards' not in council:
                issues['errors'].append(f"council.districts (or council.wards) missing")
                issues['missing'].append(('council', field))
        elif field not in council:
            issues['errors'].append(f"council.{field} missing")
            issues['missing'].append(('council', field))

    # -------------------------------------------------------------------------
    # Validate elections
    # -------------------------------------------------------------------------
    elections = data.get('elections', {})
    for field in get_required_fields('elections'):
        if field not in elections or is_empty(elections.get(field)):
            issues['errors'].append(f"elections.{field} missing")
            issues['missing'].append(('elections', field))

    return issues


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Validate OC City Council YAML files')
    parser.add_argument('--file', type=str, help='Validate only a specific file')
    parser.add_argument('--summary', action='store_true', help='Show only summary, not per-file details')
    parser.add_argument('--checklist', action='store_true', help='Generate data collection checklist')
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    council_data_dir = script_dir / '_council_data'

    if args.file:
        yaml_files = [council_data_dir / args.file]
    else:
        yaml_files = sorted(council_data_dir.glob('*.yaml'))

    # Collect all issues
    all_issues = {}
    missing_by_field = defaultdict(list)  # field -> list of cities

    for filepath in yaml_files:
        issues = validate_file(filepath)
        all_issues[filepath.stem] = issues

        for item in issues['missing']:
            if len(item) == 2:
                section, field = item
                key = f"{section}.{field}"
            else:
                section, field, member = item
                key = f"{section}.{field}"
            missing_by_field[key].append(filepath.stem)

    # -------------------------------------------------------------------------
    # Output: Per-file details
    # -------------------------------------------------------------------------
    if not args.summary and not args.checklist:
        for city, issues in all_issues.items():
            if issues['errors'] or issues['warnings']:
                print(f"\n{'='*60}")
                print(f" {city.upper()}")
                print(f"{'='*60}")

                if issues['errors']:
                    print("\n  ERRORS (required fields):")
                    for err in issues['errors']:
                        print(f"    [X] {err}")

                if issues['warnings']:
                    print("\n  WARNINGS (data quality):")
                    for warn in issues['warnings']:
                        print(f"    [!] {warn}")

    # -------------------------------------------------------------------------
    # Output: Summary
    # -------------------------------------------------------------------------
    print(f"\n{'='*60}")
    print(" VALIDATION SUMMARY")
    print(f"{'='*60}")

    total_files = len(yaml_files)
    files_with_errors = sum(1 for issues in all_issues.values() if issues['errors'])
    files_with_warnings = sum(1 for issues in all_issues.values() if issues['warnings'])

    print(f"\n  Total files: {total_files}")
    print(f"  Files with errors: {files_with_errors}")
    print(f"  Files with warnings: {files_with_warnings}")
    print(f"  Files fully valid: {total_files - files_with_errors}")

    # -------------------------------------------------------------------------
    # Output: Data collection checklist
    # -------------------------------------------------------------------------
    if args.checklist or True:  # Always show checklist
        print(f"\n{'='*60}")
        print(" DATA COLLECTION CHECKLIST")
        print(f"{'='*60}")
        print("\n  Missing data that needs to be collected:\n")

        # Group by priority
        high_priority = []
        medium_priority = []
        low_priority = []

        for field, cities in sorted(missing_by_field.items()):
            count = len(cities)
            if count == 0:
                continue

            # Categorize by importance and frequency
            if field in ['broadcast.cable_channels', 'broadcast.live_stream', 'clerk.name']:
                high_priority.append((field, cities))
            elif field.startswith('member.bio'):
                low_priority.append((field, cities))
            elif count > 10:
                medium_priority.append((field, cities))
            else:
                high_priority.append((field, cities))

        if high_priority:
            print("  HIGH PRIORITY (likely available, just needs research):")
            for field, cities in high_priority:
                print(f"    • {field}: {len(cities)} cities")
                if len(cities) <= 5:
                    print(f"      Cities: {', '.join(sorted(cities))}")
            print()

        if medium_priority:
            print("  MEDIUM PRIORITY (many cities missing, may need standardization decision):")
            for field, cities in medium_priority:
                print(f"    • {field}: {len(cities)} cities")
            print()

        if low_priority:
            print("  LOW PRIORITY (nice to have):")
            for field, cities in low_priority:
                print(f"    • {field}: {len(cities)} cities")
            print()

    # -------------------------------------------------------------------------
    # Output: Cities needing broadcast info
    # -------------------------------------------------------------------------
    if 'broadcast.cable_channels' in missing_by_field:
        print(f"\n{'='*60}")
        print(" CITIES NEEDING BROADCAST INFO")
        print(f"{'='*60}")
        for city in sorted(missing_by_field.get('broadcast.cable_channels', [])):
            print(f"  • {city}")

    return 1 if files_with_errors > 0 else 0


if __name__ == '__main__':
    exit(main())
