#!/usr/bin/env python3
"""
Validate OC Registrar election data against existing YAML data.
This script compares parsed election results to ensure data quality before bulk import.
"""

import csv
import re
import yaml
from collections import defaultdict
from pathlib import Path


def parse_2024_2022(filepath, year):
    """Parse 2024/2022 format (tab-separated)."""
    results = defaultdict(lambda: defaultdict(int))

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            contest = row.get('Contest Title', '')
            if 'CITY OF' in contest and ('Member, City Council' in contest or 'Mayor' in contest):
                candidate = row.get('Choice Name1') or row.get('Choice Name', '')
                if candidate and 'write-in' not in candidate.lower():
                    votes = int(row.get('Total Votes', 0) or 0)
                    results[contest][candidate] += votes

    return results


def parse_2020(filepath):
    """Parse 2020 format (CSV with header on line 2)."""
    results = defaultdict(lambda: defaultdict(int))

    with open(filepath, 'r', encoding='latin-1') as f:
        next(f)  # Skip format version line
        reader = csv.DictReader(f)
        for row in reader:
            contest = row.get('Contest Title', '')
            if 'CITY OF' in contest and ('Member, City Council' in contest or 'Mayor' in contest):
                candidate = row.get('Choice Name', '')
                if candidate and 'write-in' not in candidate.lower():
                    votes = int(row.get('Total Votes', 0) or 0)
                    results[contest][candidate] += votes

    return results


def parse_2018_2016(filepath):
    """Parse 2018/2016 format (CSV with different column names)."""
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

    return results


def parse_2014_2012(filepath):
    """Parse 2014/2012 format (similar to 2018/2016 but may have variations)."""
    return parse_2018_2016(filepath)


def extract_city_from_contest(contest):
    """Extract city name from contest title."""
    match = re.search(r'CITY OF ([A-Z\s]+)', contest, re.IGNORECASE)
    if match:
        return match.group(1).strip().title().replace(' ', '-').lower()
    return None


def extract_district_from_contest(contest):
    """Extract district from contest title."""
    if 'Mayor' in contest:
        return 'Mayor'
    match = re.search(r'District\s*(\d+)', contest, re.IGNORECASE)
    if match:
        return f'District {match.group(1)}'
    # At-large seats
    if 'At Large' in contest or 'At-Large' in contest:
        return 'At-Large'
    return 'Unknown'


def normalize_name(name):
    """Normalize candidate name for comparison."""
    # Remove middle initials, suffixes, etc.
    name = re.sub(r'\s+', ' ', name).strip()
    # Handle comma-separated last,first format
    if ',' in name:
        parts = name.split(',')
        name = f"{parts[1].strip()} {parts[0].strip()}"
    # Remove parenthetical nicknames like "(BILL)"
    name = re.sub(r'\([^)]+\)', '', name)
    # Remove middle initials like "W." or "A."
    name = re.sub(r'\s+[A-Z]\.\s*', ' ', name)
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name).strip()
    return name.lower()


def load_yaml(city_slug):
    """Load YAML file for a city."""
    yaml_path = Path(__file__).parent.parent / '_council_data' / f'{city_slug}.yaml'
    if yaml_path.exists():
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return None


def get_yaml_results(yaml_data, year):
    """Extract election results from YAML for a specific year."""
    results = {}
    elections = yaml_data.get('elections', {})
    history = elections.get('history', [])

    for election in history:
        if election.get('year') == year:
            election_type = election.get('type', 'general')
            for i, winner in enumerate(election.get('winners', [])):
                # Handle both district and seat field names
                district = winner.get('district') or winner.get('seat') or 'At-Large'

                # For at-large with multiple winners, use index to differentiate
                if district == 'At-Large' and i > 0:
                    key = f'At-Large-{i+1}'
                else:
                    key = district

                results[key] = {
                    'winner': winner.get('winner'),
                    'winner_votes': winner.get('votes'),
                    'runner_up': winner.get('runner_up'),
                    'runner_up_votes': winner.get('runner_up_votes'),
                    'election_type': election_type
                }
    return results


