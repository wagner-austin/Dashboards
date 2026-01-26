# Orange County City Councils

Contact information and meeting archives for all 34 Orange County city councils, with automated scraping to keep data current.

## Quick Start

```bash
# Install dependencies
pip install playwright pyyaml pdfplumber requests
playwright install firefox

# Update all city data (runs scrapers, updates JSON + YAML)
python update_all_data.py

# Update a specific city
python update_all_data.py --city "Anaheim"

# Rebuild dashboard after YAML changes
python build_dashboard.py

# Test all scrapers without saving
python test_all_scrapers.py
```

## Data Coverage

- **34 cities** with full council data
- **~190 council members** tracked
- **100% public comment email coverage** - every city has clerk/public comment contact info
- **Meeting schedules and locations** for all cities
- **Election info** - next election dates and seats up
- **Meeting archives** with agendas, minutes, and video links (for Granicus cities)
- Dynamic discovery - automatically adapts when council members change

### Public Comment Info (per city)

Each city YAML includes:
- Public comment email address
- City clerk contact (phone + email)
- Meeting schedule (day, time, location)
- Submission deadline
- Options: in-person, remote/Zoom, eComment portal, written email

## Project Structure

```
oc-city-councils/
├── update_all_data.py       # Main script - runs scrapers, updates data
├── build_dashboard.py       # Build dashboard JSON from YAML files
├── test_all_scrapers.py     # Test all scrapers
├── dashboard.html           # Interactive dashboard (reads dashboard_data.json)
├── dashboard_data.json      # Generated from YAML files (run build_dashboard.py)
├── scrapers/
│   ├── __init__.py          # Exports all scrapers + SCRAPERS registry
│   ├── base.py              # BaseScraper with core extraction methods
│   └── cities/              # One scraper per city (34 files)
│       ├── aliso_viejo.py
│       ├── anaheim.py
│       └── ...
├── cities/                   # Scraped JSON data (34 files)
│   ├── aliso-viejo.json
│   └── ...
├── _council_data/            # Curated YAML data (34 files)
│   ├── aliso-viejo.yaml
│   └── ...
└── _archive/                 # Deprecated code (for reference)
```

## Dashboard

Open `dashboard.html` in a browser to view an interactive dashboard with:
- City selector dropdown
- Quick links (website, council page, agendas, live stream)
- Meeting info, clerk contact, public comment details
- Council member cards with photos and contact info

**Important:** The dashboard reads from `dashboard_data.json`, which is generated from the YAML files. After editing YAML files, rebuild the dashboard:

```bash
python build_dashboard.py
```

## How It Works

### Dynamic Member Discovery

Each city scraper automatically discovers council members from the city website. No hardcoded member lists - when elections happen and members change, the scrapers adapt automatically.

```python
# Example: scrapers/cities/anaheim.py
class AnaheimScraper(BaseScraper):
    CITY_NAME = "Anaheim"
    COUNCIL_URL = "https://www.anaheim.net/173/City-Council"

    async def discover_members(self):
        # Finds all council member links on the page
        # Returns list of {name, position, url}
```

### Data Extraction

For each council member, scrapers extract:
- Name and position (Mayor, Mayor Pro Tem, Councilmember)
- Email address
- Phone number
- Profile URL
- Photo URL
- Bio text
- Term dates

For cities with Granicus portals, scrapers also extract:
- Meeting archives (agendas, minutes, video links)
- Meeting dates and names
- Direct links to video player (not downloads)

### Two Data Formats

1. **JSON** (`cities/*.json`) - Raw scraped data
2. **YAML** (`_council_data/*.yaml`) - Rich curated data with additional fields

The `update_all_data.py` script keeps both in sync, preserving manually curated content in YAML while updating with fresh scraped data.

## Usage

### Update All Cities

```bash
python update_all_data.py
```

This will:
1. Launch Firefox in headless mode
2. Visit each city's council page
3. Discover council members dynamically
4. Extract contact info from profile pages
5. Save to both JSON and YAML files

### Update Single City

```bash
python update_all_data.py --city "Costa Mesa"
```

### Test Without Saving

