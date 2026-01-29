#!/usr/bin/env python3
"""
Validate city council YAML files against the standard schema.
Run: python validate_schema.py
"""

import yaml
import sys
import re
from pathlib import Path

# Date format regex (YYYY-MM-DD)
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')

# Required top-level fields
REQUIRED_FIELDS = [
    'city',
    'city_name',
    'website',
    'council_url',
    'last_updated',
    'members',
]

# Required fields in elections section
REQUIRED_ELECTIONS_FIELDS = [
    'next_election',
    'election_system',
    'term_length',
    'seats_up',
]

# Term limit fields - all should be present (even if null) for consistency
TERM_LIMIT_FIELDS = [
    'term_limit',
    'term_limit_type',
    'term_limit_cooldown',
    'term_limit_cooldown_unit',
    'term_limit_effective',
    'term_limit_notes',
    'term_limit_source',
]

# Valid values for term limit fields
VALID_TERM_LIMIT_TYPES = ['terms', 'years', None]
VALID_TERM_LIMIT_COOLDOWN_UNITS = ['cycles', 'years', None]

# Required fields for each member
REQUIRED_MEMBER_FIELDS = [
    'name',
    'position',
    'email',
    'term_start',
    'term_end',
]

# Recommended fields (warn if missing)
RECOMMENDED_FIELDS = {
    'portals': ['document_center', 'municipal_code'],
    'clerk': ['phone', 'email'],
    'meetings': ['schedule', 'time'],
}

# Valid field names in portals section (anything else triggers a warning)
VALID_PORTAL_FIELDS = [
    'agendas',
    'document_center',
    'municipal_code',
    'live_stream',
    'video_archive',
    'youtube',
    'granicus',
    'legistar',
    'ecomment',
    'public_comment_form',
    'district_map',
    'invite_form',
    'cablecast',
]

# Non-standard field names that should be replaced
DEPRECATED_FIELDS = {
    'portals': {
        'laserfiche': 'document_center',
        'hyland': 'document_center',
        'weblink': 'document_center',
        'agenda_center': 'agendas',
    },
    'elections': {
        'term_limits': 'term_limit',
    },
    'council': {
        'mayor_term': 'Use elections.mayor_term_length instead',
        'councilmember_term': 'Use elections.term_length instead',
    }
}

# Valid election_system values
VALID_ELECTION_SYSTEMS = ['by-district', 'by-ward', 'at-large', 'mixed']

# Valid position values
VALID_POSITIONS = ['Mayor', 'Vice Mayor', 'Mayor Pro Tem', 'Councilmember', 'Council Member']


def is_valid_date(value):
    """Check if value is a valid YYYY-MM-DD date string."""
    if value is None:
        return True  # null is allowed
    if not isinstance(value, str):
        return False
    return bool(DATE_PATTERN.match(value))


