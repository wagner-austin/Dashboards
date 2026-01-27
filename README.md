# Dashboards

Public dashboard collection hosted at [wagner-austin.github.io/Dashboards](https://wagner-austin.github.io/Dashboards)

## Active Dashboards

| Dashboard | Description | Updates |
|-----------|-------------|---------|
| [OC City Councils](oc-city-councils/) | Contact info for all 34 Orange County city councils | Auto via GitHub Actions |
| [ASUCI Senate](asuci/) | UC Irvine student government voting records | Daily via GitHub Actions |

## Project Structure

```
Dashboards/
├── index.html                # Main landing page
├── oc-city-councils/         # OC city councils dashboard
│   ├── index.html            # Dashboard UI
│   ├── dashboard_data.json   # Auto-generated from YAML
│   ├── build_dashboard.py    # YAML → JSON builder
│   └── _council_data/        # Per-city YAML files (source of truth)
├── asuci/                    # ASUCI Senate dashboard
│   ├── generate.py           # Data scraper
│   └── index.html            # Generated dashboard
├── .github/workflows/        # GitHub Actions
│   ├── build-oc-councils.yml # Auto-rebuild OC councils on YAML change
│   └── update-dashboard.yml  # Daily ASUCI update
└── generate_all.py           # Run all generators
```

## Setup

```bash
# Install dependencies
pip install pyyaml playwright

# Install Playwright browsers (for ASUCI scraping)
playwright install firefox
```

## Usage

### OC City Councils

YAML files are the source of truth. Edit them directly, push, and GitHub Actions rebuilds the JSON.

```bash
# Manual rebuild
python oc-city-councils/build_dashboard.py
```

### ASUCI

```bash
# Generate dashboard
python asuci/generate.py
```

## Local Preview

```bash
python -m http.server 8000
# Visit http://localhost:8000
```

## License

Public domain. Data is from public government sources.
