# Scraper Development Guide

How the OC City Council scrapers work and how to create/modify them.

## Architecture

```
scrapers/
├── base.py              # BaseScraper - core extraction methods
├── __init__.py          # Exports + SCRAPERS registry
└── cities/              # One file per city
    ├── __init__.py      # Exports all city scrapers
    ├── aliso_viejo.py
    ├── anaheim.py
    └── ...
```

## Key Principles

1. **Dynamic Discovery** - No hardcoded member lists. Scrapers find members from the website.
2. **Self-Contained** - Each city scraper is a single file with all logic needed.
3. **Consistent Interface** - All scrapers inherit from `BaseScraper` and implement `scrape()`.

## BaseScraper Methods

### Page Navigation

```python
await self.visit_page(url, page_name)
# Returns: {"status": "success/error", "emails": [...], "phones": [...]}
```

### Data Extraction

```python
await self.get_page_text()              # Get all text on page
await self.extract_photo_url(name, base_url)  # Find member photo
await self.extract_bio()                # Extract biography text
await self.extract_term_info()          # Returns (term_start, term_end)
```

### Email Matching

```python
self.match_email_to_name(name, emails, city_domain)
# Tries patterns: firstlast@, first.last@, flast@, last@

self.match_emails_to_members(city_domain)
# Matches all unmatched members to available emails
```

### Adding Members

```python
self.add_council_member(
    name="John Smith",
    position="Mayor",
    district="District 1",
    email="jsmith@city.gov",
    phone="555-1234",
    profile_url="https://...",
    photo_url="https://...",
    bio="Biography text...",
    term_start=2024,
    term_end=2028,
)
```

## Scraper Template

```python
"""
City Name City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class CityNameScraper(BaseScraper):
    """City Name - Platform type with dynamic member discovery."""

    CITY_NAME = "City Name"
    PLATFORM = "civicplus"  # civicplus, granicus, wordpress, custom
    CITY_DOMAIN = "cityname.gov"
    BASE_URL = "https://www.cityname.gov"
    COUNCIL_URL = "https://www.cityname.gov/council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """Find council members from the main council page."""
        members = []
        seen_urls = set()

        try:
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text:
                    continue

                # Detect position from link text
                text_lower = text.lower()
                position = None
                if "mayor pro tem" in text_lower:
                    position = "Mayor Pro Tem"
                elif "mayor" in text_lower:
                    position = "Mayor"
                elif "council" in text_lower:
                    position = "Councilmember"

                if not position:
                    continue

                # Extract name
                name = self._extract_name_from_text(text)
                if not name:
                    continue

                url = urljoin(self.BASE_URL, href)
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                members.append({"name": name, "position": position, "url": url})
                print(f"      Found: {position} {name}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        # Visit main council page
        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        # Discover members
        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} members")

        # Scrape each member's profile page
        for member in members:
            print(f"    Scraping: {member['name']}")
            result = await self.visit_page(member["url"], f"member_{member['name']}")

            if result.get("status") == "success":
                photo_url = await self.extract_photo_url(member["name"], self.BASE_URL)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                member_email = None
                if result.get("emails"):
                    member_email = self.match_email_to_name(
                        member["name"], result["emails"], self.CITY_DOMAIN
                    )

                self.add_council_member(
                    name=member["name"],
                    position=member["position"],
                    email=member_email,
                    phone=result.get("phones", [None])[0],
                    profile_url=member["url"],
                    photo_url=photo_url,
                    bio=bio,
                    term_start=term_start,
                    term_end=term_end,
                )
            else:
                self.add_council_member(
                    name=member["name"],
                    position=member["position"],
                    profile_url=member["url"],
                )

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()
```

## Common Discovery Patterns

### CivicPlus Directory.aspx

```python
async def discover_members(self):
    members = []
    links = await self.page.query_selector_all('a[href*="Directory.aspx?EID="]')
    for link in links:
        href = await link.get_attribute("href")
        name = (await link.inner_text()).strip()
        # ...
```

### Position Keywords in Link Text

```python
# Links like "Mayor John Smith" or "Councilmember Jane Doe"
text_lower = text.lower()
if "mayor pro tem" in text_lower:
    position = "Mayor Pro Tem"
elif "mayor" in text_lower:
    position = "Mayor"
elif "council" in text_lower:
    position = "Councilmember"
```

### URL Pattern Matching

```python
# URLs like /council/mayor-john-smith or /123/Mayor-John-Smith
match = re.search(r'/(mayor|council)[-/](.+?)/?$', href.lower())
if match:
    position = "Mayor" if "mayor" in match.group(1) else "Councilmember"
```

### Text Pattern Matching

```python
# For pages with text like "John Smith, Mayor, District 1"
text = await self.get_page_text()
pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s*(Mayor|Councilmember)'
for match in re.finditer(pattern, text):
    name, position = match.groups()
```

## Testing

```bash
# Test single city
python -c "
import asyncio
from playwright.async_api import async_playwright
from scrapers.cities.anaheim import AnaheimScraper

async def test():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        scraper = AnaheimScraper(page)
        result = await scraper.scrape()
        print(f'Found {len(result[\"council_members\"])} members')
        await browser.close()

asyncio.run(test())
"

# Test all scrapers
python test_all_scrapers.py
```

## Registering a New Scraper

1. Create `scrapers/cities/new_city.py`

2. Add to `scrapers/cities/__init__.py`:
```python
from .new_city import NewCityScraper
```

3. Add to `scrapers/__init__.py`:
```python
from .cities import NewCityScraper

SCRAPERS = {
    # ...
    "New City": NewCityScraper,
}
```

4. Add to `update_all_data.py`:
```python
from scrapers.cities import NewCityScraper

SCRAPERS = {
    # ...
    "New City": ("new-city", NewCityScraper),
}
```

## Debugging Tips

1. **Print page text** to understand structure:
   ```python
   text = await self.get_page_text()
   print(text[:2000])
   ```

2. **Check for emails** on the main page:
   ```python
   result = await self.visit_page(url, "test")
   print(f"Emails found: {result.get('emails', [])}")
   ```

3. **Use browser devtools** to find selectors:
   ```bash
   playwright codegen https://citywebsite.gov/council
   ```

4. **Check for 403 blocks** - Firefox handles these better than Chromium.
