#!/usr/bin/env python3
"""
Calculate term limit tracking for council members.

For each member in cities with term limits, calculates:
- terms_since_cutoff: Terms served since term limits took effect
- terms_remaining: Terms they can still serve before terming out
- eligible_years: Election years they can run in
- term_out_year: Year they'd term out (if they keep winning)
- eligible_again: First year they can run again after terming out

Run: python calculate_term_limits.py [city-slug]
     python calculate_term_limits.py aliso-viejo
     python calculate_term_limits.py --all
"""

import yaml
import sys
import re
from pathlib import Path
from datetime import datetime

CURRENT_YEAR = datetime.now().year


def parse_cycle_years(cycle_str: str) -> list[int]:
    """
    Parse cycle pattern like "2024, 2028, 2032..." into a list of years.
    Generates years up to 2050.
    """
    if not cycle_str:
        return []

    # Extract the first few years from the pattern
    years = re.findall(r'\d{4}', cycle_str)
    if len(years) < 2:
        return [int(y) for y in years]

    # Calculate the interval
    first_years = [int(y) for y in years[:2]]
    interval = first_years[1] - first_years[0]

    # Generate years up to 2050
    result = []
    year = first_years[0]
    while year <= 2050:
        result.append(year)
        year += interval

    return result


def get_district_cycle(elections: dict, district: str) -> list[int]:
    """Get the election years for a specific district."""
    cycle_pattern = elections.get('cycle_pattern', {})

    for group_name, group_data in cycle_pattern.items():
        if group_name.startswith('group_'):
            seats = group_data.get('seats', [])
            # Check if district matches any seat pattern
            for seat in seats:
                if district in seat or seat in district or district == seat:
                    return parse_cycle_years(group_data.get('years', ''))

    # Fallback: assume every election year based on term length
    term_length = elections.get('term_length', 4)
    base_year = 2024
    return list(range(base_year, 2051, term_length))


def calculate_terms_since_cutoff(member: dict, cutoff_year: int) -> int:
    """
    Calculate how many terms a member has served since the cutoff.
    Only counts terms that STARTED on or after the cutoff year.
    """
    term_start = member.get('term_start')
    if not term_start:
        return 0

    if term_start >= cutoff_year:
        return 1  # Currently serving 1 term since cutoff

    return 0


def calculate_term_tracking(member: dict, elections: dict) -> dict | None:
    """
    Calculate term limit tracking for a single member.
    Returns None if city has no term limits.
    """
    term_limit = elections.get('term_limit')
    if not term_limit:
        return None

    # Get term limit parameters
    term_limit_effective = elections.get('term_limit_effective')
    term_limit_type = elections.get('term_limit_type', 'terms')  # 'terms' or 'years'
    cutoff_date = term_limit_effective  # Keep full date for comparison
    if term_limit_effective:
        cutoff_year = int(str(term_limit_effective)[:4])
    else:
        cutoff_year = 2000  # Default to counting all terms
        cutoff_date = None

    term_length = elections.get('term_length', 4)
    cooldown = elections.get('term_limit_cooldown', 0)
    cooldown_unit = elections.get('term_limit_cooldown_unit', 'cycles')  # 'cycles' or 'years'

    # Calculate cooldown in years based on unit
    if cooldown:
        if cooldown_unit == 'years':
            cooldown_years = cooldown
        else:  # cycles - assume 1 cycle = term_length years (typically 4)
            cooldown_years = cooldown * term_length
    else:
        cooldown_years = term_length

    # Get member info
    district = member.get('district', 'At-Large')
    term_start = member.get('term_start')
    term_end = member.get('term_end')
    term_start_date = member.get('term_start_date')  # Exact date if available
    name = member.get('name', 'Unknown')

    if not term_start:
        return None

    # Get election cycle for this district
    district_cycle = get_district_cycle(elections, district)

    # Calculate terms since cutoff
    # Use exact date comparison if both term_start_date and cutoff_date are available
    terms_since_cutoff = 0

    # Check if current term started after cutoff
    if cutoff_date and term_start_date:
        # Exact date comparison
        if term_start_date >= cutoff_date:
            terms_since_cutoff = 1
    elif term_start >= cutoff_year:
        # Fall back to year comparison
        terms_since_cutoff = 1

    # Check for previous terms by looking at election history
    # For now, we'll use a simple heuristic based on term_start
    # A more accurate version would parse the history section

    # Handle appointed members serving < 2 years (doesn't count)
    bio = member.get('bio', '').lower()
    if 'appointed' in bio:
        # Check if serving less than 2 years
        if term_end and term_start:
            years_served = term_end - term_start
            if years_served < 2:
                terms_since_cutoff = 0

    # Convert term_limit to max terms if type is 'years'
    if term_limit_type == 'years':
        max_terms = term_limit // term_length  # 8 years / 4 year term = 2 terms max
    else:
        max_terms = term_limit

    # Calculate terms remaining
    terms_remaining = max(0, max_terms - terms_since_cutoff)

    # Calculate eligible election years
    eligible_years = []
    term_out_year = None

    if terms_remaining > 0:
        # Find next election years for this district
        for year in district_cycle:
            if year >= CURRENT_YEAR:
                if len(eligible_years) < terms_remaining:
                    eligible_years.append(year)
                else:
                    term_out_year = year
                    break
    else:
        # Already termed out
        term_out_year = term_end

    # If they have eligible years, term_out is after their last eligible win
    if eligible_years and not term_out_year:
        last_eligible = eligible_years[-1]
        # Find the next election after their last eligible win + term_length
        for year in district_cycle:
            if year > last_eligible:
                term_out_year = year
                break

    # Calculate when they're eligible again after terming out
    eligible_again = None
    if term_out_year:
        # They need to wait cooldown_years after their term ends
        # Term ends = term_out_year (election they can't run in)
        # So they're off the council starting term_out_year
        # Eligible again after cooldown
        min_eligible_year = term_out_year + cooldown_years
        for year in district_cycle:
            if year >= min_eligible_year:
                eligible_again = year
                break

    return {
        'name': name,
        'district': district,
        'term_start': term_start,
        'term_end': term_end,
        'term_start_date': term_start_date,
        'terms_since_cutoff': terms_since_cutoff,
        'terms_remaining': terms_remaining,
        'eligible_years': eligible_years,
        'term_out_year': term_out_year,
        'eligible_again': eligible_again,
        'term_limit_type': term_limit_type,
    }


