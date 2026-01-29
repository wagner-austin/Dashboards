#!/usr/bin/env python3
"""
Rebuild the SQLite database from YAML files.

Usage:
    python db/init_db.py                # Rebuild database and import all YAML
    python db/init_db.py --schema-only  # Create empty database (no import)
"""

import sqlite3
import yaml
import sys
import json
from datetime import date, timedelta
from pathlib import Path

# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# File paths
DB_PATH = Path(__file__).parent / 'councils.db'
SCHEMA_PATH = Path(__file__).parent / 'schema.sql'
YAML_DIR = Path(__file__).parent.parent / '_council_data'

# California election timing
ELECTION_MONTH = 11  # November
DAYS_IN_WEEK = 7
MONDAY = 0  # weekday() returns 0 for Monday
TUESDAY_OFFSET = 1  # Tuesday is 1 day after Monday

# Default term assumptions (can be overridden in YAML)
DEFAULT_TERM_LENGTH_YEARS = 4
DEFAULT_SWEARING_IN_MONTH = 12  # December
DEFAULT_SWEARING_IN_DAY = 1

# Date format detection
YEAR_ONLY_LENGTH = 4  # "2024" is 4 chars, "2024-11-05" is longer


def election_day(year: int) -> str:
    """Calculate election day: first Tuesday after first Monday in November."""
    nov1 = date(year, ELECTION_MONTH, 1)
    # Find first Monday
    days_until_monday = (DAYS_IN_WEEK - nov1.weekday()) % DAYS_IN_WEEK
    if nov1.weekday() == MONDAY:
        first_monday = nov1
    else:
        first_monday = nov1 + timedelta(days=days_until_monday)
    # Tuesday after first Monday
    election = first_monday + timedelta(days=TUESDAY_OFFSET)
    return election.isoformat()


