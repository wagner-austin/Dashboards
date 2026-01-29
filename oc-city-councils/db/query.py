#!/usr/bin/env python3
"""
Simple query interface for the councils database.

Usage:
    python db/query.py cities                    # List all cities
    python db/query.py city aliso-viejo          # Show city details
    python db/query.py council aliso-viejo       # Show current council
    python db/query.py elections aliso-viejo     # Show election history
    python db/query.py term-limits               # Cities with term limits
    python db/query.py missing                   # Cities missing data
    python db/query.py sql "SELECT * FROM ..."   # Raw SQL query
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / 'councils.db'


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def list_cities():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT slug, name, council_size, election_system, term_limit
        FROM cities ORDER BY name
    ''')
    print(f"{'Slug':<25} {'Name':<25} {'Size':<6} {'System':<12} {'Term Limit':<10}")
    print("-" * 80)
    for row in cursor.fetchall():
        term_limit = str(row['term_limit']) if row['term_limit'] else '-'
        system = row['election_system'] or '-'
        print(f"{row['slug']:<25} {row['name']:<25} {row['council_size'] or '-':<6} {system:<12} {term_limit:<10}")


def show_city(slug):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cities WHERE slug = ?', (slug,))
    row = cursor.fetchone()
    if not row:
        print(f"City not found: {slug}")
        return

    print(f"\n{'='*60}")
    print(f"  {row['name']}")
    print(f"{'='*60}")
    print(f"  Website: {row['website']}")
    print(f"  Council URL: {row['council_url']}")
    print(f"  Council Size: {row['council_size']} ({row['districts']} districts, {row['at_large']} at-large)")
    print(f"  Election System: {row['election_system']}")
    print(f"  Term Length: {row['term_length']} years")
    if row['term_limit']:
        print(f"  Term Limit: {row['term_limit']} terms, {row['term_limit_cooldown']} cycle cooldown")
        print(f"  Term Limit Source: {row['term_limit_source']}")
    print(f"  Document Center: {row['document_center']}")
    print(f"  Municipal Code: {row['municipal_code']}")


def show_council(slug):
    conn = get_conn()
    cursor = conn.cursor()

    # Get city
    cursor.execute('SELECT id, name FROM cities WHERE slug = ?', (slug,))
    city = cursor.fetchone()
    if not city:
        print(f"City not found: {slug}")
        return

    print(f"\n{city['name']} - Current Council")
    print("-" * 60)

    cursor.execute('''
        SELECT m.name, t.position, t.district, t.start_year, t.end_year
        FROM terms t
        JOIN members m ON t.member_id = m.id
        WHERE t.city_id = ? AND t.end_year >= strftime('%Y', 'now')
        ORDER BY
            CASE t.position
                WHEN 'Mayor' THEN 1
                WHEN 'Vice Mayor' THEN 2
                WHEN 'Mayor Pro Tem' THEN 2
                ELSE 3
            END,
            t.district
    ''', (city['id'],))

    print(f"{'Name':<25} {'Position':<15} {'District':<12} {'Term':<10}")
    print("-" * 60)
    for row in cursor.fetchall():
        district = row['district'] or 'At-Large'
        term = f"{row['start_year']}-{row['end_year']}"
        print(f"{row['name']:<25} {row['position']:<15} {district:<12} {term:<10}")


def show_elections(slug):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('SELECT id, name FROM cities WHERE slug = ?', (slug,))
    city = cursor.fetchone()
    if not city:
        print(f"City not found: {slug}")
        return

    print(f"\n{city['name']} - Election History")
    print("-" * 60)

    cursor.execute('''
        SELECT e.date, e.type, e.resolution_number, e.source_url
        FROM elections e
        WHERE e.city_id = ?
        ORDER BY e.date DESC
    ''', (city['id'],))

    elections = cursor.fetchall()
    for election in elections:
        year = election['date'][:4]
        print(f"\n{year} ({election['type'] or 'general'})")
        if election['resolution_number']:
            print(f"  Resolution: {election['resolution_number']}")

        # Get winners
        cursor.execute('''
            SELECT es.district, m.name, er.votes, er.notes
            FROM election_results er
            JOIN election_seats es ON er.seat_id = es.id
            JOIN members m ON er.member_id = m.id
            JOIN elections e ON er.election_id = e.id
            WHERE e.date = ? AND e.city_id = ?
        ''', (election['date'], city['id']))

        for result in cursor.fetchall():
            votes = f" ({result['votes']} votes)" if result['votes'] else ""
            notes = f" - {result['notes']}" if result['notes'] else ""
            print(f"  {result['district']}: {result['name']}{votes}{notes}")


def show_term_limits():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, term_limit, term_limit_cooldown, term_limit_effective, term_limit_source
        FROM cities
        WHERE term_limit IS NOT NULL
        ORDER BY name
    ''')

    print(f"\nCities with Term Limits")
    print("-" * 80)
    print(f"{'City':<25} {'Limit':<8} {'Cooldown':<10} {'Effective':<12} {'Source':<30}")
    print("-" * 80)

    for row in cursor.fetchall():
        cooldown = f"{row['term_limit_cooldown']} cycles" if row['term_limit_cooldown'] else '-'
        effective = row['term_limit_effective'] or '-'
        source = (row['term_limit_source'] or '-')[:30]
        print(f"{row['name']:<25} {row['term_limit']:<8} {cooldown:<10} {effective:<12} {source:<30}")


def show_missing():
    conn = get_conn()
    cursor = conn.cursor()

    print("\nCities missing document_center:")
    cursor.execute("SELECT name FROM cities WHERE document_center IS NULL ORDER BY name")
    for row in cursor.fetchall():
        print(f"  - {row['name']}")

    print("\nCities missing municipal_code:")
    cursor.execute("SELECT name FROM cities WHERE municipal_code IS NULL ORDER BY name")
    for row in cursor.fetchall():
        print(f"  - {row['name']}")

    print("\nCities missing term_limit info (may not have limits):")
    cursor.execute("SELECT name FROM cities WHERE term_limit IS NULL ORDER BY name")
    for row in cursor.fetchall():
        print(f"  - {row['name']}")


def run_sql(query):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        if rows:
            # Print header
            print(" | ".join(rows[0].keys()))
            print("-" * 60)
            for row in rows:
                print(" | ".join(str(v) for v in row))
        else:
            print("No results")
    except Exception as e:
        print(f"Error: {e}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == 'cities':
        list_cities()
    elif cmd == 'city' and len(sys.argv) > 2:
        show_city(sys.argv[2])
    elif cmd == 'council' and len(sys.argv) > 2:
        show_council(sys.argv[2])
    elif cmd == 'elections' and len(sys.argv) > 2:
        show_elections(sys.argv[2])
    elif cmd == 'term-limits':
        show_term_limits()
    elif cmd == 'missing':
        show_missing()
    elif cmd == 'sql' and len(sys.argv) > 2:
        run_sql(sys.argv[2])
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
