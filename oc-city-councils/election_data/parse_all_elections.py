#!/usr/bin/env python3
"""
Parse OC Registrar election data files and extract city council results.
Handles multiple file formats from 2016-2024.
"""

import csv
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
                # Handle both "Choice Name1" (2024) and "Choice Name" (2022)
                candidate = row.get('Choice Name1') or row.get('Choice Name', '')
                if candidate and 'write-in' not in candidate.lower():
                    votes = int(row.get('Total Votes', 0) or 0)
                    results[contest][candidate] += votes

    return results

def parse_2020(filepath):
    """Parse 2020 format (CSV with header on line 2)."""
    results = defaultdict(lambda: defaultdict(int))

    with open(filepath, 'r', encoding='latin-1') as f:
        # Skip the format version line
        next(f)
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
                    # Sum all vote types
                    absentee = int(row.get('Absentee_votes', 0) or 0)
                    early = int(row.get('Early_votes', 0) or 0)
                    election = int(row.get('Election_Votes', 0) or 0)
                    votes = absentee + early + election
                    results[contest][candidate] += votes

    return results

def print_results(results, year):
    """Print results in a formatted way."""
    print(f'\n{"="*70}')
    print(f'{year} CITY COUNCIL RACES - ALL CANDIDATES')
    print(f'{"="*70}')

    for contest in sorted(results.keys()):
        print(f'\n{contest}')
        candidates = sorted(results[contest].items(), key=lambda x: -x[1])
        for i, (candidate, votes) in enumerate(candidates):
            marker = '[W]' if i == 0 else '[L]'
            print(f'  {marker} {candidate}: {votes:,} votes')

def main():
    base_path = Path(__file__).parent

    # Parse each year
    all_results = {}

    # 2024
    f2024 = base_path / 'results-final.txt'
    if f2024.exists():
        all_results[2024] = parse_2024_2022(f2024, 2024)
        print_results(all_results[2024], 2024)

    # 2022
    f2022 = base_path / 'results.txt'
    if f2022.exists():
        all_results[2022] = parse_2024_2022(f2022, 2022)
        print_results(all_results[2022], 2022)

    # 2020
    f2020 = base_path / 'Detailed vote totals.CSV'
    if f2020.exists():
        all_results[2020] = parse_2020(f2020)
        print_results(all_results[2020], 2020)

    # 2018
    f2018 = base_path / '2018_data' / 'contest_table.txt'
    if f2018.exists():
        all_results[2018] = parse_2018_2016(f2018)
        print_results(all_results[2018], 2018)

    # 2016
    f2016 = base_path / '2016_data' / 'contest_table.txt'
    if f2016.exists():
        all_results[2016] = parse_2018_2016(f2016)
        print_results(all_results[2016], 2016)

    # Summary
    print(f'\n{"="*70}')
    print('SUMMARY')
    print(f'{"="*70}')
    for year in sorted(all_results.keys(), reverse=True):
        races = len(all_results[year])
        candidates = sum(len(c) for c in all_results[year].values())
        print(f'{year}: {races} races, {candidates} candidates')

if __name__ == '__main__':
    main()