```bash
python test_all_scrapers.py
```

Shows results without modifying any files.

## Adding a New Scraper

Create a new file in `scrapers/cities/`:

```python
# scrapers/cities/new_city.py
from ..base import BaseScraper

class NewCityScraper(BaseScraper):
    CITY_NAME = "New City"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "newcity.gov"
    BASE_URL = "https://www.newcity.gov"
    COUNCIL_URL = "https://www.newcity.gov/council"

    async def discover_members(self):
        # Find member links on page
        members = []
        links = await self.page.query_selector_all("a")
        for link in links:
            # ... detect council member links
            members.append({"name": name, "position": position, "url": url})
        return members

    async def scrape(self):
        await self.visit_page(self.COUNCIL_URL, "council_main")
        members = await self.discover_members()
        for member in members:
            # Visit profile page, extract data
            result = await self.visit_page(member["url"], f"member_{member['name']}")
            self.add_council_member(...)
        return self.get_results()
```

Then add to `scrapers/cities/__init__.py` and `scrapers/__init__.py`.

## Data Files

### YAML Format (`_council_data/*.yaml`)

```yaml
city: anaheim
city_name: Anaheim
last_updated: '2026-01-25'
website: https://www.anaheim.net
council_url: https://www.anaheim.net/173/City-Council

meetings:
  schedule: 1st and 3rd Tuesdays
  time: 5:00 PM
  location:
    name: Council Chamber
    address: 200 S. Anaheim Blvd
    city_state_zip: Anaheim, CA 92805

clerk:
  title: City Clerk's Office
  phone: (714) 765-5166
  email: cityclerk@anaheim.net

public_comment:
  email: publiccomment@anaheim.net
  deadline: 2 hours prior to meeting
  in_person: true
  remote_live: false
  ecomment: false
  written_email: true
  time_limit: 3 minutes per speaker

elections:
  next_election: '2026-11-03'
  seats_up: [Mayor, District 3, District 5]
  term_length: 4
  election_system: by-district

members:
- name: Ashleigh E. Aitken
  position: Mayor
  district: Citywide
  email: aaitken@anaheim.net
  phone: (714) 765-5164
  photo_url: https://...
  bio: Ashleigh Aitken was elected as the 48th mayor...
  term_start: 2022
  term_end: 2026
```

### JSON Format (`cities/*.json`)

```json
{
  "city_name": "Irvine",
  "slug": "irvine",
  "last_updated": "2026-01-25",
  "council_members": [
    {
      "name": "Larry Agran",
      "position": "Mayor",
      "email": "LarryAgran@cityofirvine.org",
      "phone": "949-724-6000",
      "city_profile": "https://..."
    }
  ],
  "meetings": [
    {
      "name": "CITY COUNCIL REGULAR MEETING",
      "date": "January 14, 2025",
      "agenda_url": "https://irvine.granicus.com/AgendaViewer.php?...",
      "minutes_url": "https://irvine.granicus.com/MinutesViewer.php?...",
      "video_url": "https://irvine.granicus.com/player/clip/7000?view_id=68"
    }
  ]
}
```

See [SCHEMA.md](SCHEMA.md) for the complete YAML schema with all available fields.

## Troubleshooting

### 403 Errors

Some websites block automated requests. The scrapers use Firefox with stealth settings to avoid this. If you still get blocked:

1. Check if the website is down
2. Try again later (some sites rate-limit)
3. The scraper will still extract emails from the main page

### Missing Emails

If emails aren't found:

1. Check if the city uses a shared council email (some do)
2. Look for a separate directory page (e.g., `/Directory.aspx`)
3. Some cities only provide contact forms

### Import Errors

```bash
# Make sure you're in the right directory
cd oc-city-councils

# Test imports
python -c "from scrapers import SCRAPERS; print(len(SCRAPERS))"
```

## Dependencies

- Python 3.11+
- `playwright` - Browser automation
- `pyyaml` - YAML file handling
- `pdfplumber` - PDF parsing (for extracting Zoom info from city PDFs)
- `requests` - HTTP requests

## License

Public domain. Data is from public government sources.