def validate_city_year(oc_data, city_slug, year):
    """Validate OC Registrar data against YAML for a specific city and year."""
    yaml_data = load_yaml(city_slug)
    if not yaml_data:
        return {'status': 'no_yaml', 'message': f'No YAML file found for {city_slug}'}

    yaml_results = get_yaml_results(yaml_data, year)
    if not yaml_results:
        return {'status': 'no_year', 'message': f'No {year} results in YAML for {city_slug}'}

    # Check if this was an at-large election
    is_at_large = any(r.get('election_type') == 'at-large' for r in yaml_results.values())

    # Filter OC data for this city
    city_name = yaml_data.get('city_name', '').upper()
    city_contests = {}
    # Also collect all candidates for at-large matching
    all_city_candidates = {}

    for contest, candidates in oc_data.items():
        if city_name in contest.upper():
            district = extract_district_from_contest(contest)
            sorted_candidates = dict(sorted(candidates.items(), key=lambda x: -x[1]))
            city_contests[district] = sorted_candidates
            # For at-large, merge all candidates
            for name, votes in sorted_candidates.items():
                all_city_candidates[name] = votes

    # Compare results
    matches = []
    mismatches = []
    missing_in_oc = []
    extra_in_oc = []

    for district, yaml_result in yaml_results.items():
        yaml_winner = yaml_result['winner']
        yaml_votes = yaml_result['winner_votes']

        # For at-large elections, search all candidates
        if is_at_large and 'At-Large' in district:
            found = False
            for oc_name, oc_votes in all_city_candidates.items():
                if normalize_name(oc_name) == normalize_name(yaml_winner) or \
                   yaml_winner.lower() in oc_name.lower() or \
                   oc_name.lower() in yaml_winner.lower():
                    found = True
                    if yaml_votes is None or oc_votes == yaml_votes:
                        matches.append({
                            'district': district,
                            'candidate': yaml_winner,
                            'votes': yaml_votes,
                            'oc_name': oc_name,
                            'oc_votes': oc_votes
                        })
                    else:
                        mismatches.append({
                            'district': district,
                            'type': 'vote_count',
                            'candidate': yaml_winner,
                            'yaml_votes': yaml_votes,
                            'oc_votes': oc_votes,
                            'oc_name': oc_name
                        })
                    break
            if not found:
                missing_in_oc.append({
                    'district': district,
                    'winner': yaml_winner,
                    'votes': yaml_votes,
                    'note': 'Not found in OC Registrar data'
                })
            continue

        if district in city_contests:
            oc_candidates = city_contests[district]
            oc_sorted = list(oc_candidates.items())

            if len(oc_sorted) >= 1:
                oc_winner = oc_sorted[0]

                # Check winner match
                if normalize_name(oc_winner[0]) == normalize_name(yaml_winner) or \
                   yaml_winner.lower() in oc_winner[0].lower() or \
                   oc_winner[0].lower() in yaml_winner.lower():
                    if yaml_votes is None or oc_winner[1] == yaml_votes:
                        matches.append({
                            'district': district,
                            'candidate': yaml_winner,
                            'votes': yaml_votes,
                            'oc_name': oc_winner[0]
                        })
                    else:
                        mismatches.append({
                            'district': district,
                            'type': 'vote_count',
                            'candidate': yaml_winner,
                            'yaml_votes': yaml_votes,
                            'oc_votes': oc_winner[1],
                            'oc_name': oc_winner[0]
                        })
                else:
                    mismatches.append({
                        'district': district,
                        'type': 'winner_name',
                        'yaml_winner': yaml_winner,
                        'yaml_votes': yaml_votes,
                        'oc_winner': oc_winner[0],
                        'oc_votes': oc_winner[1]
                    })

                # Check runner-up if present
                if yaml_result.get('runner_up') and len(oc_sorted) >= 2:
                    oc_runner_up = oc_sorted[1]
                    yaml_runner_up = yaml_result['runner_up']
                    yaml_runner_up_votes = yaml_result['runner_up_votes']

                    if normalize_name(oc_runner_up[0]) == normalize_name(yaml_runner_up) or \
                       yaml_runner_up.lower() in oc_runner_up[0].lower() or \
                       oc_runner_up[0].lower() in yaml_runner_up.lower():
                        if yaml_runner_up_votes is None or oc_runner_up[1] == yaml_runner_up_votes:
                            matches.append({
                                'district': f'{district} (runner-up)',
                                'candidate': yaml_runner_up,
                                'votes': yaml_runner_up_votes,
                                'oc_name': oc_runner_up[0]
                            })
                        else:
                            mismatches.append({
                                'district': f'{district} (runner-up)',
                                'type': 'vote_count',
                                'candidate': yaml_runner_up,
                                'yaml_votes': yaml_runner_up_votes,
                                'oc_votes': oc_runner_up[1],
                                'oc_name': oc_runner_up[0]
                            })
        else:
            missing_in_oc.append({
                'district': district,
                'winner': yaml_result['winner'],
                'votes': yaml_result['winner_votes'],
                'note': 'Possibly unopposed (no election held)'
            })

    # Check for extra districts in OC data
    for district in city_contests:
        if district not in yaml_results:
            candidates = list(city_contests[district].items())
            extra_in_oc.append({
                'district': district,
                'candidates': candidates[:3]  # Top 3
            })

    return {
        'status': 'validated',
        'matches': matches,
        'mismatches': mismatches,
        'missing_in_oc': missing_in_oc,
        'extra_in_oc': extra_in_oc
    }


