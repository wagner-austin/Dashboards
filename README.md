# Dashboards

Public dashboard collection hosted at [austinwagner.org](https://austinwagner.org)

## Projects

### Active Dashboards

| Dashboard | Description | Auto-Updates |
|-----------|-------------|--------------|
| [ASUCI Senate](asuci/) | UC Irvine student government voting records | Daily via GitHub Actions |
| [Metabolomics](metabolomics/) | Tree metabolomics research analysis | Manual |
| [ICE 287(g) Cooperation](ice-cooperation/) | Tracking law enforcement ICE agreements and signers | Manual |
| [Irvine City Council](irvine-city-council/) | Irvine city council member info | Manual |
| [OC City Councils](oc-city-councils/) | All 34 Orange County city council contacts | Manual (with auto-scraping) |

### Project Structure

```
Dashboards/
├── asuci/                    # ASUCI Senate dashboard
│   ├── generate.py           # Data scraper and HTML generator
│   └── index.html            # Generated dashboard
├── ice-cooperation/          # ICE 287(g) agreements tracker
│   ├── generate.py           # Dashboard generator
│   ├── fetch_all_signers.py  # Sheriff data matcher
│   ├── signer_data.json      # Matched signer data
│   └── index.html            # Generated dashboard
├── irvine-city-council/      # Irvine council dashboard
│   ├── generate.py           # Dashboard generator
│   └── index.html            # Generated dashboard
├── metabolomics/             # Metabolomics research dashboard
│   └── index.html            # Static dashboard
├── oc-city-councils/         # OC city councils project
│   ├── scrapers/             # Modular web scrapers
│   ├── oc_cities_master.json # Master data (34 cities)
│   ├── run_scrapers.py       # Main scraper runner
│   └── index.html            # Generated dashboard
├── shared/                   # Shared utilities
├── generate_all.py           # Run all generators
├── pyproject.toml            # Python dependencies
└── index.html                # Main landing page
```

## Setup

### Prerequisites

- Python 3.11+
- Poetry (dependency management)
- Playwright (for web scraping)

### Installation

```bash
# Install dependencies
poetry install

# Install Playwright browsers
playwright install chromium
playwright install firefox  # Optional: better for bot detection
```

### Running Generators

```bash
# Run all generators
poetry run python generate_all.py

# Run specific dashboard
poetry run python asuci/generate.py
poetry run python ice-cooperation/generate.py
poetry run python oc-city-councils/run_scrapers.py --all --browser firefox
```

## Adding a New Dashboard

1. Create a folder with `index.html`
2. If it needs auto-updates:
   - Add `generate.py` script
   - Add to `generate_all.py`
   - (Optional) Add GitHub Actions workflow
3. Push to main branch

## Tech Stack

- **Python** - Data scraping and processing
- **Playwright** - Headless browser automation
- **GitHub Pages** - Static hosting
- **GitHub Actions** - Automated updates

## Development

### Local Preview

```bash
# Simple HTTP server
python -m http.server 8000
# Visit http://localhost:8000
```

### Code Style

- Python: Follow PEP 8
- HTML: Minimal, inline CSS preferred for single-file dashboards
- JSON: 2-space indentation

## License

Public domain. Data is from public government sources.
