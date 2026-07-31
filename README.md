# Dashboards

Public dashboard collection hosted at [austinwagner.org](https://austinwagner.org).

## For recruiters — start here

If evaluating this repo, skim these three dashboards (10 min total):

1. [`oc-city-councils/`](oc-city-councils/) — Civic-data pipeline covering all 34 OC cities. YAML source-of-truth → build script → JSON → dashboard, auto-rebuilt via GitHub Actions.
2. [`ivy/de-escalation/`](ivy/de-escalation/) — Primary-source research synthesis (21 sections, 35+ sources). Design pattern for AI-readable research corpora with citation traceability.
3. [`asuci/`](asuci/) — Playwright web scraper + daily GitHub Actions cron pulling UC Irvine student-government voting records.

Skip the game/fun stuff (`rabbit/`) and personal coursework (`ics5/`, `presentation/`, `sculc2026/`) unless curious.

## Active Dashboards

| Dashboard | Description | Updates |
|-----------|-------------|---------|
| [OC City Councils](oc-city-councils/) | Contact info and governance data for all 34 Orange County city councils | Auto via GitHub Actions |
| [ASUCI Senate](asuci/) | UC Irvine student government voting records and senator info | Daily via GitHub Actions |
| [Irvine City Council](irvine-city-council/) | Current Irvine city council members and governance info | Manual |
| [Flock ALPR Investigation](flock-investigation/) | Primary-source investigation into whether federal immigration agencies can reach Irvine PD's license-plate-reader data — sourced timeline, obtained MOUs and BSCC grant records | Manual |
| [ICE 287(g) Cooperation Tracker](ice-cooperation-tracker/) | Which local law-enforcement agencies hold 287(g) agreements with ICE, and who signed them — 1,314 agreements across 40 states, with signer identification for 18 states | Manual |
| [Document Search](doc-search/) | California public-records document search tool | Manual |
| [Metabolomics](metabolomics/) | Interactive visualization of plant metabolomics data with filtering and analysis | Manual |
| [Nursing Research Corpus](ivy/) | Primary-source research synthesis on structured de-escalation & restraint reduction in adult inpatient psychiatric care | Manual |
| [SCULC 2026](sculc2026/) | Conference presentation: Quantifying Mutual Intelligibility Using Language Models | Manual |
| [Kazakh Formality Presentation](presentation/) | LSCI 169 coursework: Formality and Honorifics in Kazakh | Manual |
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
├── metabolomics/               # Deploy artifact only — source is a separate repo
│   └── index.html              # Interactive dashboard (D3.js + DataTables)
│                               # built in ~/PROJECTS/metabolomics-dashboard
│
├── irvine-city-council/        # Irvine city council info
│   ├── generate.py             # Dashboard generator
│   └── index.html              # Council member dashboard
│
├── doc-search/                 # California public-records search tool
│   └── index.html              # Search interface
│
├── flock-investigation/        # OC Flock Safety ALPR investigation
│   ├── index.html              # Sourced timeline + findings
│   ├── data/                   # Obtained records: MOUs, BSCC grants, shared-network exports
│   ├── docs/                   # Research notes
│   └── Makefile                # `make dev` local preview, `make urls` link check
│
├── ice-cooperation-tracker/    # ICE 287(g) agreements + who signed them
│   ├── index.html              # Dashboard UI
│   ├── generate.py             # Builds the dashboard from the scraped signer DB
│   ├── fetch_sheriffs.py       # Per-state sheriff directory scrapers
│   ├── extract_signers.py      # Matches agreement signatories to named officials
│   ├── audit_data_quality.py   # Coverage + match-rate audit
│   ├── SCRAPING_METHODOLOGY.md # How each state's directory was obtained
│   └── archive/                # Raw scrape captures, kept for provenance
│
├── ivy/                        # Nursing research corpus (primary-source synthesis)
│   ├── index.html              # Landing page
│   └── de-escalation/          # Structured de-escalation & restraint-reduction research
│       ├── index.html          # 21-section synthesis
│       └── de-escalation.md    # Downloadable Markdown for AI ingest
│
├── sculc2026/                  # SCULC 2026 conference presentation
│   └── index.html              # Quantifying Mutual Intelligibility Using Language Models
│
├── presentation/               # LSCI 169 coursework
│   └── index.html              # Formality and Honorifics in Kazakh
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

Source lives in its own repo (`wagner-austin/metabolomics-dashboard`), checked out
at `~/PROJECTS/metabolomics-dashboard`. Build there, then copy the artifact here —
`metabolomics/index.html` in this repo is what GitHub Pages serves, so the copy
step is the deploy.

```bash
cd ~/PROJECTS/metabolomics-dashboard
make build            # poetry run python generate.py
cp index.html ~/PROJECTS/Dashboards/metabolomics/index.html
# then commit metabolomics/index.html here
```

### ICE 287(g) Cooperation Tracker

Signer identification is a scrape-then-match pipeline: per-state sheriff and
police-chief directories are fetched, then matched against the agency list in
ICE's own 287(g) Excel export. `SCRAPING_METHODOLOGY.md` records how each
state's directory was obtained, because the sources are not uniform.

```bash
cd ice-cooperation-tracker
python fetch_sheriffs.py        # per-state directory scrape
python extract_signers.py       # match signatories to named officials
python audit_data_quality.py    # coverage + match-rate report
python generate.py              # rebuild index.html
```

### Flock ALPR Investigation

```bash
cd flock-investigation
make dev     # local preview
make urls    # check every cited link still resolves
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
