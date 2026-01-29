#!/usr/bin/env python3
"""
Populate election history for all cities from OC Registrar data.
Creates history entries with winners and candidates for years 2012-2024.

Usage:
    python populate_history.py --dry-run      # Preview what would be added
    python populate_history.py                # Apply changes
    python populate_history.py tustin         # Single city
"""

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path
from ruamel.yaml import YAML


# City name mapping for special cases
CITY_NAME_MAP = {
    'la-habra': 'LA HABRA',
    'la-palma': 'LA PALMA',
    'rancho-santa-margarita': 'RANCHO SANTA MARGARITA',
    'san-clemente': 'SAN CLEMENTE',
    'san-juan-capistrano': 'SAN JUAN CAPISTRANO',
    'santa-ana': 'SANTA ANA',
    'lake-forest': 'LAKE FOREST',
    'laguna-beach': 'LAGUNA BEACH',
    'laguna-hills': 'LAGUNA HILLS',
    'laguna-niguel': 'LAGUNA NIGUEL',
    'laguna-woods': 'LAGUNA WOODS',
    'los-alamitos': 'LOS ALAMITOS',
    'mission-viejo': 'MISSION VIEJO',
    'newport-beach': 'NEWPORT BEACH',
    'seal-beach': 'SEAL BEACH',
    'villa-park': 'VILLA PARK',
    'yorba-linda': 'YORBA LINDA',
    'aliso-viejo': 'ALISO VIEJO',
    'buena-park': 'BUENA PARK',
    'costa-mesa': 'COSTA MESA',
    'dana-point': 'DANA POINT',
    'fountain-valley': 'FOUNTAIN VALLEY',
    'garden-grove': 'GARDEN GROVE',
    'huntington-beach': 'HUNTINGTON BEACH',
}


def parse_2024_2022(filepath: Path, year: int) -> dict:
    """Parse 2024/2022 format (tab-separated). Returns {contest: {candidate: votes}}"""
    results = defaultdict(lambda: defaultdict(int))
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            contest = row.get('Contest Title', '')
            if 'CITY OF' in contest and ('City Council' in contest or 'Mayor' in contest):
                candidate = row.get('Choice Name1') or row.get('Choice Name', '')
                if candidate and 'write-in' not in candidate.lower():
                    votes = int(row.get('Total Votes', 0) or 0)
                    results[contest][candidate] += votes
    return dict(results)


def parse_2020(filepath: Path) -> dict:
    """Parse 2020 format (CSV with header comment)."""
    results = defaultdict(lambda: defaultdict(int))
    with open(filepath, 'r', encoding='latin-1') as f:
        next(f)  # Skip format version line
        reader = csv.DictReader(f)
        for row in reader:
            contest = row.get('Contest Title', '')
            if 'CITY OF' in contest and ('City Council' in contest or 'Mayor' in contest):
                candidate = row.get('Choice Name', '')
                if candidate and 'write-in' not in candidate.lower():
                    votes = int(row.get('Total Votes', 0) or 0)
                    results[contest][candidate] += votes
    return dict(results)


def parse_2018_earlier(filepath: Path) -> dict:
    """Parse 2018/2016/2014/2012 format."""
    results = defaultdict(lambda: defaultdict(int))
    with open(filepath, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f)
        for row in reader:
            contest = row.get('Contest_title', '')
            if 'CITY OF' in contest.upper() and ('CITY COUNCIL' in contest.upper() or 'MAYOR' in contest.upper()):
                candidate = row.get('Candidate_name', '')
                if candidate and 'write-in' not in candidate.lower():
                    absentee = int(row.get('Absentee_votes', 0) or 0)
                    early = int(row.get('Early_votes', 0) or 0)
                    election = int(row.get('Election_Votes', 0) or 0)
                    votes = absentee + early + election
                    results[contest][candidate] += votes
    return dict(results)


