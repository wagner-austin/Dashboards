# Election Data

This folder contains OC Registrar of Voters election data and scripts to populate/enrich city YAML files.

## Data Sources

All election data comes from the **Orange County Registrar of Voters**:
- **Website:** https://ocvote.gov/results
- **Direct link to past results:** https://ocvote.gov/results/election-results-archives

### Files and Their Sources

| File | Year | Source URL | Format |
|------|------|------------|--------|
| `results-final.txt` | 2024 | https://ocvote.gov/results (after certification) | Tab-separated |
| `results.txt` | 2022 | https://ocvote.gov/results/election-results-archives | Tab-separated |
| `Detailed vote totals.CSV` | 2020 | https://ocvote.gov/results/election-results-archives | CSV (header line 2) |
| `2018_data/contest_table.txt` | 2018 | Archive download from OC Registrar | CSV |
| `2016_data/contest_table.txt` | 2016 | Archive download from OC Registrar | CSV |
| `2014_data/contest_table.txt` | 2014 | Archive download from OC Registrar | CSV |
| `2012_data/contest_table.txt` | 2012 | Archive download from OC Registrar | CSV |

### How to Download Fresh Data

1. **2024/2022**: Go to https://ocvote.gov/results, click "Export" or download the results file after certification
2. **2020 and earlier**: Go to https://ocvote.gov/results/election-results-archives, find the election, download the detailed results

The files are typically named:
- `cumulative.txt` or `results.txt` (2022-2024)
- `Detailed vote totals.CSV` (2020)
- `contest_table.txt` inside zip archives (2018 and earlier)

## Scripts

### `populate_history.py` - Create Election History from Scratch

Parses all election data files and creates `history` entries in each city's YAML file with winners, vote counts, and full candidate lists.

```bash
# Preview what would be added
python populate_history.py --dry-run

# Add history to all cities
python populate_history.py

# Add history to single city
python populate_history.py tustin
```

**What it does:**
- Reads all election data files (2012-2024)
- Finds city council and mayoral races for each city
- Determines winners based on vote totals
- Creates structured history entries with:
  - Winners (name, district/seat, votes)
  - All candidates (name, votes, outcome: won/lost)

### `enrich_yaml.py` - Add Vote Counts to Existing History

If history entries already exist (with winners but no vote counts), this script adds vote counts and candidate lists from OC Registrar data.

```bash
# Preview changes for all cities
python enrich_yaml.py --all --dry-run

# Show match report (what was matched)
python enrich_yaml.py --all --report

# Apply to single city
python enrich_yaml.py aliso-viejo
```

### `validate_against_yaml.py` - Verify Data Accuracy

Compares YAML data against OC Registrar source files to verify accuracy.

```bash
python validate_against_yaml.py
```

Shows matches, mismatches, and verification percentages.

## Data Format Reference

### 2024/2022 Format (Tab-separated)
```
Contest Title    Choice Name1    Total Votes    ...
CITY OF TUSTIN Member, City Council, District 1    LEE FINK    4059    ...
```

Key columns:
- `Contest Title` - Contains city name and race type
- `Choice Name1` or `Choice Name` - Candidate name (UPPERCASE)
- `Total Votes` - Vote count

### 2020 Format (CSV)
```csv
#FormatVersion 1
Precinct,Contest Title,Choice Name,Total Votes,...
```
- First line is a comment, skip it
- `Contest Title`, `Choice Name`, `Total Votes` columns

### 2018 and Earlier Format (CSV)
```csv
Contest_title,Candidate_name,Absentee_votes,Early_votes,Election_Votes,...
```
- Vote total = Absentee_votes + Early_votes + Election_Votes
- Candidate names may be "LAST, FIRST" format

## For Claude AI / Future Reference

### To populate election history for a new election year:

1. Download the results file from https://ocvote.gov/results after certification
2. Save as `results-YYYY.txt` in this folder
3. Add parsing logic to `populate_history.py` if format changed
4. Run: `python populate_history.py --dry-run` to preview
5. Run: `python populate_history.py` to apply

### To verify data accuracy:

```bash
# Check against OC Registrar data
python validate_against_yaml.py

# Check schema coverage
python ../validate_schema.py --coverage
```

### To update a single city's election history:

```bash
python populate_history.py city-slug
# e.g., python populate_history.py tustin
```

### Data structure in YAML files:

```yaml
elections:
  history:
    - year: 2024
      type: by-district  # or 'at-large'
      winners:
        - district: District 1
          winner: Lee Fink
          votes: 4059
      candidates:
        - district: District 1
          candidates:
            - name: Lee Fink
              votes: 4059
              outcome: won
            - name: Tanner Douthit
              votes: 3735
              outcome: lost
```

## Known Issues

1. **Ballot measures mixed in**: Some years have "Yes"/"No" appearing as winners when ballot measures are in the same contest category. These need manual cleanup.

2. **Unopposed candidates**: Candidates who run unopposed (per EC 10229) don't appear in OC Registrar data because no election was held.

3. **Name variations**: OC Registrar uses UPPERCASE names, sometimes "LAST, FIRST" format. Scripts normalize to title case.

4. **Missing years**: Some cities don't have elections every cycle (odd years, special elections, etc.).
