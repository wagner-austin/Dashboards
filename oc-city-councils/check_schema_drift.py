#!/usr/bin/env python3
"""
Check schema drift between cities and the reference (Aliso Viejo).
Shows exactly what fields/sections are missing in each city.

Usage:
    python check_schema_drift.py              # Check all cities
    python check_schema_drift.py anaheim      # Check single city
    python check_schema_drift.py --summary    # Quick summary only
"""

import yaml
import sys
from pathlib import Path


def get_all_keys(d, prefix=''):
    """Recursively get all keys from a dict, with dot notation for nested keys."""
    keys = set()
    if isinstance(d, dict):
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.add(full_key)
            if isinstance(v, dict):
                keys.update(get_all_keys(v, full_key))
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                # For lists of dicts, check first item's structure
                keys.update(get_all_keys(v[0], f"{full_key}[]"))
    return keys


def load_yaml(filepath):
    """Load a YAML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def check_drift(reference: dict, target: dict, target_name: str) -> dict:
    """Compare target to reference and return missing fields."""
    ref_keys = get_all_keys(reference)
    target_keys = get_all_keys(target)

    missing = ref_keys - target_keys
    extra = target_keys - ref_keys

    # Check election history years
    ref_history = reference.get('elections', {}).get('history', [])
    target_history = target.get('elections', {}).get('history', [])

    ref_years = {h.get('year') for h in ref_history}
    target_years = {h.get('year') for h in target_history}

    missing_years = ref_years - target_years

    return {
        'city': target_name,
        'missing_fields': sorted(missing),
        'extra_fields': sorted(extra),
        'missing_years': sorted(missing_years),
        'has_years': sorted(target_years),
    }


def print_drift_report(drift: dict, verbose: bool = True):
    """Print drift report for a single city."""
    city = drift['city']
    missing = drift['missing_fields']
    missing_years = drift['missing_years']
    has_years = drift['has_years']

    # Filter out some expected differences (like specific member data)
    missing_important = [m for m in missing if not m.startswith('members[].')
                        and not m.startswith('elections.history[]')]

    has_issues = bool(missing_important) or bool(missing_years)

    if not has_issues and not verbose:
        return False

    status = "[DRIFT]" if has_issues else "[OK]"
    print(f"\n{status} {city}")

    if missing_years:
        print(f"  Missing election years: {missing_years}")
        print(f"  Has years: {has_years if has_years else 'none'}")

    if missing_important and verbose:
        print(f"  Missing fields ({len(missing_important)}):")
        # Group by section
        sections = {}
        for field in missing_important:
            section = field.split('.')[0]
            if section not in sections:
                sections[section] = []
            sections[section].append(field)

        for section, fields in sorted(sections.items()):
            print(f"    {section}:")
            for f in fields[:10]:  # Limit to 10 per section
                print(f"      - {f}")
            if len(fields) > 10:
                print(f"      ... and {len(fields) - 10} more")

    return has_issues


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Check schema drift against reference city')
    parser.add_argument('city', nargs='?', help='Check single city')
    parser.add_argument('--summary', action='store_true', help='Show summary only')
    parser.add_argument('--reference', default='aliso-viejo', help='Reference city (default: aliso-viejo)')
    args = parser.parse_args()

    data_dir = Path(__file__).parent / '_council_data'

    # Load reference
    ref_path = data_dir / f'{args.reference}.yaml'
    if not ref_path.exists():
        print(f"Error: Reference file not found: {ref_path}")
        sys.exit(1)

    reference = load_yaml(ref_path)
    ref_name = reference.get('city_name', args.reference)

    # Get election years from reference
    ref_history = reference.get('elections', {}).get('history', [])
    ref_years = sorted([h.get('year') for h in ref_history])

    print(f"Reference: {ref_name}")
    print(f"Election years required: {ref_years}")
    print(f"{'='*60}")

    # Check cities
    if args.city:
        yaml_files = [data_dir / f'{args.city}.yaml']
        if not yaml_files[0].exists():
            print(f"Error: File not found: {yaml_files[0]}")
            sys.exit(1)
    else:
        yaml_files = sorted(data_dir.glob('*.yaml'))
        yaml_files = [f for f in yaml_files if f.name != f'{args.reference}.yaml']

    issues_count = 0
    ok_count = 0

    for filepath in yaml_files:
        target = load_yaml(filepath)
        target_name = target.get('city_name', filepath.stem)

        drift = check_drift(reference, target, target_name)

        if args.summary:
            missing_years = drift['missing_years']
            has_years = len(drift['has_years'])
            missing_fields = len([m for m in drift['missing_fields']
                                 if not m.startswith('members[].')
                                 and not m.startswith('elections.history[]')])

            if missing_years or missing_fields > 5:
                print(f"[DRIFT] {target_name}: {len(missing_years)} missing years, ~{missing_fields} missing fields")
                issues_count += 1
            else:
                ok_count += 1
        else:
            has_issues = print_drift_report(drift, verbose=not args.summary)
            if has_issues:
                issues_count += 1
            else:
                ok_count += 1

    print(f"\n{'='*60}")
    print(f"Summary: {ok_count} OK, {issues_count} with drift")

    if issues_count > 0:
        print(f"\nTo fix drift, each city needs:")
        print(f"  - Election history for years: {ref_years}")
        print(f"  - All sections: members, meetings, portals, broadcast, clerk,")
        print(f"    public_comment, council, elections (with history, cycle_pattern, etc.)")


if __name__ == '__main__':
    main()
