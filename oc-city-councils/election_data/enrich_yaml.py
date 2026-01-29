#!/usr/bin/env python3
"""
Enrich a single YAML file with OC Registrar election data.
Adds vote counts and all candidates (losers) to election history.
Uses ruamel.yaml to preserve comments and formatting.

Usage:
    python enrich_yaml.py aliso-viejo --dry-run   # Preview changes
    python enrich_yaml.py aliso-viejo             # Apply changes
"""

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

from ruamel.yaml import YAML


def parse_2024_2022(filepath: Path, year: int) -> dict:
    """Parse 2024/2022 format (tab-separated)."""
    results: dict = defaultdict(lambda: defaultdict(int))
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            contest = row.get('Contest Title', '')
            if 'CITY OF' in contest and ('Member, City Council' in contest or 'Mayor' in contest):
                candidate = row.get('Choice Name1') or row.get('Choice Name', '')
                if candidate and 'write-in' not in candidate.lower():
                    votes = int(row.get('Total Votes', 0) or 0)
                    results[contest][candidate] += votes
    return dict(results)


def parse_2020(filepath: Path) -> dict:
    """Parse 2020 format (CSV with header on line 2)."""
    results: dict = defaultdict(lambda: defaultdict(int))
    with open(filepath, 'r', encoding='latin-1') as f:
        next(f)
        reader = csv.DictReader(f)
        for row in reader:
            contest = row.get('Contest Title', '')
            if 'CITY OF' in contest and ('Member, City Council' in contest or 'Mayor' in contest):
                candidate = row.get('Choice Name', '')
                if candidate and 'write-in' not in candidate.lower():
                    votes = int(row.get('Total Votes', 0) or 0)
                    results[contest][candidate] += votes
    return dict(results)


def parse_2018_2016(filepath: Path) -> dict:
    """Parse 2018/2016/2014/2012 format."""
    results: dict = defaultdict(lambda: defaultdict(int))
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