def title_case_name(name: str) -> str:
    """Convert uppercase name to title case."""
    # Handle "LAST, FIRST" format
    if ',' in name:
        parts = name.split(',', 1)
        name = f"{parts[1].strip()} {parts[0].strip()}"

    words = name.split()
    result = []
    for word in words:
        if word.startswith('(') and word.endswith(')'):
            result.append('(' + word[1:-1].title() + ')')
        elif '.' in word:
            result.append(word.upper())  # Keep initials uppercase
        elif word.upper() in ('II', 'III', 'IV', 'JR', 'SR'):
            result.append(word.upper())
        else:
            result.append(word.title())
    return ' '.join(result)


def get_city_contests(all_data: dict, city_name: str) -> dict:
    """Extract contests for a specific city."""
    city_upper = city_name.upper()
    contests = {}

    for contest, candidates in all_data.items():
        # Match city name in contest title
        if city_upper in contest.upper():
            # Sort candidates by votes descending
            sorted_candidates = sorted(candidates.items(), key=lambda x: -x[1])
            contests[contest] = sorted_candidates

    return contests


def parse_contest_info(contest: str) -> dict:
    """Extract district/seat info from contest title."""
    info = {'type': 'at-large', 'district': None, 'is_mayor': False}

    if 'Mayor' in contest:
        info['is_mayor'] = True
        info['district'] = 'Mayor'

    # Check for district number
    district_match = re.search(r'District\s*(\d+)', contest, re.IGNORECASE)
    if district_match:
        info['type'] = 'by-district'
        info['district'] = f"District {district_match.group(1)}"

    return info


def determine_winners(candidates: list, num_seats: int = 1) -> list:
    """Determine winners from sorted candidate list."""
    winners = []
    for i, (name, votes) in enumerate(candidates[:num_seats]):
        winners.append({
            'name': title_case_name(name),
            'votes': votes
        })
    return winners


def build_history_entry(year: int, city_contests: dict, election_system: str) -> dict:
    """Build a history entry for a year."""
    entry = {
        'year': year,
        'type': election_system,
        'winners': [],
        'candidates': []
    }

    # Group by district
    district_results = {}
    has_mayor = False

    for contest, candidates in city_contests.items():
        info = parse_contest_info(contest)

        if info['is_mayor']:
            has_mayor = True
            district_results['Mayor'] = candidates
        elif info['district']:
            district_results[info['district']] = candidates
        else:
            # At-large - combine all candidates
            if 'At-Large' not in district_results:
                district_results['At-Large'] = []
            district_results['At-Large'].extend(candidates)

    # Process each district/seat
    for district, candidates in sorted(district_results.items()):
        if district == 'At-Large':
            # De-duplicate and re-sort at-large candidates
            unique = {}
            for name, votes in candidates:
                if name not in unique or votes > unique[name]:
                    unique[name] = votes
            candidates = sorted(unique.items(), key=lambda x: -x[1])

            # At-large typically has 2-3 seats
            num_seats = 2  # Default, could be smarter based on total candidates
            if len(candidates) >= 5:
                num_seats = 2

            for winner in candidates[:num_seats]:
                entry['winners'].append({
                    'seat': 'At-Large',
                    'winner': title_case_name(winner[0]),
                    'votes': winner[1]
                })

            # Add all candidates
            entry['candidates'].append({
                'district': 'At-Large',
                'candidates': [
                    {
                        'name': title_case_name(name),
                        'votes': votes,
                        'outcome': 'won' if i < num_seats else 'lost'
                    }
                    for i, (name, votes) in enumerate(candidates)
                ]
            })
        else:
            # District or Mayor - one winner
            if candidates:
                winner_name, winner_votes = candidates[0]

                if district == 'Mayor':
                    entry['winners'].append({
                        'seat': 'Mayor',
                        'winner': title_case_name(winner_name),
                        'votes': winner_votes
                    })
                else:
                    entry['winners'].append({
                        'district': district,
                        'winner': title_case_name(winner_name),
                        'votes': winner_votes
                    })

                # Add all candidates for this district
                entry['candidates'].append({
                    'district': district,
                    'candidates': [
                        {
                            'name': title_case_name(name),
                            'votes': votes,
                            'outcome': 'won' if i == 0 else 'lost'
                        }
                        for i, (name, votes) in enumerate(candidates)
                    ]
                })

    return entry if entry['winners'] else None