def process_city(filepath: Path) -> dict | None:
    """Process a single city YAML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

    if not data:
        return None

    elections = data.get('elections', {})
    members = data.get('members', [])

    if not elections.get('term_limit'):
        return {
            'city': data.get('city_name', filepath.stem),
            'has_term_limits': False,
            'members': []
        }

    # Calculate tracking for each member
    member_tracking = []
    for member in members:
        tracking = calculate_term_tracking(member, elections)
        if tracking:
            member_tracking.append(tracking)

    return {
        'city': data.get('city_name', filepath.stem),
        'has_term_limits': True,
        'term_limit': elections.get('term_limit'),
        'term_limit_type': elections.get('term_limit_type', 'terms'),
        'term_limit_effective': elections.get('term_limit_effective'),
        'term_limit_cooldown': elections.get('term_limit_cooldown'),
        'term_limit_cooldown_unit': elections.get('term_limit_cooldown_unit', 'cycles'),
        'term_limit_source': elections.get('term_limit_source'),
        'members': member_tracking
    }


def print_city_report(result: dict):
    """Print a formatted report for a city."""
    print(f"\n{'='*70}")
    print(f"  {result['city']}")
    print(f"{'='*70}")

    if not result['has_term_limits']:
        print("  No term limits")
        return

    limit_type = result.get('term_limit_type', 'terms')
    print(f"  Term Limit: {result['term_limit']} consecutive {limit_type}")
    if result.get('term_limit_effective'):
        print(f"  Effective: {result['term_limit_effective']}")
    if result.get('term_limit_cooldown'):
        cooldown_unit = result.get('term_limit_cooldown_unit', 'cycles')
        print(f"  Cooldown: {result['term_limit_cooldown']} {cooldown_unit}")

    print(f"\n  {'Member':<25} {'District':<12} {'Terms':<8} {'Remaining':<10} {'Eligible':<20} {'Term Out':<10} {'Again':<8}")
    print(f"  {'-'*25} {'-'*12} {'-'*8} {'-'*10} {'-'*20} {'-'*10} {'-'*8}")

    for m in result['members']:
        eligible_str = ', '.join(str(y) for y in m['eligible_years']) if m['eligible_years'] else '-'
        term_out_str = str(m['term_out_year']) if m['term_out_year'] else '-'
        again_str = str(m['eligible_again']) if m['eligible_again'] else '-'

        print(f"  {m['name']:<25} {m['district']:<12} {m['terms_since_cutoff']:<8} {m['terms_remaining']:<10} {eligible_str:<20} {term_out_str:<10} {again_str:<8}")


def main():
    data_dir = Path(__file__).parent / '_council_data'

    if len(sys.argv) < 2:
        print("Usage: python calculate_term_limits.py [city-slug|--all]")
        print("       python calculate_term_limits.py aliso-viejo")
        print("       python calculate_term_limits.py --all")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == '--all':
        yaml_files = sorted(data_dir.glob('*.yaml'))
        for filepath in yaml_files:
            result = process_city(filepath)
            if result and result['has_term_limits']:
                print_city_report(result)
    else:
        filepath = data_dir / f"{arg}.yaml"
        if not filepath.exists():
            print(f"Error: File not found: {filepath}")
            sys.exit(1)

        result = process_city(filepath)
        if result:
            print_city_report(result)


if __name__ == '__main__':
    main()