def normalize_name(name: str) -> str:
    """Normalize candidate name for comparison."""
    name = re.sub(r'\s+', ' ', name).strip()
    if ',' in name:
        parts = name.split(',')
        name = f"{parts[1].strip()} {parts[0].strip()}"
    name = re.sub(r'\([^)]+\)', '', name)
    name = re.sub(r'\s+[A-Z]\.\s*', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.lower()


def title_case_name(name: str) -> str:
    """Convert uppercase name to title case."""
    words = name.split()
    result = []
    for word in words:
        if word.startswith('(') and word.endswith(')'):
            result.append('(' + word[1:-1].title() + ')')
        elif '.' in word:
            result.append(word.upper())
        else:
            result.append(word.title())
    return ' '.join(result)


def get_city_data(oc_data: dict, city_name: str) -> dict:
    """Extract all contests for a city from OC data."""
    city_upper = city_name.upper()
    city_contests = {}

    for contest, candidates in oc_data.items():
        if city_upper in contest.upper():
            sorted_candidates = sorted(candidates.items(), key=lambda x: -x[1])
            city_contests[contest] = sorted_candidates

    return city_contests


def match_winner(yaml_winner: str, oc_candidates: list) -> tuple:
    """Find matching candidate in OC data."""
    yaml_norm = normalize_name(yaml_winner)
    for oc_name, votes in oc_candidates:
        if normalize_name(oc_name) == yaml_norm or \
           yaml_winner.lower() in oc_name.lower() or \
           oc_name.lower() in yaml_winner.lower():
            return oc_name, votes
    return None, None


def enrich_election(election: dict, oc_data: dict, city_name: str, year: int) -> tuple:
    """Enrich a single election entry with OC data."""
    city_contests = get_city_data(oc_data, city_name)

    if not city_contests:
        return None, f"No OC data found for {city_name} in {year}"

    changes = []
    election_type = election.get('type', 'general')
    is_at_large = election_type == 'at-large'

    # For at-large, merge all candidates
    all_candidates = []
    if is_at_large:
        for contest, candidates in city_contests.items():
            all_candidates.extend(candidates)
        all_candidates = sorted(all_candidates, key=lambda x: -x[1])

    winners = election.get('winners', [])

    for winner_entry in winners:
        yaml_winner = winner_entry.get('winner')
        district = winner_entry.get('district') or winner_entry.get('seat')

        if is_at_large:
            oc_name, votes = match_winner(yaml_winner, all_candidates)
        else:
            matched_contest = None
            for contest in city_contests:
                if district and district.replace('District ', '') in contest:
                    matched_contest = contest
                    break
                if district and 'Mayor' in district and 'Mayor' in contest:
                    matched_contest = contest
                    break

            if matched_contest:
                oc_name, votes = match_winner(yaml_winner, city_contests[matched_contest])
            else:
                oc_name, votes = None, None

        if oc_name and votes:
            old_votes = winner_entry.get('votes')
            if old_votes != votes:
                winner_entry['votes'] = votes
                changes.append(f"  {district}: {yaml_winner} votes: {old_votes} -> {votes}")

    # Add candidates (losers) if not present
    if 'candidates' not in election and not is_at_large:
        # Build a map of normalized winner names to their exact YAML names
        winner_name_map = {}
        for w in winners:
            yaml_name = w.get('winner')
            if yaml_name:
                winner_name_map[normalize_name(yaml_name)] = yaml_name

        candidates_list = []
        for contest, candidates in city_contests.items():
            district_match = re.search(r'District\s*(\d+)', contest, re.IGNORECASE)
            if district_match:
                district = f"District {district_match.group(1)}"
            elif 'Mayor' in contest:
                district = 'Mayor'
            else:
                continue

            candidate_entries = []
            for i, (name, votes) in enumerate(candidates):
                # Use winner's exact name if this candidate matches a winner
                norm_name = normalize_name(name)
                if norm_name in winner_name_map:
                    display_name = winner_name_map[norm_name]
                else:
                    display_name = title_case_name(name)

                entry = {
                    'name': display_name,
                    'votes': votes,
                    'outcome': 'won' if i == 0 else 'lost'
                }
                candidate_entries.append(entry)

            if candidate_entries:
                candidates_list.append({
                    'district': district,
                    'candidates': candidate_entries
                })

        if candidates_list:
            election['candidates'] = candidates_list
            changes.append(f"  Added {len(candidates_list)} district candidate lists")

    # For at-large, add all candidates
    if 'candidates' not in election and is_at_large and all_candidates:
        num_winners = len(winners)

        # Build a map of normalized winner names to their exact YAML names
        winner_name_map = {}
        for w in winners:
            yaml_name = w.get('winner')
            if yaml_name:
                winner_name_map[normalize_name(yaml_name)] = yaml_name

        candidate_entries = []
        for i, (name, votes) in enumerate(all_candidates):
            # Use winner's exact name if this candidate matches a winner
            norm_name = normalize_name(name)
            if norm_name in winner_name_map:
                display_name = winner_name_map[norm_name]
            else:
                display_name = title_case_name(name)

            entry = {
                'name': display_name,
                'votes': votes,
                'outcome': 'won' if i < num_winners else 'lost'
            }
            candidate_entries.append(entry)

        election['candidates'] = [{
            'district': 'At-Large',
            'candidates': candidate_entries
        }]
        changes.append(f"  Added at-large candidate list ({len(candidate_entries)} candidates)")

    return changes, None


def main() -> int:
    parser = argparse.ArgumentParser(description='Enrich YAML with OC Registrar data')
    parser.add_argument('city', help='City slug (e.g., aliso-viejo)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    args = parser.parse_args()

    base_path = Path(__file__).parent
    yaml_path = base_path.parent / '_council_data' / f'{args.city}.yaml'

    if not yaml_path.exists():
        print(f"Error: YAML file not found: {yaml_path}")
        return 1

    # Setup ruamel.yaml to preserve formatting
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 120

    # Load YAML
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.load(f)

    city_name = data.get('city_name', args.city.replace('-', ' ').title())

    # Load all OC data
    data_sources = {
        2024: ('results-final.txt', parse_2024_2022),
        2022: ('results.txt', parse_2024_2022),
        2020: ('Detailed vote totals.CSV', parse_2020),
        2018: ('2018_data/contest_table.txt', parse_2018_2016),
        2016: ('2016_data/contest_table.txt', parse_2018_2016),
        2014: ('2014_data/contest_table.txt', parse_2018_2016),
        2012: ('2012_data/contest_table.txt', parse_2018_2016),
    }

    oc_data = {}
    for year, (filename, parser_func) in data_sources.items():
        filepath = base_path / filename
        if filepath.exists():
            if year in [2024, 2022]:
                oc_data[year] = parser_func(filepath, year)
            else:
                oc_data[year] = parser_func(filepath)

    # Process elections
    elections = data.get('elections', {})
    history = elections.get('history', [])

    print(f"\n{'='*60}")
    print(f"ENRICHING: {city_name}")
    print(f"{'='*60}")

    all_changes = []

    for election in history:
        year = election.get('year')
        if year in oc_data:
            changes, error = enrich_election(election, oc_data[year], city_name, year)
            if error:
                print(f"\n{year}: {error}")
            elif changes:
                print(f"\n{year}:")
                for change in changes:
                    print(change)
                all_changes.extend(changes)
            else:
                print(f"\n{year}: No changes needed")
        else:
            print(f"\n{year}: No OC data available")

    if not all_changes:
        print("\nNo changes to make.")
        return 0

    if args.dry_run:
        print(f"\n[DRY RUN] Would write {len(all_changes)} changes to {yaml_path}")
    else:
        # Write updated YAML (ruamel preserves comments)
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)
        print(f"\nWrote changes to {yaml_path}")

    return 0


if __name__ == '__main__':
    exit(main())