class ValidationResult:
    def __init__(self, city_file):
        self.city_file = city_file
        self.errors = []
        self.warnings = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def has_issues(self):
        return len(self.errors) > 0 or len(self.warnings) > 0

    def print_results(self):
        if not self.has_issues():
            return

        print(f"\n{'='*60}")
        print(f"  {self.city_file}")
        print(f"{'='*60}")

        if self.errors:
            print(f"\n  ERRORS ({len(self.errors)}):")
            for e in self.errors:
                print(f"    - {e}")

        if self.warnings:
            print(f"\n  WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"    - {w}")


def validate_file(filepath: Path) -> ValidationResult:
    result = ValidationResult(filepath.name)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        result.error(f"Failed to parse YAML: {e}")
        return result

    if not data:
        result.error("File is empty or invalid")
        return result

    # Check required top-level fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            result.error(f"Missing required field: {field}")

    # Validate last_updated date format
    if 'last_updated' in data and not is_valid_date(data['last_updated']):
        result.error(f"Invalid date format for last_updated: {data['last_updated']} (expected YYYY-MM-DD)")

    # Check elections section
    if 'elections' in data:
        elections = data['elections']
        for field in REQUIRED_ELECTIONS_FIELDS:
            if field not in elections:
                result.error(f"Missing required elections field: {field}")

        # Validate election_system value
        if 'election_system' in elections:
            if elections['election_system'] not in VALID_ELECTION_SYSTEMS:
                result.error(f"Invalid election_system: {elections['election_system']} (valid: {VALID_ELECTION_SYSTEMS})")

        # Validate date formats
        if 'next_election' in elections and not is_valid_date(elections['next_election']):
            result.error(f"Invalid date format for next_election: {elections['next_election']} (expected YYYY-MM-DD)")

        if 'term_limit_effective' in elections and not is_valid_date(elections['term_limit_effective']):
            result.error(f"Invalid date format for term_limit_effective: {elections['term_limit_effective']} (expected YYYY-MM-DD)")

        # Check for deprecated field names
        for old_name, new_name in DEPRECATED_FIELDS.get('elections', {}).items():
            if old_name in elections:
                result.error(f"Deprecated field 'elections.{old_name}' - use '{new_name}' instead")

        # Check term limit fields for consistency
        if elections.get('term_limit') is not None:
            # If city has term limits, check all fields are documented
            for field in TERM_LIMIT_FIELDS:
                if field not in elections:
                    result.warn(f"term_limit is set but '{field}' is missing")

            # Validate term_limit_type value
            tl_type = elections.get('term_limit_type')
            if tl_type not in VALID_TERM_LIMIT_TYPES:
                result.error(f"Invalid term_limit_type: {tl_type} (valid: terms, years, or null)")

            # Validate term_limit_cooldown_unit value
            tl_cooldown_unit = elections.get('term_limit_cooldown_unit')
            if tl_cooldown_unit not in VALID_TERM_LIMIT_COOLDOWN_UNITS:
                result.error(f"Invalid term_limit_cooldown_unit: {tl_cooldown_unit} (valid: cycles, years, or null)")
    else:
        result.error("Missing required section: elections")

    # Check portals section
    if 'portals' in data:
        portals = data['portals']

        # Check for deprecated field names
        for old_name, new_name in DEPRECATED_FIELDS.get('portals', {}).items():
            if old_name in portals:
                result.error(f"Deprecated field 'portals.{old_name}' - use '{new_name}' instead")

        # Check recommended portal fields
        for field in RECOMMENDED_FIELDS.get('portals', []):
            if field not in portals or not portals[field]:
                result.warn(f"Missing recommended portals field: {field}")
    else:
        result.warn("Missing recommended section: portals")

    # Check members
    if 'members' in data:
        members = data['members']
        if not isinstance(members, list):
            result.error("'members' should be a list")
        else:
            for i, member in enumerate(members):
                for field in REQUIRED_MEMBER_FIELDS:
                    if field not in member:
                        result.error(f"Member {i+1} missing required field: {field}")

                # Validate position
                if 'position' in member:
                    pos = member['position']
                    if pos not in VALID_POSITIONS:
                        result.warn(f"Member '{member.get('name', i+1)}' has non-standard position: {pos}")

                # Validate optional date fields
                for date_field in ['term_start_date', 'term_end_date']:
                    if date_field in member and not is_valid_date(member[date_field]):
                        result.error(f"Member '{member.get('name', i+1)}' has invalid {date_field}: {member[date_field]} (expected YYYY-MM-DD)")

    # Check clerk section
    if 'clerk' in data:
        clerk = data['clerk']
        for field in RECOMMENDED_FIELDS.get('clerk', []):
            if field not in clerk or not clerk[field]:
                result.warn(f"Missing recommended clerk field: {field}")
    else:
        result.warn("Missing recommended section: clerk")

    # Check meetings section
    if 'meetings' in data:
        meetings = data['meetings']
        for field in RECOMMENDED_FIELDS.get('meetings', []):
            if field not in meetings or not meetings[field]:
                result.warn(f"Missing recommended meetings field: {field}")
    else:
        result.warn("Missing recommended section: meetings")

    # Check council section for deprecated fields
    if 'council' in data:
        council = data['council']
        elections = data.get('elections', {})

        # Check for deprecated field names
        for old_name, suggestion in DEPRECATED_FIELDS.get('council', {}).items():
            if old_name in council:
                result.error(f"Deprecated field 'council.{old_name}' - {suggestion}")

        # Validate term length consistency
        if 'term_length' in council and 'term_length' in elections:
            if council['term_length'] != elections['term_length']:
                result.error(f"Inconsistent term_length: council={council['term_length']}, elections={elections['term_length']}")

    return result


def check_coverage(data: dict, city_name: str) -> dict:
    """Check data coverage for a city, returning what's present/missing."""
    coverage = {
        'city': city_name,
        'sections': {},
    }

    # Check main sections
    sections = {
        'members': bool(data.get('members')),
        'meetings': bool(data.get('meetings')),
        'portals': bool(data.get('portals')),
        'broadcast': bool(data.get('broadcast')),
        'clerk': bool(data.get('clerk')),
        'public_comment': bool(data.get('public_comment')),
        'council': bool(data.get('council')),
        'elections': bool(data.get('elections')),
    }
    coverage['sections'] = sections

    # Check member details (sample first member)
    members = data.get('members', [])
    if members:
        m = members[0]
        coverage['member_fields'] = {
            'bio': bool(m.get('bio')),
            'photo_url': bool(m.get('photo_url')),
            'city_page': bool(m.get('city_page')),
            'term_start_date': bool(m.get('term_start_date')),
            'term_end_date': bool(m.get('term_end_date')),
        }

    # Check elections details
    elections = data.get('elections', {})
    coverage['elections'] = {
        'history': bool(elections.get('history')),
        'history_years': len(elections.get('history', [])),
        'cycle_pattern': bool(elections.get('cycle_pattern')),
        'term_limit': elections.get('term_limit') is not None,
        'term_limit_source': bool(elections.get('term_limit_source')),
    }

    # Check if history has vote counts
    history = elections.get('history', [])
    has_votes = False
    has_candidates = False
    for h in history:
        winners = h.get('winners', [])
        for w in winners:
            if w.get('votes') is not None:
                has_votes = True
        if h.get('candidates'):
            has_candidates = True
    coverage['elections']['has_vote_counts'] = has_votes
    coverage['elections']['has_candidate_lists'] = has_candidates

    # Check portals
    portals = data.get('portals', {})
    coverage['portals'] = {
        'agendas': bool(portals.get('agendas')),
        'live_stream': bool(portals.get('live_stream')),
        'video_archive': bool(portals.get('video_archive')),
        'document_center': bool(portals.get('document_center')),
        'municipal_code': bool(portals.get('municipal_code')),
        'ecomment': bool(portals.get('ecomment')),
    }

    return coverage


def print_coverage_report(data_dir: Path):
    """Print a coverage report for all cities."""
    yaml_files = sorted(data_dir.glob('*.yaml'))

    print(f"{'City':<25} {'Hist':<5} {'Votes':<6} {'Cands':<6} {'TLimit':<7} {'Docs':<5} {'MCode':<5}")
    print(f"{'-'*25} {'-'*5} {'-'*6} {'-'*6} {'-'*7} {'-'*5} {'-'*5}")

    for filepath in yaml_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        city_name = data.get('city_name', filepath.stem)
        cov = check_coverage(data, city_name)

        hist_years = cov['elections']['history_years']
        has_votes = 'yes' if cov['elections']['has_vote_counts'] else '-'
        has_cands = 'yes' if cov['elections']['has_candidate_lists'] else '-'
        has_tlimit = 'yes' if cov['elections']['term_limit'] else '-'
        has_docs = 'yes' if cov['portals']['document_center'] else '-'
        has_mcode = 'yes' if cov['portals']['municipal_code'] else '-'

        print(f"{city_name:<25} {hist_years:<5} {has_votes:<6} {has_cands:<6} {has_tlimit:<7} {has_docs:<5} {has_mcode:<5}")

    print(f"\nLegend: Hist=election history years, Votes=has vote counts, Cands=has candidate lists")
    print(f"        TLimit=has term limits, Docs=document_center, MCode=municipal_code")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Validate city council YAML files')
    parser.add_argument('--coverage', action='store_true', help='Show data coverage report')
    parser.add_argument('city', nargs='?', help='Validate single city (e.g., anaheim)')
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / '_council_data'

    if not data_dir.exists():
        print(f"Error: Directory not found: {data_dir}")
        sys.exit(1)

    if args.coverage:
        print_coverage_report(data_dir)
        sys.exit(0)

    if args.city:
        yaml_files = [data_dir / f'{args.city}.yaml']
        if not yaml_files[0].exists():
            print(f"Error: File not found: {yaml_files[0]}")
            sys.exit(1)
    else:
        yaml_files = sorted(data_dir.glob('*.yaml'))

    if not yaml_files:
        print(f"No YAML files found in {data_dir}")
        sys.exit(1)

    print(f"Validating {len(yaml_files)} YAML files...")

    total_errors = 0
    total_warnings = 0
    files_with_issues = 0

    results = []
    for filepath in yaml_files:
        result = validate_file(filepath)
        results.append(result)
        total_errors += len(result.errors)
        total_warnings += len(result.warnings)
        if result.has_issues():
            files_with_issues += 1

    # Print results for files with issues
    for result in results:
        result.print_results()

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Files checked:      {len(yaml_files)}")
    print(f"  Files with issues:  {files_with_issues}")
    print(f"  Total errors:       {total_errors}")
    print(f"  Total warnings:     {total_warnings}")

    if total_errors == 0 and total_warnings == 0:
        print(f"\n  All files valid!")

    # Exit with error code if there are errors
    sys.exit(1 if total_errors > 0 else 0)


if __name__ == '__main__':
    main()
