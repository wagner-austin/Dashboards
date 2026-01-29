#!/usr/bin/env python3
"""
Verify seats_up matches members whose terms end in the next election year.

Usage:
    python verify_seats_up.py           # Check all cities
    python verify_seats_up.py tustin    # Check single city
    python verify_seats_up.py --fix     # Show suggested fixes
"""

import yaml
import argparse
from pathlib import Path


def get_members_up(members: list, election_year: int) -> list:
    """Get members whose terms end in the election year."""
    up = []
    for m in members:
        term_end = m.get('term_end')
        if term_end == election_year:
            up.append({
                'name': m.get('name'),
                'position': m.get('position'),
                'district': m.get('district'),
                'term_end': term_end
            })
    return up


def normalize_seat(seat) -> str:
    """Normalize seat representation for comparison."""
    if isinstance(seat, dict):
        return seat.get('district', str(seat))
    return str(seat)


def verify_city(filepath: Path, show_fix: bool = False) -> dict:
    """Verify seats_up for a city."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    city_name = data.get('city_name', filepath.stem)
    members = data.get('members', [])
    elections = data.get('elections', {})

    next_election = elections.get('next_election', '')
    if next_election:
        election_year = int(next_election[:4])
    else:
        election_year = 2026  # Default

    seats_up = elections.get('seats_up', [])
    members_up = get_members_up(members, election_year)

    result = {
        'city': city_name,
        'election_year': election_year,
        'seats_up': seats_up,
        'members_up': members_up,
        'issues': []
    }

    # Check if number of seats matches
    num_seats = len(seats_up)
    num_members = len(members_up)

    # Handle aggregate seats like "At-Large (3 seats)"
    for seat in seats_up:
        seat_str = normalize_seat(seat)
        if '(' in seat_str and 'seat' in seat_str.lower():
            # Extract number like "At-Large (3 seats)" -> 3
            import re
            match = re.search(r'\((\d+)\s*seat', seat_str.lower())
            if match:
                num_seats = num_seats - 1 + int(match.group(1))

    if num_seats != num_members:
        result['issues'].append(f"Count mismatch: seats_up={num_seats}, members_up={num_members}")

    # Check if members are represented in seats_up
    seats_str = [normalize_seat(s).lower() for s in seats_up]
    for m in members_up:
        district = m['district']
        position = m['position']
        name = m['name']

        # Check if this member's seat is in seats_up
        found = False
        for seat_str in seats_str:
            if district and district.lower() in seat_str:
                found = True
                break
            if position and position.lower() in seat_str:
                found = True
                break
            if 'at-large' in seat_str and district and 'at-large' in district.lower():
                found = True
                break

        if not found:
            result['issues'].append(f"Member not in seats_up: {name} ({position}, {district})")

    # Generate suggested fix
    if show_fix and members_up:
        suggested = []
        for m in members_up:
            district = m['district'] or m['position']
            suggested.append({
                'district': district,
                'incumbent': m['name']
            })
        result['suggested'] = suggested

    return result


def main():
    parser = argparse.ArgumentParser(description='Verify seats_up against member terms')
    parser.add_argument('city', nargs='?', help='Single city to check')
    parser.add_argument('--fix', action='store_true', help='Show suggested fixes')
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / '_council_data'

    if args.city:
        yaml_files = [data_dir / f'{args.city}.yaml']
    else:
        yaml_files = sorted(data_dir.glob('*.yaml'))

    issues_found = 0
    ok_count = 0

    for filepath in yaml_files:
        if not filepath.exists():
            print(f"File not found: {filepath}")
            continue

        result = verify_city(filepath, args.fix)

        if result['issues']:
            issues_found += 1
            print(f"\n[ISSUE] {result['city']} ({result['election_year']}):")
            for issue in result['issues']:
                print(f"  - {issue}")
            print(f"  seats_up: {result['seats_up']}")
            print(f"  members ending {result['election_year']}:")
            for m in result['members_up']:
                print(f"    - {m['name']} ({m['position']}, {m['district']})")
            if args.fix and 'suggested' in result:
                print(f"  suggested seats_up:")
                for s in result['suggested']:
                    print(f"    - district: {s['district']}")
                    print(f"      incumbent: {s['incumbent']}")
        else:
            ok_count += 1
            if args.city:  # Only show OK for single city
                print(f"[OK] {result['city']}: {len(result['members_up'])} seats match")

    print(f"\n{'='*60}")
    print(f"Summary: {ok_count} OK, {issues_found} with issues")


if __name__ == '__main__':
    main()
