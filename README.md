# Dashboards

Public dashboard collection hosted at [wagner-austin.github.io/Dashboards](https://wagner-austin.github.io/Dashboards)

## Active Dashboards

| Dashboard | Description | Updates |
|-----------|-------------|---------|
| [OC City Councils](oc-city-councils/) | Contact info and governance data for all 34 Orange County city councils | Auto via GitHub Actions |
| [ASUCI Senate](asuci/) | UC Irvine student government voting records and senator info | Daily via GitHub Actions |
| [Metabolomics](metabolomics/) | Interactive visualization of plant metabolomics data with filtering and analysis | Manual |
| [Irvine City Council](irvine-city-council/) | Current Irvine city council members and governance info | Manual |
| [Flock Investigation](flock-investigation/) | Research on Orange County ALPR camera deployment and surveillance networks | Manual |
| [ICS 5 Field Trips](ics5/) | UC Irvine ICS 5 sustainability field trip information | Manual |
| [Rabbit](rabbit/) | ASCII art animation engine with interactive bunny character | Manual |

## Project Structure

```
Dashboards/
├── index.html                  # Main landing page
├── pyproject.toml              # Poetry dependencies
├── generate_all.py             # Run all generators
│
├── oc-city-councils/           # OC city councils dashboard
│   ├── index.html              # Dashboard UI
│   ├── dashboard_data.json     # Auto-generated from YAML
│   ├── build_dashboard.py      # YAML → JSON builder
│   ├── _council_data/          # Per-city YAML files (source of truth)
│   └── docs/                   # Data guides and templates
│
├── asuci/                      # ASUCI Senate dashboard
│   ├── generate.py             # Playwright web scraper
│   └── index.html              # Generated dashboard
│
├── metabolomics/               # Metabolomics data visualization
│   ├── generate.py             # Data processing pipeline
│   ├── index.html              # Interactive dashboard (D3.js + DataTables)
│   └── *.xlsx, *.csv           # Source data files
│
├── irvine-city-council/        # Irvine city council info
│   ├── generate.py             # Dashboard generator
│   └── index.html              # Council member dashboard
│
├── flock-investigation/        # ALPR surveillance research
│   ├── index.html              # Investigation dashboard
│   ├── README.md               # Detailed findings and analysis
│   ├── scripts/                # FOIA scrapers and data tools
│   └── data/                   # PDFs, documents, and evidence
│
├── rabbit/                     # ASCII animation engine
│   ├── src/                    # TypeScript source
│   ├── tools/                  # GIF to ASCII converter
│   └── index.html              # Interactive animation
│
├── ics5/                       # ICS 5 field trip dashboard
│   └── index.html              # Field trip options
│
├── shared/                     # Shared utilities
│   ├── scrapers/               # Web scraping modules
│   └── utils/                  # Common utilities
│
└── .github/workflows/          # GitHub Actions
    ├── build-oc-councils.yml   # Auto-rebuild on YAML change
    └── update-dashboard.yml    # Daily ASUCI update
```

## Setup

### Using Poetry (Recommended)

```bash
# Install Poetry if needed
pip install poetry

# Install all dependencies
poetry install

# Install Playwright browsers (for web scraping)
poetry run playwright install firefox
```

### Manual Installation

```bash
pip install pyyaml playwright requests pillow opencv-python
playwright install firefox
```

### Rabbit (TypeScript/Node.js)

```bash
cd rabbit
npm install
npm run build
```

## Usage

### OC City Councils

YAML files in `_council_data/` are the source of truth. Edit them directly, push, and GitHub Actions rebuilds the JSON.

```bash
# Manual rebuild
python oc-city-councils/build_dashboard.py
```

### ASUCI Senate

```bash
# Full scrape with Playwright
python asuci/generate.py

# Quick refresh (Google Sheets only)
python asuci/generate.py --quick
```

### Metabolomics

```bash
# Generate dashboard from Excel data
python metabolomics/generate.py
```

### Rabbit

```bash
cd rabbit

# Development
npm run dev

# Build
npm run build

# Run tests
npm test

# Generate sprites from GIFs
python scripts/generate_sprites.py
```

### Generate All Dashboards

```bash
python generate_all.py
```

## Development

### Linting and Testing

```bash
# In rabbit directory
make check    # Run all linters and tests
make test     # Vitest + pytest with coverage
make build    # Generate sprites and compile
```

### Local Preview

```bash
python -m http.server 8000
# Visit http://localhost:8000
```

## Technologies

- **Python 3.11+** with Poetry for dependency management
- **TypeScript/Node.js** for Rabbit animation engine
- **Playwright** for web scraping
- **D3.js** and **DataTables** for interactive visualizations
- **GitHub Actions** for automated updates
- **GitHub Pages** for static site hosting

## License

Public domain. Data is from public government sources.