def load_all_election_data(base_path: Path) -> dict:
    """Load election data for all years."""
    data_sources = {
        2024: ('results-final.txt', parse_2024_2022),
        2022: ('results.txt', parse_2024_2022),
        2020: ('Detailed vote totals.CSV', parse_2020),
        2018: ('2018_data/contest_table.txt', parse_2018_earlier),
        2016: ('2016_data/contest_table.txt', parse_2018_earlier),
        2014: ('2014_data/contest_table.txt', parse_2018_earlier),
        2012: ('2012_data/contest_table.txt', parse_2018_earlier),
    }

    all_data = {}
    for year, (filename, parser) in data_sources.items():
        filepath = base_path / filename
        if filepath.exists():
            if year in [2024, 2022]:
                all_data[year] = parser(filepath, year)
            else:
                all_data[year] = parser(filepath)
            print(f"  Loaded {year}: {len(all_data[year])} contests")
        else:
            print(f"  Missing: {filename}")

    return all_data


def process_city(city_slug: str, yaml_path: Path, all_data: dict, dry_run: bool) -> dict:
    """Process a single city's YAML file."""
    report = {'city': city_slug, 'added': [], 'skipped': [], 'errors': []}

    # Setup YAML - use default_flow_style=False for block style
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 120
    yaml.default_flow_style = False
    yaml.indent(mapping=2, sequence=4, offset=2)

    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.load(f)

    city_name = data.get('city_name', city_slug.replace('-', ' ').title())
    election_system = data.get('elections', {}).get('election_system', 'at-large')

    # Get or use mapped city name for OC data lookup
    lookup_name = CITY_NAME_MAP.get(city_slug, city_name.upper())

    # Get existing history
    if 'elections' not in data:
        data['elections'] = {}
    if 'history' not in data['elections']:
        data['elections']['history'] = []

    existing_years = {h.get('year') for h in data['elections']['history']}

    # Process each year
    for year in sorted(all_data.keys(), reverse=True):
        if year in existing_years:
            report['skipped'].append(f"{year}: already exists")
            continue

        city_contests = get_city_contests(all_data[year], lookup_name)

        if not city_contests:
            report['skipped'].append(f"{year}: no contests found")
            continue

        # Build history entry
        entry = build_history_entry(year, city_contests, election_system)

        if entry:
            data['elections']['history'].append(entry)
            winners_summary = ', '.join([w.get('winner', w.get('name', '?')) for w in entry['winners'][:3]])
            report['added'].append(f"{year}: {len(entry['winners'])} winners ({winners_summary}...)")
        else:
            report['skipped'].append(f"{year}: no valid contests")

    # Sort history by year descending
    data['elections']['history'].sort(key=lambda x: -x.get('year', 0))

    # Save if not dry run
    if not dry_run and report['added']:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)

    return report


def main():
    parser = argparse.ArgumentParser(description='Populate election history from OC data')
    parser.add_argument('city', nargs='?', help='Single city slug to process')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    args = parser.parse_args()

    base_path = Path(__file__).parent
    yaml_dir = base_path.parent / '_council_data'

    print("Loading election data...")
    all_data = load_all_election_data(base_path)
    print()

    # Get cities to process
    if args.city:
        yaml_files = [yaml_dir / f'{args.city}.yaml']
    else:
        yaml_files = sorted(yaml_dir.glob('*.yaml'))

    print(f"Processing {len(yaml_files)} cities...")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLY CHANGES'}")
    print("=" * 60)

    total_added = 0
    for yaml_path in yaml_files:
        city_slug = yaml_path.stem
        report = process_city(city_slug, yaml_path, all_data, args.dry_run)

        if report['added']:
            print(f"\n{report['city']}:")
            for item in report['added']:
                print(f"  + {item}")
                total_added += 1

    print(f"\n{'=' * 60}")
    print(f"Total: {total_added} history entries {'would be ' if args.dry_run else ''}added")
    if args.dry_run:
        print("(No files modified - run without --dry-run to apply)")


if __name__ == '__main__':
    main()
