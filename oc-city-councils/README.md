# Orange County City Councils

Contact information and meeting details for all 34 Orange County city councils.

**Live Dashboard:** [https://wagner-austin.github.io/Dashboards/oc-city-councils/](https://wagner-austin.github.io/Dashboards/oc-city-councils/)

## Data

The YAML files in `_council_data/` are the **golden source of truth**. They have been manually verified against official city websites.

### What's Included (per city)

- **Council members** - names, positions, districts, terms
- **Contact info** - emails, phone numbers, city profile pages
- **Meeting schedule** - day, time, location
- **Public comment info** - email, deadline, time limits, remote options
- **City clerk** - name, phone, email
- **Quick links** - agendas, live stream, video archives

## Usage

### View the Dashboard

Open `index.html` in a browser, or visit the live site above.

### Edit City Data

1. Edit the YAML file in `_council_data/` (e.g., `anaheim.yaml`)
2. Run `python build_dashboard.py` to rebuild the JSON
3. Commit and push

**Or just push the YAML changes** - GitHub Actions will auto-rebuild the JSON.

### Rebuild Dashboard Manually

```bash
python build_dashboard.py
```

This reads all YAML files and outputs `dashboard_data.json`.

## Project Structure

```
oc-city-councils/
├── index.html              # Dashboard (reads dashboard_data.json)
├── dashboard_data.json     # Auto-generated from YAML files
├── build_dashboard.py      # YAML → JSON builder
├── _council_data/          # ✅ YAML files (golden source of truth)
│   ├── aliso-viejo.yaml
│   ├── anaheim.yaml
│   └── ... (34 cities)
├── scrapers/               # Legacy scrapers (reference only)
└── _archive/               # Disabled scripts
```

## YAML Format

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
  phone: (714) 765-5164
  term_start: 2022
  term_end: 2026

meetings:
  schedule: 1st and 3rd Tuesdays
  time: 5:00 PM
  location:
    name: Council Chamber
    address: 200 S. Anaheim Blvd
    city_state_zip: Anaheim, CA 92805

clerk:
  name: Theresa Bass
  title: City Clerk
  phone: (714) 765-5166
  email: cityclerk@anaheim.net

public_comment:
  in_person: true
  remote_live: false
  written_email: true
  email: publiccomment@anaheim.net
  time_limit: 3 minutes per speaker
  deadline: 2 hours prior to meeting

council:
  size: 7
  districts: 6
  at_large: 1
  mayor_elected: true
```

## GitHub Actions

When you push changes to any YAML file in `_council_data/`, the `build-oc-councils.yml` workflow automatically:

1. Runs `build_dashboard.py`
2. Commits the updated `dashboard_data.json`
3. Pushes to the repo

No manual rebuild needed.

## Important Notes

⚠️ **Do NOT run the legacy scrapers** - they can overwrite verified data. The scraper scripts have been moved to `_archive/`.

✅ **YAML is the source of truth** - edit YAML files directly, not JSON.

✅ **Dashboard auto-rebuilds** - just push YAML changes.

## License

Public domain. Data is from public government sources.
