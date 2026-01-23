# Dashboards

Personal dashboard collection - auto-updating static sites hosted on GitHub Pages.

## Dashboards

| Dashboard | Description | Update Frequency |
|-----------|-------------|------------------|
| [ASUCI Senate](/asuci/) | UC Irvine student government meetings, attendance, voting records | Daily |

## How It Works

1. **GitHub Actions** runs daily at 6 AM UTC (10 PM PST)
2. **Playwright** scrapes live data from various sources
3. **Static HTML** is generated with embedded data
4. **GitHub Pages** serves the updated dashboards

## Adding a New Dashboard

1. Create a new folder: `mkdir my-dashboard`
2. Add a `generate.py` script that outputs `index.html`
3. Add the folder name to `DASHBOARDS` list in `generate_all.py`
4. Push - the workflow handles the rest

## Local Development

```bash
# Install dependencies
poetry install
playwright install chromium

# Generate all dashboards
poetry run python generate_all.py

# Or generate a specific one
poetry run python asuci/generate.py
```

## Manual Trigger

Go to Actions → Update Dashboards → Run workflow

## Tech Stack

- Python 3.12
- Playwright (headless browser for JS-rendered content)
- Requests (API/sheet fetching)
- GitHub Actions (scheduled updates)
- GitHub Pages (hosting)
