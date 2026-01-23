# Dashboards

Personal dashboard collection hosted at [austinwagner.org](https://austinwagner.org)

## Dashboards

- **ASUCI Senate** - UC Irvine student government (auto-updates daily)
- **Metabolomics** - Tree metabolomics analysis

## Adding a Dashboard

1. Create folder with `index.html`
2. If it needs auto-updates, add `generate.py` and list in `generate_all.py`
3. Push to main

## Local Dev

```bash
poetry install
playwright install chromium
poetry run python generate_all.py
```