def print_validation_report(city_slug, year, result):
    """Print a formatted validation report."""
    print(f"\n{'='*70}")
    print(f"VALIDATION: {city_slug.upper()} - {year}")
    print(f"{'='*70}")

    if result['status'] in ['no_yaml', 'no_year']:
        print(f"  SKIPPED: {result['message']}")
        return

    if result['matches']:
        print(f"\n  MATCHES ({len(result['matches'])}):")
        for m in result['matches']:
            votes_str = f"{m['votes']:,}" if m['votes'] else "N/A"
            print(f"    [OK] {m['district']}: {m['candidate']} = {votes_str} votes")
            if m.get('oc_name') != m['candidate']:
                print(f"         (OC name: {m['oc_name']})")

    if result['mismatches']:
        print(f"\n  MISMATCHES ({len(result['mismatches'])}):")
        for m in result['mismatches']:
            if m['type'] == 'vote_count':
                yaml_v = m['yaml_votes'] or 0
                oc_v = m['oc_votes'] or 0
                diff = oc_v - yaml_v
                print(f"    [!] {m['district']}: {m['candidate']}")
                print(f"        YAML: {yaml_v:,} vs OC: {oc_v:,} (diff: {diff:+,})")
            else:
                print(f"    [!] {m['district']}: Winner mismatch")
                yaml_v = m['yaml_votes'] or 0
                oc_v = m['oc_votes'] or 0
                print(f"        YAML: {m['yaml_winner']} ({yaml_v:,})")
                print(f"        OC:   {m['oc_winner']} ({oc_v:,})")

    if result['missing_in_oc']:
        print(f"\n  MISSING IN OC REGISTRAR ({len(result['missing_in_oc'])}):")
        for m in result['missing_in_oc']:
            votes_str = f"({m['votes']:,})" if m['votes'] else "(no votes recorded)"
            print(f"    [?] {m['district']}: {m['winner']} {votes_str} - {m['note']}")

    if result['extra_in_oc']:
        print(f"\n  EXTRA IN OC REGISTRAR ({len(result['extra_in_oc'])}):")
        for m in result['extra_in_oc']:
            print(f"    [+] {m['district']}:")
            for name, votes in m['candidates']:
                print(f"        {name}: {votes:,}")

    # Summary
    total_yaml = len(result['matches']) + len(result['mismatches'])
    match_rate = len(result['matches']) / total_yaml * 100 if total_yaml > 0 else 0
    print(f"\n  SUMMARY: {len(result['matches'])}/{total_yaml} matched ({match_rate:.1f}%)")


def main():
    base_path = Path(__file__).parent

    # Load all data sources
    data_sources = {
        2024: ('results-final.txt', parse_2024_2022),
        2022: ('results.txt', parse_2024_2022),
        2020: ('Detailed vote totals.CSV', parse_2020),
        2018: ('2018_data/contest_table.txt', parse_2018_2016),
        2016: ('2016_data/contest_table.txt', parse_2018_2016),
        2014: ('2014_data/contest_table.txt', parse_2014_2012),
        2012: ('2012_data/contest_table.txt', parse_2014_2012),
    }

    # Cities to validate
    cities = ['anaheim', 'aliso-viejo']
    years = [2024, 2022, 2020, 2018, 2016]

    all_results = {}

    for year, (filename, parser) in data_sources.items():
        filepath = base_path / filename
        if filepath.exists():
            if year in [2024, 2022]:
                all_results[year] = parser(filepath, year)
            else:
                all_results[year] = parser(filepath)

    # Validate each city/year combination
    for city in cities:
        for year in years:
            if year in all_results:
                result = validate_city_year(all_results[year], city, year)
                print_validation_report(city, year, result)


if __name__ == '__main__':
    main()
