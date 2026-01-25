# Orange County City Councils

Contact information for all 34 Orange County city council members, with automated scraping to keep data current.

## Quick Start

```bash
# Install dependencies (from parent directory)
poetry install
playwright install chromium
playwright install firefox

# Run scrapers (Firefox recommended for blocked sites)
python run_scrapers.py --all --browser firefox --stealth

# Preview changes before applying
python -c "from scrapers.updater import preview_updates; preview_updates('scrape_results.json', 'oc_cities_master.json')"

# Apply updates to master JSON
python -c "from scrapers.updater import apply_updates; apply_updates('scrape_results.json', 'oc_cities_master.json')"
```

## Data Coverage

### Cities with Individual Council Member Emails

| City | Members | Email Coverage | Platform |
|------|---------|----------------|----------|
| Aliso Viejo | 5 | 5/5 (100%) | CivicPlus |
| Anaheim | 6 | 6/6 (100%) | CivicPlus Custom |
| Laguna Beach | 5 | 5/5 (100%) | Granicus |
| Laguna Hills | 5 | 5/5 (100%) | CivicPlus |
| Orange | 7 | 7/7 (100%) | Custom CMS |

### Cities with Generic Council Email Only

| City | Generic Email | Notes |
|------|---------------|-------|
| Brea | N/A | Only found mayorsaward@ |
| La Habra | CityCouncil@lahabraca.gov | Individual emails not public |
| La Palma | citycouncil@lapalmaca.gov | Individual emails not public |
| Mission Viejo | citycouncil@cityofmissionviejo.org | Uses contact form |
| Tustin | N/A | Uses contact form only |

### All 34 OC Cities

Full list in `oc_cities_master.json` with data for:
- Council member names, positions, districts
- Email addresses (individual or generic)
- Phone numbers
- City profile URLs
- City website, Instagram, public comment methods

## Project Structure

```
oc-city-councils/
├── scrapers/                    # Modular scraper system
│   ├── __init__.py
│   ├── base.py                  # Base scraper class
│   ├── civicplus.py             # CivicPlus platform scrapers
│   ├── anaheim.py               # Anaheim-specific scraper
│   ├── custom.py                # Custom scrapers (Orange, Laguna Beach, etc.)
│   ├── stealth_scraper.py       # Firefox stealth scraper for blocked sites
│   └── updater.py               # Safe JSON updater with backup
├── backups/                     # Auto-created backups before updates
├── data/                        # Intermediate data files
├── oc_cities_master.json        # Master data file (34 cities)
├── scrape_results.json          # Latest scrape output
├── run_scrapers.py              # Main scraper runner
├── generate_html.py             # HTML dashboard generator
└── index.html                   # Generated dashboard
```

## Scraper Architecture

### Base Scraper (`scrapers/base.py`)

All scrapers inherit from `BaseScraper` which provides:

- **Page visiting** with error handling and logging
- **Email extraction** from text and mailto: links
- **Phone extraction** with pattern matching
- **Email-to-name matching** for when main page has emails but individual pages fail
- **Council member management**

### Platform-Specific Scrapers

| Platform | Cities | File |
|----------|--------|------|
| CivicPlus | Aliso Viejo, La Habra, La Palma, Laguna Hills, Brea | `civicplus.py` |
| CivicPlus Custom | Anaheim | `anaheim.py` |
| Granicus | Laguna Beach | `custom.py` |
| Custom CMS | Orange, Mission Viejo, Tustin | `custom.py` |

### Email Matching

When individual council member pages return 403 errors, the scraper:

1. Extracts all emails from the main council page
2. Matches emails to member names using patterns:
   - `firstlast@domain` (e.g., danslater@)
   - `first.last@domain` (e.g., dan.slater@)
   - `flast@domain` (e.g., dslater@)
   - `last@domain` (e.g., slater@)

## Usage

### Basic Scraping

```bash
# Scrape cities with missing data (default)
python run_scrapers.py

# Scrape specific city
python run_scrapers.py --city "Anaheim"

# Scrape all cities
python run_scrapers.py --all
```

### Browser Options

```bash
# Use Chromium (default)
python run_scrapers.py --browser chromium

# Use Firefox (better for bot detection)
python run_scrapers.py --browser firefox

# Enable stealth mode (recommended)
python run_scrapers.py --browser firefox --stealth
```

### Safe Updates

The updater has safety features to prevent data loss:

1. **Never overwrites** existing data with null/empty values
2. **Only fills** blank fields with new data
3. **Creates backup** before any changes
4. **Dry-run mode** by default to preview changes

```python
from scrapers.updater import MasterJSONUpdater

# Preview changes (safe)
updater = MasterJSONUpdater('oc_cities_master.json')
updater.update_from_scrape_results(scrape_results, dry_run=True)

# Apply changes (creates backup first)
updater.update_from_scrape_results(scrape_results, dry_run=False)
```

### Election Detection

The updater can detect when council members change after elections:

```python
# Compares scraped names to existing names by position
# If "Mayor" position has different name, flags as new member
changes = updater.detect_member_changes(city_name, existing_members, scraped_members)
```

## Troubleshooting

### 403 Errors (Blocked)

Some city websites block automated requests. Solutions:

1. **Use Firefox with stealth mode**:
   ```bash
   python run_scrapers.py --city "Orange" --browser firefox --stealth
   ```

2. **The scraper will still work** because emails are extracted from the main council page and matched to members.

### Missing Emails

If emails aren't matched:

1. Check if the city uses a generic email (many do)
2. Verify council member names match exactly
3. Check `emails_found` in `scrape_results.json` for available emails

### Backup Recovery

If something goes wrong:

```bash
# Backups are in backups/ folder
cp backups/oc_cities_master_BACKUP_YYYYMMDD_HHMMSS.json oc_cities_master.json
```

## Data Fields

### City Object

```json
{
  "city_name": "Aliso Viejo",
  "website": "https://www.avcity.org",
  "council_url": "https://avcity.org/222/City-Council",
  "email": "city-council@avcity.org",
  "phone": "949-425-2500",
  "instagram": "@cityofalisoviejo",
  "public_comment_url": "https://...",
  "council_members": [...]
}
```

### Council Member Object

```json
{
  "name": "Max Duncan",
  "position": "Mayor",
  "district": null,
  "email": "mduncan@avcity.org",
  "phone": "949-425-2510",
  "personal_website": null,
  "city_profile": "https://avcity.org/294/Mayor-Max-Duncan",
  "instagram": null
}
```

## Adding a New City Scraper

1. Create scraper class inheriting from `BaseScraper`:

```python
# In scrapers/custom.py
class NewCityScraper(BaseScraper):
    CITY_NAME = "New City"
    PLATFORM = "custom"
    CITY_DOMAIN = "newcity.org"

    MEMBERS = [
        {"name": "John Doe", "position": "Mayor"},
        # ...
    ]

    async def scrape(self):
        await self.visit_page("https://newcity.org/council", "council_main")
        # Add members
        for member in self.MEMBERS:
            self.add_council_member(name=member["name"], position=member["position"])
        # Match emails
        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()
```

2. Register in `run_scrapers.py`:

```python
from scrapers.custom import NewCityScraper

SCRAPERS = {
    # ...
    "New City": NewCityScraper,
}
```

## Dependencies

- `playwright` - Headless browser automation
- `aiohttp` - Async HTTP requests (optional)
- Python 3.11+

## License

Public domain. Data is from public government sources.
