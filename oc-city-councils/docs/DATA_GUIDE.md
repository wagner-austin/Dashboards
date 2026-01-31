# OC City Councils Data Guide

This document provides comprehensive documentation for the Orange County City Councils database, including data sources, field definitions, and procedures for data collection and validation.

## Table of Contents

1. [Overview](#overview)
2. [Data Sources](#data-sources)
3. [YAML Field Reference](#yaml-field-reference)
4. [Database Schema](#database-schema)
5. [OC Registrar Election Data](#oc-registrar-election-data)
6. [Data Collection Procedures](#data-collection-procedures)
7. [Validation and Quality Control](#validation-and-quality-control)
8. [Known Issues and Challenges](#known-issues-and-challenges)
9. [TODO Checklist by City](#todo-checklist-by-city)

---

## Overview

This project tracks city council information for all 34 incorporated cities in Orange County, California. Data includes:

- Current council members and their terms
- Election systems (by-district, at-large, mixed)
- Term limits and cooldown periods
- Historical election results with vote counts
- Meeting schedules and public comment procedures
- Contact information and official URLs

### Cities Covered (34 total)

Aliso Viejo, Anaheim, Brea, Buena Park, Costa Mesa, Cypress, Dana Point, Fountain Valley, Fullerton, Garden Grove, Huntington Beach, Irvine, La Habra, La Palma, Laguna Beach, Laguna Hills, Laguna Niguel, Laguna Woods, Lake Forest, Los Alamitos, Mission Viejo, Newport Beach, Orange, Placentia, Rancho Santa Margarita, San Clemente, San Juan Capistrano, Santa Ana, Seal Beach, Stanton, Tustin, Villa Park, Westminster, Yorba Linda

---

## Data Sources

### Primary Sources

| Source | URL | Data Type | Update Frequency |
|--------|-----|-----------|------------------|
| OC Registrar of Voters | https://ocvote.gov | Official election results, vote counts | After each election |
| City websites | varies | Council members, meeting info, term limits | As needed |
| Municipal codes | varies (amlegal, codepublishing, ecode360) | Term limits, election rules | Rarely changes |

### OC Registrar Statement of Vote (SOV)

The authoritative source for election results. Available at:
- **Archive**: https://ocvote.gov/data/election-results-archives/archived-statement-of-votes
- **Format**: media.zip files containing CSV/TSV data
- **Coverage**: 2012-present

**Downloaded files location**: `election_data/`

| Year | File | Format | Notes |
|------|------|--------|-------|
| 2024 | `results-final.txt` | Tab-separated | Column: `Choice Name1` |
| 2022 | `results.txt` | Tab-separated | Column: `Choice Name` |
| 2020 | `Detailed vote totals.CSV` | CSV, latin-1 encoding | Skip first line (version header) |
| 2018 | `2018_data/contest_table.txt` | CSV, latin-1 | Sum: Absentee + Early + Election votes |
| 2016 | `2016_data/contest_table.txt` | CSV, latin-1 | Same as 2018 |
| 2014 | `2014_data/contest_table.txt` | CSV, latin-1 | Same as 2018 |
| 2012 | `2012_data/contest_table.txt` | CSV, latin-1 | Same as 2018 |

---

## YAML Field Reference

### Required Fields for All Cities

```yaml
city: slug-name                    # URL-safe identifier (lowercase, hyphens)
city_name: Full City Name          # Display name
website: https://...               # Official city website
council_url: https://...           # City council page
last_updated: 'YYYY-MM-DD'         # Last data verification date
```

### Member Fields

```yaml
members:
  - name: STRING                   # Full name as appears on city website
    position: STRING               # Mayor, Vice Mayor, Mayor Pro Tem, Councilmember
    district: STRING               # District 1, Ward 6, At-Large, etc.
    email: STRING
    phone: STRING
    term_start: INTEGER            # Year term began (e.g., 2024)
    term_end: INTEGER              # Year term ends (e.g., 2028)
    term_start_date: 'YYYY-MM-DD'  # Exact swearing-in date (for term limit calculation)
    term_end_date: 'YYYY-MM-DD'    # Exact term end date
    first_elected: INTEGER         # Year first elected (optional)
    notes: STRING                  # Special notes (vacancy, special election, etc.)
```

**Important**: `term_start_date` is used for exact term limit calculations. If a term limit took effect Nov 8, 2022, and someone was sworn in Dec 6, 2022, they ARE subject to the limit. Year-only comparison would miss this.

### Election Fields

```yaml
elections:
  election_system: STRING          # 'by-district', 'by-ward', 'at-large', 'mixed'
  term_length: INTEGER             # Default years per term (usually 4)
  mayor_term_length: INTEGER       # If mayor has different term (Costa Mesa, Santa Ana = 2)
```

### Term Limit Fields (STANDARDIZED)

All cities MUST have these fields, even if values are null:

```yaml
elections:
  term_limit: INTEGER or null      # Max consecutive terms/years allowed
  term_limit_type: STRING          # 'terms' or 'years' (default: 'terms')
  term_limit_cooldown: INTEGER     # Break period before eligible again
  term_limit_cooldown_unit: STRING # 'cycles' or 'years' (default: 'cycles')
  term_limit_effective: STRING     # Date limit took effect 'YYYY-MM-DD'
  term_limit_notes: STRING         # Human-readable explanation with ordinance refs
  term_limit_source: URL           # Link to municipal code section
```

**Examples:**

```yaml
# Aliso Viejo - 2 consecutive 4-year terms, 1 cycle (2 year) cooldown
term_limit: 2
term_limit_type: terms
term_limit_cooldown: 1
term_limit_cooldown_unit: cycle
term_limit_effective: "2022-11-08"
term_limit_notes: "Max consecutive 4-year terms per Ord. 2022-232. Applies to persons elected on/after Nov 8, 2022."
term_limit_source: https://www.codepublishing.com/CA/AlisoViejo/#!/AlisoViejo02/AlisoViejo0204.html

# Anaheim - 8 consecutive YEARS (not terms!)
term_limit: 8
term_limit_type: years
term_limit_cooldown: null
term_limit_cooldown_unit: null
term_limit_effective: null
term_limit_notes: "8 consecutive years combined for Mayor + Council per Charter § 503.5. Limit is in years, not terms."
term_limit_source: https://codelibrary.amlegal.com/codes/anaheim/latest/anaheim_ca/0-0-0-51937

# Cities without term limits
term_limit: null
term_limit_type: null
term_limit_cooldown: null
term_limit_cooldown_unit: null
term_limit_effective: null
term_limit_notes: null
term_limit_source: null
```

### Election History Fields

```yaml
elections:
  history:
    - year: 2024
      type: STRING                 # 'by-district', 'at-large', 'general'
      seats: [LIST]                # Seats up for election
      nomination_period: STRING    # "Month DD - Month DD, YYYY"
      notes: STRING                # Any special circumstances
      certified: STRING            # Certification date 'YYYY-MM-DD'
      resolution: STRING           # City resolution number
      source: URL                  # Link to certification document
      results_url: URL             # Link to results page
      winners:
        - district: STRING         # "District 1", "Mayor", "At-Large"
          winner: STRING           # Full name as appears on ballot
          votes: INTEGER           # From OC Registrar SOV
          runner_up: STRING        # Optional - second place
          runner_up_votes: INTEGER # Optional
          notes: STRING            # "re-elected", "appointed", etc.
      candidates:                  # Full candidate list from OC Registrar
        - district: STRING
          candidates:
            - name: STRING
              votes: INTEGER
              outcome: STRING      # 'won' or 'lost'
```

### Seats Up Fields

```yaml
elections:
  seats_up:
    - district: STRING             # "District 1", "Mayor", "At-Large"
      incumbent: STRING            # Current officeholder name
      term_length: INTEGER         # Optional - if different from default
```

---

## Database Schema

### Core Tables

| Table | Purpose |
|-------|---------|
| `cities` | All city information (75+ columns) |
| `people` | Council members and candidates |
| `terms` | Service terms linking people to cities |
| `elections` | Election events |
| `candidates` | Election candidates with votes and outcomes |
| `election_seats` | Seats up in each election |
| `election_cycles` | Recurring election patterns |
| `cable_channels` | TV broadcast info |
| `sources` | Data source citations |

### Key Views

| View | Purpose |
|------|---------|
| `v_current_councils` | Active council members |
| `v_term_limit_status` | Calculates terms remaining, eligible again date |
| `v_term_limit_cities` | Summary of cities with term limits |
| `v_upcoming_elections` | Next election details |

### Term Limit Calculation Logic

The `v_term_limit_status` view calculates:
- `terms_since_cutoff`: Terms served since term limit effective date
- `terms_remaining`: How many terms left before hitting limit
- `term_out_year`: Year member will term out (if applicable)
- `eligible_again`: Year member can run again after cooldown

**Important**: The calculation differs based on `term_limit_type`:
- `terms`: Counts discrete 4-year terms
- `years`: Counts cumulative years served (Anaheim's model)

---

## OC Registrar Election Data

### Parsing Scripts

Located in `election_data/`:

| Script | Purpose |
|--------|---------|
| `parse_all_elections.py` | Parse and display all city council races |
| `validate_against_yaml.py` | Compare OC data against existing YAML |
| `enrich_yaml.py` | Add vote counts and candidates to YAML |

### Running Validation

```bash
cd election_data
python validate_against_yaml.py
```

Output shows:
- `[OK]` - Data matches between OC Registrar and YAML
- `[!]` - Mismatch in vote counts or winner names
- `[?]` - Missing in OC Registrar (likely unopposed)
- `[+]` - Extra data in OC Registrar (losers not yet in YAML)

### Running Enrichment

```bash
# Preview changes (dry run)
python enrich_yaml.py aliso-viejo --dry-run

# Apply changes
python enrich_yaml.py aliso-viejo
```

The enrichment script:
1. Reads existing YAML (preserves comments with ruamel.yaml)
2. Matches winners against OC Registrar data
3. Adds vote counts to winners
4. Adds full candidate lists (including losers)
5. Writes updated YAML

### File Format Differences

| Years | Format | Key Differences |
|-------|--------|-----------------|
| 2024, 2022 | Tab-separated | `Choice Name1` vs `Choice Name` column |
| 2020 | CSV | First line is version header (skip it), latin-1 encoding |
| 2012-2018 | CSV | Different column names (`Contest_title`, `Candidate_name`), must sum vote columns |

### Contest Title Patterns

```
CITY OF ANAHEIM, Member, City Council, District 1
CITY OF ALISO VIEJO, Member, City Council
CITY OF COSTA MESA, Mayor
```

---

## Data Collection Procedures

### For Each City, Collect:

1. **From City Website:**
   - [ ] Council member names, photos, bios
   - [ ] Meeting schedule and location
   - [ ] Public comment procedures
   - [ ] Clerk contact information

2. **From Municipal Code:**
   - [ ] Term limits (if any)
   - [ ] Term limit effective date
   - [ ] Cooldown period
   - [ ] Election system (by-district vs at-large)

3. **From OC Registrar:**
   - [ ] Historical election results (2012-2024)
   - [ ] Vote counts for all candidates
   - [ ] Verify winner names match city records

### Verification Steps

1. Cross-reference OC Registrar vote counts with city-published results
2. Verify term start/end dates against election dates
3. Check for unopposed races (won't appear in SOV)
4. Note any mid-term appointments or vacancies

---

## Validation and Quality Control

### Automated Validation

```bash
# Validate YAML schema
python validate_schema.py

# Validate against OC Registrar
python election_data/validate_against_yaml.py

# Rebuild database and check for errors
python db/init_db.py
```

### Manual Verification Checklist

For each city:
- [ ] Current council members match city website
- [ ] Term end years are accurate
- [ ] Election history has vote counts from OC Registrar
- [ ] Term limits match municipal code
- [ ] All URLs are valid and current

---

## Known Issues and Challenges

### 1. Unopposed Candidates

**Issue**: Candidates who run unopposed do not appear in the OC Registrar Statement of Vote.

**Reason**: Per California Elections Code § 10229, cities can appoint sole nominees without holding an election.

**Solution**:
- Keep winner info from city sources for unopposed races
- Mark as `votes: null` in YAML
- Add note: `notes: "Appointed - unopposed per EC § 10229"`

**How to verify**: Check city council meeting minutes for appointment resolutions.

### 2. Name Variations

**Issue**: Names may differ between OC Registrar and city records.

**Examples**:
- `WILLIAM (BILL) A. PHILLIPS` vs `William A. Phillips`
- `RICHARD HURT` vs `Richard W. Hurt`

**Solution**: The validation script normalizes names by:
- Removing parenthetical nicknames
- Removing middle initials
- Case-insensitive comparison

### 3. At-Large to By-District Transitions

**Issue**: Several cities have recently transitioned from at-large to by-district elections.

**Cities affected**: Aliso Viejo, Cypress, Buena Park, and others

**Solution**: Use `transition_note` field and `type` in election history:
```yaml
transition_note: "Converted from at-large to by-district. Districts 1,3,5 elected 2024; Districts 2,4 in 2026."
history:
  - year: 2024
    type: by-district
    notes: "First district election after transition from at-large"
```

### 4. Term Limit Variations

**Issue**: Term limits vary significantly between cities.

| City | Limit | Type | Cooldown |
|------|-------|------|----------|
| Aliso Viejo | 2 | terms | 1 cycle |
| Anaheim | 8 | years | none |
| Fountain Valley | 3 | terms | 2 years |
| Dana Point | 2 | terms | unknown |

**Solution**: Use standardized fields with explicit `term_limit_type` and `term_limit_cooldown_unit`.

### 5. Data Encoding

**Issue**: Some OC Registrar files use latin-1 encoding, not UTF-8.

**Solution**: Parser scripts specify encoding:
```python
with open(filepath, 'r', encoding='latin-1') as f:
```

---

## TODO Checklist by City

### Cities with Term Limits (need full documentation)

| City | term_limit | term_limit_type | term_limit_notes | term_limit_source | Status |
|------|------------|-----------------|------------------|-------------------|--------|
| Aliso Viejo | 2 | terms | ✓ | ✓ | Complete |
| Anaheim | 8 | years | ✓ | ✓ | Complete |
| Dana Point | 2 | terms (assumed) | TODO | TODO | Needs research |
| Fountain Valley | 3 | terms | ✓ | ✓ | Complete |

### Cities Needing Election History Enrichment

Run `python election_data/enrich_yaml.py CITY --dry-run` for each:

| City | 2024 | 2022 | 2020 | 2018 | 2016 | Status |
|------|------|------|------|------|------|--------|
| Aliso Viejo | ✓ | ✓ | ✓ | ✓ | ✓ | Enriched |
| Anaheim | ✓ | ✓ | ✓ | - | - | Partial |
| Others | - | - | - | - | - | Not started |

### Data Quality TODO

- [ ] Research Dana Point term limit ordinance
- [ ] Add election history to all 34 cities
- [ ] Verify all term end dates
- [ ] Add full candidate lists from OC Registrar
- [ ] Cross-reference member photos with official sources
- [ ] Validate all municipal code URLs still work

---

## Scripts Reference

| Script | Location | Purpose |
|--------|----------|---------|
| `init_db.py` | `db/` | Import YAML to SQLite database |
| `query.py` | `db/` | Query database from command line |
| `parse_all_elections.py` | `election_data/` | Parse OC Registrar files |
| `validate_against_yaml.py` | `election_data/` | Compare OC vs YAML data |
| `enrich_yaml.py` | `election_data/` | Add vote counts to YAML |
| `validate_schema.py` | root | Validate YAML structure |
| `calculate_term_limits.py` | root | Term limit calculations |

---

## Appendix: OC Registrar URL Patterns

### Statement of Vote Archives

```
# 2020-2024 pattern
https://ocvote.gov/sites/default/files/elections/gen{YEAR}/results/media.zip

# 2012-2018 pattern
https://ocvote.gov/fileadmin/live/gen{YEAR}/Final/media.zip

# Special cases
2020: /gen2020/ (not gen2020nov)
2014: /gen2014/Final/ (with /Final/)
```

### Data Central

- Results: https://ocvote.gov/datacentral/?tab=results
- Maps: https://ocvote.gov/datacentral/?tab=maps
- Registration: https://ocvote.gov/datacentral/?tab=registration

---

*Last updated: 2026-01-29*