def init_database():
    """Create the database with complete schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SCHEMA_PATH, 'r') as f:
        schema = f.read()

    cursor.executescript(schema)
    conn.commit()
    print(f"Database created at {DB_PATH}")
    return conn


def import_city(conn, filepath: Path):
    """Import a single city YAML file into the database with ALL fields."""
    cursor = conn.cursor()

    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not data:
        return

    # Extract nested sections
    elections = data.get('elections', {})
    meetings = data.get('meetings', {})
    clerk = data.get('clerk', {})
    portals = data.get('portals', {})
    council = data.get('council', {})
    broadcast = data.get('broadcast', {})
    public_comment = data.get('public_comment', {})
    location = meetings.get('location', {})
    candidate_info = elections.get('candidate_info', {})

    # Insert city with ALL fields
    cursor.execute('''
        INSERT OR REPLACE INTO cities (
            slug, name, website, council_url,
            -- Meeting info
            meeting_schedule, meeting_time, meeting_location_name,
            meeting_address, meeting_city_state_zip,
            -- Remote meeting access
            zoom_url, zoom_id, zoom_passcode, zoom_phone_numbers, webex_url,
            -- Clerk info
            clerk_name, clerk_title, clerk_phone, clerk_fax, clerk_email, clerk_address,
            -- Council composition
            council_size, council_districts, council_at_large, mayor_elected, mayor_rotation,
            council_expanded_date, council_transition_date, council_notes,
            -- Portals & URLs
            document_center, municipal_code, agendas_url, live_stream_url, video_archive_url,
            granicus_url, legistar_url, youtube_url, cablecast_url, ecomment_url,
            district_map_url, invite_form_url, public_comment_form_url,
            -- Broadcast
            broadcast_live_stream,
            -- Public comment rules
            public_comment_in_person, public_comment_remote_live, public_comment_ecomment,
            public_comment_written_email, public_comment_written_form,
            public_comment_time_limit, public_comment_total_time_limit,
            public_comment_deadline, public_comment_email,
            public_comment_instructions_url, public_comment_notes,
            -- Term limits
            term_limit, term_limit_type, term_limit_cooldown, term_limit_cooldown_unit,
            term_limit_effective, term_limit_notes, term_limit_source, term_length,
            -- Elections
            election_system, next_election, nomination_period, transition_note,
            results_source, past_results_url, districting_info_url, fppc_filings_url,
            candidate_resources_url, contribution_limit,
            -- Candidate filing info
            candidate_contact_email, candidate_contact_phone, candidate_filing_location,
            -- Meta
            last_updated, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('city'),                           # slug
        data.get('city_name'),                      # name
        data.get('website'),                        # website
        data.get('council_url'),                    # council_url
        # Meeting info
        meetings.get('schedule'),                   # meeting_schedule
        meetings.get('time'),                       # meeting_time
        location.get('name'),                       # meeting_location_name
        location.get('address'),                    # meeting_address
        location.get('city_state_zip'),             # meeting_city_state_zip
        # Remote meeting access
        meetings.get('zoom_url'),                   # zoom_url
        meetings.get('zoom_id'),                    # zoom_id
        meetings.get('zoom_passcode'),              # zoom_passcode
        json.dumps(meetings.get('zoom_phone_numbers')) if meetings.get('zoom_phone_numbers') else None,
        meetings.get('webex_url'),                  # webex_url
        # Clerk info
        clerk.get('name'),                          # clerk_name
        clerk.get('title'),                         # clerk_title
        clerk.get('phone'),                         # clerk_phone
        clerk.get('fax'),                           # clerk_fax
        clerk.get('email'),                         # clerk_email
        clerk.get('address'),                       # clerk_address
        # Council composition
        council.get('size'),                        # council_size
        council.get('districts'),                   # council_districts
        council.get('at_large'),                    # council_at_large
        council.get('mayor_elected'),               # mayor_elected
        council.get('mayor_rotation'),              # mayor_rotation
        council.get('expanded_date'),               # council_expanded_date
        council.get('transition_date'),             # council_transition_date
        council.get('notes'),                       # council_notes
        # Portals & URLs
        portals.get('document_center'),             # document_center
        portals.get('municipal_code'),              # municipal_code
        portals.get('agendas'),                     # agendas_url
        portals.get('live_stream'),                 # live_stream_url
        portals.get('video_archive'),               # video_archive_url
        portals.get('granicus'),                    # granicus_url
        portals.get('legistar'),                    # legistar_url
        portals.get('youtube'),                     # youtube_url
        portals.get('cablecast'),                   # cablecast_url
        portals.get('ecomment'),                    # ecomment_url
        portals.get('district_map'),                # district_map_url
        portals.get('invite_form'),                 # invite_form_url
        portals.get('public_comment_form'),         # public_comment_form_url
        # Broadcast
        broadcast.get('live_stream'),               # broadcast_live_stream
        # Public comment rules
        public_comment.get('in_person'),            # public_comment_in_person
        public_comment.get('remote_live'),          # public_comment_remote_live
        public_comment.get('ecomment'),             # public_comment_ecomment
        public_comment.get('written_email'),        # public_comment_written_email
        public_comment.get('written_form'),         # public_comment_written_form
        public_comment.get('time_limit'),           # public_comment_time_limit
        public_comment.get('total_time_limit'),     # public_comment_total_time_limit
        public_comment.get('deadline'),             # public_comment_deadline
        public_comment.get('email'),                # public_comment_email
        public_comment.get('instructions_url'),     # public_comment_instructions_url
        public_comment.get('notes'),                # public_comment_notes
        # Term limits
        elections.get('term_limit'),                # term_limit
        elections.get('term_limit_type', 'terms'),  # term_limit_type
        elections.get('term_limit_cooldown'),       # term_limit_cooldown
        elections.get('term_limit_cooldown_unit', 'cycles'),  # term_limit_cooldown_unit
        elections.get('term_limit_effective'),      # term_limit_effective
        elections.get('term_limit_notes'),          # term_limit_notes
        elections.get('term_limit_source'),         # term_limit_source
        elections.get('term_length', 4),            # term_length
        # Elections
        elections.get('election_system'),           # election_system
        elections.get('next_election'),             # next_election
        elections.get('nomination_period'),         # nomination_period
        elections.get('transition_note'),           # transition_note
        elections.get('results_source'),            # results_source
        elections.get('past_results_url'),          # past_results_url
        elections.get('districting_info'),          # districting_info_url
        elections.get('fppc_filings'),              # fppc_filings_url
        elections.get('candidate_resources'),       # candidate_resources_url
        elections.get('contribution_limit'),        # contribution_limit
        # Candidate filing info
        candidate_info.get('contact_email'),        # candidate_contact_email
        candidate_info.get('contact_phone'),        # candidate_contact_phone
        candidate_info.get('location'),             # candidate_filing_location
        # Meta
        data.get('last_updated'),                   # last_updated
        data.get('notes'),                          # notes
    ))

    city_id = cursor.lastrowid or cursor.execute(
        'SELECT id FROM cities WHERE slug = ?', (data.get('city'),)
    ).fetchone()[0]

    # Insert cable channels
    for channel in broadcast.get('cable_channels', []):
        if channel:
            cursor.execute('''
                INSERT INTO cable_channels (city_id, provider, channel)
                VALUES (?, ?, ?)
            ''', (city_id, channel.get('provider', ''), channel.get('channel', '')))

    # Insert people (members) with ALL fields
    for member_data in data.get('members', []):
        # Check if person already exists
        cursor.execute('SELECT id FROM people WHERE name = ?', (member_data.get('name'),))
        row = cursor.fetchone()

        if row:
            person_id = row[0]
            # Update person info with all fields
            cursor.execute('''
                UPDATE people SET
                    email=?, phone=?, bio=?, photo_url=?,
                    city_page=?, website=?, facebook=?, twitter=?, instagram=?, linkedin=?
                WHERE id=?
            ''', (
                member_data.get('email'),
                member_data.get('phone'),
                member_data.get('bio'),
                member_data.get('photo_url'),
                member_data.get('city_page'),
                member_data.get('website'),
                member_data.get('facebook'),
                member_data.get('twitter'),
                member_data.get('instagram'),
                member_data.get('linkedin'),
                person_id,
            ))
        else:
            cursor.execute('''
                INSERT INTO people (name, email, phone, bio, photo_url, city_page, website, facebook, twitter, instagram, linkedin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                member_data.get('name'),
                member_data.get('email'),
                member_data.get('phone'),
                member_data.get('bio'),
                member_data.get('photo_url'),
                member_data.get('city_page'),
                member_data.get('website'),
                member_data.get('facebook'),
                member_data.get('twitter'),
                member_data.get('instagram'),
                member_data.get('linkedin'),
            ))
            person_id = cursor.lastrowid

        # Determine start_type from bio/notes or default to 'elected'
        bio = member_data.get('bio', '') or ''
        start_type = 'elected'  # Default
        if 'appointed' in bio.lower():
            start_type = 'appointed'

        # Get exact dates if available, otherwise derive from years
        # Typical swearing-in is first December meeting after November election
        start_year = member_data.get('term_start')
        end_year = member_data.get('term_end')
        start_date = member_data.get('term_start_date')
        end_date = member_data.get('term_end_date')

        # Default to December 1 of start year if no exact date
        if not start_date and start_year:
            start_date = f"{start_year}-{DEFAULT_SWEARING_IN_MONTH:02d}-{DEFAULT_SWEARING_IN_DAY:02d}"
        # Default to December 1 of end year (when successor takes over)
        if not end_date and end_year:
            end_date = f"{end_year}-{DEFAULT_SWEARING_IN_MONTH:02d}-{DEFAULT_SWEARING_IN_DAY:02d}"

        # Insert current term with all fields including dates
        cursor.execute('''
            INSERT INTO terms (person_id, city_id, district, position, start_year, end_year, start_date, end_date, start_type, end_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            person_id,
            city_id,
            member_data.get('district'),
            member_data.get('position'),
            start_year,
            end_year,
            start_date,
            end_date,
            start_type,
            'ongoing',  # Current members have ongoing terms
        ))

    # Insert election history with full details
    for election in elections.get('history', []):
        year = election.get('year')
        # Use exact date if provided, otherwise calculate correct election day
        election_date = election.get('date')
        if not election_date or len(str(election_date)) == YEAR_ONLY_LENGTH:
            election_date = election_day(year)

        cursor.execute('''
            INSERT INTO elections (city_id, date, year, type, election_system, nomination_period, resolution_number, certified_date, source_url, results_url, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            city_id,
            election_date,
            year,
            election.get('type', 'general'),
            election.get('type'),  # by-district, at-large, etc.
            election.get('nomination_period'),
            election.get('resolution'),
            election.get('certified'),
            election.get('source'),
            election.get('results_url'),
            election.get('notes'),
        ))
        election_id = cursor.lastrowid

        # Get default term length from city, fallback to standard 4-year term
        default_term_length = elections.get('term_length', DEFAULT_TERM_LENGTH_YEARS)
        mayor_term_length = elections.get('mayor_term_length', default_term_length)

        # Insert seats and winners
        for winner in election.get('winners', []):
            district = winner.get('district') or winner.get('seat')

            # Determine term length: winner-specific > mayor-specific > city default
            if winner.get('term_length'):
                term_years = winner.get('term_length')
            elif district and 'Mayor' in district:
                term_years = mayor_term_length
            else:
                term_years = default_term_length

            # Find or create election seat (avoid duplicates for At-Large races)
            cursor.execute('''
                SELECT id FROM election_seats WHERE election_id = ? AND district = ?
            ''', (election_id, district))
            row = cursor.fetchone()
            if row:
                seat_id = row[0]
            else:
                cursor.execute('''
                    INSERT INTO election_seats (election_id, district, seat_type, term_years)
                    VALUES (?, ?, ?, ?)
                ''', (election_id, district, 'full_term', term_years))
                seat_id = cursor.lastrowid

            # Find or create person for winner
            winner_name = winner.get('winner')
            if winner_name:
                cursor.execute('SELECT id FROM people WHERE name = ?', (winner_name,))
                row = cursor.fetchone()
                if row:
                    winner_person_id = row[0]
                else:
                    cursor.execute('INSERT INTO people (name) VALUES (?)', (winner_name,))
                    winner_person_id = cursor.lastrowid

                # Insert candidate record (winner)
                cursor.execute('''
                    INSERT INTO candidates (election_id, seat_id, person_id, votes, vote_percentage, outcome, notes, source_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    election_id,
                    seat_id,
                    winner_person_id,
                    winner.get('votes'),
                    winner.get('percentage'),
                    'won',
                    winner.get('notes'),
                    winner.get('source'),
                ))

            # Insert runner-up if present (Anaheim format)
            runner_up_name = winner.get('runner_up')
            if runner_up_name:
                cursor.execute('SELECT id FROM people WHERE name = ?', (runner_up_name,))
                row = cursor.fetchone()
                if row:
                    runner_up_id = row[0]
                else:
                    cursor.execute('INSERT INTO people (name) VALUES (?)', (runner_up_name,))
                    runner_up_id = cursor.lastrowid

                cursor.execute('''
                    INSERT INTO candidates (election_id, seat_id, person_id, votes, outcome)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    election_id,
                    seat_id,
                    runner_up_id,
                    winner.get('runner_up_votes'),
                    'lost',
                ))

        # Insert full candidate lists if present
        # Supports two formats:
        # 1. Old format: candidates: ["Name1", "Name2"] with winner field
        # 2. New format: candidates: [{name: "Name1", votes: 123, outcome: "won"}, ...]
        for race in election.get('candidates', []):
            if isinstance(race, dict):
                district = race.get('district')
                candidate_list = race.get('candidates', [])
                race_winner = race.get('winner')  # Only used in old format

                # Determine term length for this district
                if district and 'Mayor' in district:
                    term_years = mayor_term_length
                else:
                    term_years = default_term_length

                # Find or create the seat for this race
                cursor.execute('''
                    SELECT id FROM election_seats WHERE election_id = ? AND district = ?
                ''', (election_id, district))
                row = cursor.fetchone()
                if row:
                    seat_id = row[0]
                else:
                    cursor.execute('''
                        INSERT INTO election_seats (election_id, district, seat_type, term_years)
                        VALUES (?, ?, ?, ?)
                    ''', (election_id, district, 'full_term', term_years))
                    seat_id = cursor.lastrowid

                # Insert each candidate
                for cand in candidate_list:
                    # Handle both old format (string) and new format (dict)
                    if isinstance(cand, dict):
                        cand_name = cand.get('name')
                        cand_votes = cand.get('votes')
                        cand_outcome = cand.get('outcome', 'lost')
                    else:
                        cand_name = cand
                        cand_votes = None
                        cand_outcome = 'won' if cand_name == race_winner else 'lost'

                    if not cand_name:
                        continue

                    cursor.execute('SELECT id FROM people WHERE name = ?', (cand_name,))
                    row = cursor.fetchone()
                    if row:
                        cand_id = row[0]
                    else:
                        cursor.execute('INSERT INTO people (name) VALUES (?)', (cand_name,))
                        cand_id = cursor.lastrowid

                    # Check if candidate already exists for this election/seat (from winners section)
                    cursor.execute('''
                        SELECT id FROM candidates WHERE election_id = ? AND seat_id = ? AND person_id = ?
                    ''', (election_id, seat_id, cand_id))
                    existing = cursor.fetchone()

                    if existing:
                        # Update existing record with votes if we have them
                        if cand_votes:
                            cursor.execute('''
                                UPDATE candidates SET votes = ? WHERE id = ?
                            ''', (cand_votes, existing[0]))
                    else:
                        # Insert new candidate record
                        cursor.execute('''
                            INSERT INTO candidates (election_id, seat_id, person_id, votes, outcome)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (election_id, seat_id, cand_id, cand_votes, cand_outcome))

    # Insert election cycles
    cycle_pattern = elections.get('cycle_pattern', {})
    for group_name, group_data in cycle_pattern.items():
        if group_name.startswith('group_'):
            years = group_data.get('years', '')
            for seat in group_data.get('seats', []):
                cursor.execute('''
                    INSERT INTO election_cycles (city_id, group_name, district, cycle_years)
                    VALUES (?, ?, ?, ?)
                ''', (city_id, group_name, seat, years))

    # Insert upcoming seats (handle both dict and string formats)
    for seat in elections.get('seats_up', []):
        if isinstance(seat, dict):
            # New format: {district: "District 2", incumbent: "Max Duncan"}
            incumbent_id = None
            incumbent_name = seat.get('incumbent')
            if incumbent_name:
                cursor.execute('SELECT id FROM people WHERE name = ?', (incumbent_name,))
                row = cursor.fetchone()
                if row:
                    incumbent_id = row[0]

            cursor.execute('''
                INSERT INTO upcoming_seats (city_id, election_date, district, incumbent_id, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                city_id,
                elections.get('next_election'),
                seat.get('district'),
                incumbent_id,
                seat.get('notes'),
            ))
        else:
            # Old format: just a string like "District 1" or "At-Large"
            cursor.execute('''
                INSERT INTO upcoming_seats (city_id, election_date, district, notes)
                VALUES (?, ?, ?, ?)
            ''', (
                city_id,
                elections.get('next_election'),
                str(seat),
                None,
            ))

    # Insert sources
    if elections.get('source'):
        cursor.execute('''
            INSERT INTO sources (city_id, url, document_type, notes)
            VALUES (?, ?, 'webpage', 'Elections page')
        ''', (city_id, elections.get('source')))

    if elections.get('term_limit_source'):
        cursor.execute('''
            INSERT INTO sources (city_id, url, document_type, notes)
            VALUES (?, ?, 'ordinance', 'Term limits ordinance')
        ''', (city_id, elections.get('term_limit_source')))

    conn.commit()
    print(f"  Imported: {data.get('city_name')}")


def import_all_yaml(conn):
    """Import all YAML files."""
    print(f"\nImporting from {YAML_DIR}")

    yaml_files = sorted(YAML_DIR.glob('*.yaml'))
    for filepath in yaml_files:
        try:
            import_city(conn, filepath)
        except Exception as e:
            print(f"  Error importing {filepath.name}: {e}")
            import traceback
            traceback.print_exc()


def print_summary(conn):
    """Print database summary statistics."""
    cursor = conn.cursor()

    tables = [
        ('cities', 'Cities'),
        ('people', 'People'),
        ('terms', 'Terms'),
        ('elections', 'Elections'),
        ('candidates', 'Candidates'),
        ('election_seats', 'Election Seats'),
        ('election_cycles', 'Election Cycles'),
        ('upcoming_seats', 'Upcoming Seats'),
        ('cable_channels', 'Cable Channels'),
        ('sources', 'Sources'),
    ]

    print(f"\nDatabase summary:")
    for table, label in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"  {label}: {count}")
        except:
            pass


def main():
    """
    Default: recreate database and import all YAML data.
    Use --schema-only to create empty database without importing.
    """
    schema_only = '--schema-only' in sys.argv

    # Always remove existing database when rebuilding
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing database")

    conn = init_database()

    if schema_only:
        print("\n[--schema-only] Created empty database, no data imported.")
    else:
        import_all_yaml(conn)

    print_summary(conn)
    conn.close()


if __name__ == '__main__':
    main()
