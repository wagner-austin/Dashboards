# Orange County City Councils

Contact information, meeting details, elections, and term limits for all 34 Orange County city councils.

**Live Dashboard:** [https://wagner-austin.github.io/Dashboards/oc-city-councils/](https://wagner-austin.github.io/Dashboards/oc-city-councils/)

## Data

The YAML files in `_council_data/` are the **golden source of truth**. They have been manually verified against official city websites.

### What's Included (per city)

- **Council members** - names, positions, districts, terms, exact dates
- **Contact info** - emails, phone numbers, city profile pages
- **Meeting schedule** - day, time, location
- **Public comment info** - email, deadline, time limits, remote options
- **City clerk** - name, phone, email
- **Quick links** - agendas, live stream, video archives
- **Elections** - history, candidates, vote counts, cycle patterns
- **Term limits** - limits, cooldowns, effective dates, sources

## Usage

### View the Dashboard

Open `index.html` in a browser, or visit the live site above.

### Edit City Data

1. Edit the YAML file in `_council_data/` (e.g., `anaheim.yaml`)
2. Run `python build_dashboard.py` to rebuild the JSON
3. Commit and push

**Or just push the YAML changes** - GitHub Actions will auto-rebuild the JSON.

### Validate YAML Files

```bash
python validate_schema.py
```

This checks all YAML files against the standard schema and reports errors/warnings.

### Rebuild Database

```bash
python db/init_db.py
```

This imports all YAML data into SQLite for querying.

### Populate Election History

```bash
python election_data/populate_history.py --dry-run  # Preview
python election_data/populate_history.py            # Apply
```

Creates election history entries (winners, vote counts, all candidates) from OC Registrar data for years 2012-2024. See `election_data/README.md` for data sources and details.

### Enrich Existing Election Data

```bash
python election_data/enrich_yaml.py --all --dry-run
```

Adds vote counts and candidate lists to existing history entries.

### Check Schema Drift

```bash
python check_schema_drift.py
```

Compares all cities against the reference schema (Aliso Viejo) to find missing fields or structural differences.

### Check Data Coverage

```bash
python validate_schema.py --coverage
```

Shows a table of what data each city has (history years, vote counts, term limits, etc.).

## Project Structure

```
oc-city-councils/
├── index.html              # Dashboard (reads dashboard_data.json)
├── dashboard_data.json     # Auto-generated from YAML files
├── build_dashboard.py      # YAML → JSON builder
├── validate_schema.py      # YAML schema validator (use --coverage for report)
├── check_schema_drift.py   # Compare cities against reference schema
├── add_missing_fields.py   # Add missing schema fields to all cities
├── _council_data/          # ✅ YAML files (golden source of truth)
│   ├── aliso-viejo.yaml    # Reference schema
│   ├── anaheim.yaml
│   └── ... (34 cities)
├── db/                     # Database scripts
│   ├── init_db.py          # YAML → SQLite importer
│   └── schema.sql          # Database schema with views
└── election_data/          # Election data & scripts
    ├── README.md           # Data sources & how to use
    ├── populate_history.py # Create history from OC Registrar data
    ├── enrich_yaml.py      # Add vote counts to existing history
    ├── validate_against_yaml.py  # Verify data accuracy
    └── *.txt, *.CSV        # Raw OC Registrar data (gitignored)
```

## YAML Format

See `docs/YAML_TEMPLATE.md` for the complete field reference. Key sections:

```yaml
city: anaheim
city_name: Anaheim
website: https://www.anaheim.net
council_url: https://www.anaheim.net/173/City-Council
last_updated: '2026-01-27'

members:
- name: Ashleigh E. Aitken
  position: Mayor
  district: Citywide
  email: aaitken@anaheim.net
  term_start: 2022
  term_end: 2026
  term_start_date: '2022-12-06'  # Exact date for term limit calc
  term_end_date: '2026-12-08'

elections:
  next_election: '2026-11-03'
  election_system: by-district
  term_length: 4
  term_limit: 2
  term_limit_type: terms           # 'terms' or 'years'
  term_limit_effective: '2022-11-08'
  term_limit_cooldown: 2
  term_limit_cooldown_unit: cycles # 'cycles' or 'years'
  term_limit_source: https://...   # Municipal code URL
```

## Database

The SQLite database (`db/oc_councils.db`) provides queryable access to all data with pre-built views:

- `v_current_council` - Current council members for all cities
- `v_term_limit_status` - Term limit tracking with grandfathering
- `v_term_limit_cities` - Cities with term limits
- `v_election_history` - Past election results

## GitHub Actions

When you push changes to any YAML file in `_council_data/`, the `build-oc-councils.yml` workflow automatically:

1. Runs `build_dashboard.py`
2. Commits the updated `dashboard_data.json`
3. Pushes to the repo

No manual rebuild needed.

## Important Notes

✅ **YAML is the source of truth** - edit YAML files directly, not JSON.

✅ **Dashboard auto-rebuilds** - just push YAML changes.

✅ **Term limits use exact dates** - `term_start_date` field determines if a member is grandfathered.

## License

Public domain. Data is from public government sources.
