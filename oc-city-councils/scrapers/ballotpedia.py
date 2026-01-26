"""
Ballotpedia Scraper for Orange County City Councils

Scrapes term/district data from Ballotpedia for cities that have coverage.
Outputs to config/known_terms.yaml.

IMPORTANT: Ballotpedia only covers the 100 largest US cities by population.
In Orange County, only 3 cities have coverage:
- Anaheim (~350k pop)
- Santa Ana (~310k pop)
- Irvine (~300k pop)

The other 31 OC cities are "outside coverage scope" and won't have data.
For those cities, term data must come from other sources (city websites, etc).

Usage:
    python -m scrapers.ballotpedia

After elections, run this to update term data for covered cities.
"""
import asyncio
import re
import yaml
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright


# Only the 3 OC cities that Ballotpedia covers (top 100 US cities by population)
# Other OC cities are "outside coverage scope" on Ballotpedia
COVERED_CITIES = {
    "anaheim": "Anaheim,_California",      # ~350k pop
    "irvine": "Irvine,_California",        # ~300k pop
    "santa_ana": "Santa_Ana,_California",  # ~310k pop
}


class BallotpediaScraper:
    """Scrapes council member term data from Ballotpedia."""

    BASE_URL = "https://ballotpedia.org"

    def __init__(self, page):
        self.page = page
        self.results = {}

    def normalize_name(self, name):
        """Normalize a name for matching (lowercase, no extra spaces)."""
        return " ".join(name.lower().strip().split())

    async def scrape_city(self, city_key, ballotpedia_slug):
        """Scrape council members for a single city."""
        url = f"{self.BASE_URL}/{ballotpedia_slug}"
        members = []

        print(f"  Scraping {city_key}...")

        try:
            await self.page.goto(url, timeout=30000)
            # Wait for page to fully load - Ballotpedia uses dynamic content
            await self.page.wait_for_timeout(2000)

            # Scroll down to trigger lazy loading of council section
            await self.page.evaluate("window.scrollTo(0, 1000)")
            await self.page.wait_for_timeout(1000)
            await self.page.evaluate("window.scrollTo(0, 2000)")
            await self.page.wait_for_timeout(1000)
            await self.page.evaluate("window.scrollTo(0, 0)")
            await self.page.wait_for_timeout(1000)

            # Also wait for any tables to appear
            try:
                await self.page.wait_for_selector("table", timeout=5000)
            except:
                pass

            # Get page text for fallback parsing
            text = await self.page.inner_text("body")

            # First, look for city council specific section
            # Ballotpedia has sections with headers like "City council"
            council_section = None
            headings = await self.page.query_selector_all("h2, h3, h4")
            for heading in headings:
                heading_text = (await heading.inner_text()).lower()
                if "city council" in heading_text or "council members" in heading_text:
                    # Found council section - look for next table
                    council_section = heading
                    break

            # First try to find specific officeholder table by ID
            officeholder_table = await self.page.query_selector("#officeholder-table")
            if officeholder_table:
                tables = [officeholder_table]
            else:
                # Fall back to all tables
                tables = await self.page.query_selector_all("table")

            for idx, table in enumerate(tables):
                # Use textContent instead of inner_text to avoid CSS visibility issues
                table_text = await table.evaluate("el => el.textContent")
                table_lower = table_text.lower()

                # Skip tables that are clearly federal/state officials (not city)
                if "u.s. senate" in table_lower or "u.s. house" in table_lower:
                    continue
                if "governor" in table_lower and "mayor" not in table_lower:
                    continue

                # Look for tables with term info
                # Check for header text or year patterns (2024-2030)
                has_term_info = any(x in table_lower for x in [
                    "date assumed office", "term ends", "assumed office",
                    "date assumed", "term end"
                ])
                # Also check for year patterns indicating term data
                has_year_patterns = bool(re.search(r'\b202[4-9]\b.*\b202[6-9]\b', table_text))

                if not has_term_info and not has_year_patterns:
                    continue

                # Check if this table has city-level positions (District X, At-Large, or Mayor)
                has_city_positions = any(x in table_lower for x in [
                    "district 1", "district 2", "district 3", "district 4",
                    "district 5", "district 6", "district 7",
                    "council district 1", "council district 2", "council district 3",
                    "council district 4", "council district 5", "council district 6",
                    "at-large", "at large", "ward 1", "ward 2",
                    "city council ward 1", "city council ward 2"
                ])

                # Also accept if the table mentions city council
                if not has_city_positions:
                    # Check if table or surrounding context mentions city council
                    has_council_mention = "city council" in table_lower or "council member" in table_lower
                    if not has_council_mention:
                        parent = await table.evaluate("el => el.closest('section, div')?.textContent?.slice(0, 500) || ''")
                        has_council_mention = "city council" in parent.lower()

                    if not has_council_mention:
                        continue

                rows = await table.query_selector_all("tr")

                for row in rows:
                    cells = await row.query_selector_all("td, th")
                    if len(cells) < 2:
                        continue

                    # Use textContent for reliable text extraction
                    row_text = await row.evaluate("el => el.textContent")
                    row_lower = row_text.lower()

                    # Skip header rows
                    if "office" in row_lower and "name" in row_lower:
                        continue
                    if "date assumed" in row_lower and "date term" in row_lower:
                        continue

                    # Skip state-level positions
                    if any(x in row_lower for x in ["governor", "attorney general", "treasurer", "secretary of state", "controller", "superintendent", "lieutenant"]):
                        continue

                    # Extract data from row
                    member_data = await self.parse_council_row(row, cells, city_key)
                    if member_data:
                        members.append(member_data)

            # If table parsing didn't work, try text patterns
            if not members:
                members = await self.parse_from_text(text, city_key)

            print(f"    Found {len(members)} members")

        except Exception as e:
            print(f"    ERROR: {str(e)[:100]}")

        return members

    async def parse_council_row(self, row, cells, city_key):
        """Parse a single table row for council member data.

        Ballotpedia officeholder table structure:
        - Cell 0: Office (District X, Ward X, At-Large, Mayor, etc.)
        - Cell 1: Name (person's full name, usually a link)
        - Cell 2: Party (Nonpartisan, Democratic, Republican)
        - Cell 3: Date assumed office (Month Day, Year)
        - Cell 4: Date term ends (Year)
        """
        try:
            if len(cells) < 4:
                return None

            # Get cell contents using textContent for reliability
            cell_texts = []
            for cell in cells:
                text = await cell.evaluate("el => el.textContent")
                cell_texts.append(text.strip())

            # Cell 0: Office/Position
            office = cell_texts[0].lower() if len(cell_texts) > 0 else ""

            # Cell 1: Name - look for link first, then plain text
            name = None
            if len(cells) > 1:
                name_cell = cells[1]
                # Try to get name from link (more reliable)
                name_link = await name_cell.query_selector("a")
                if name_link:
                    name = await name_link.evaluate("el => el.textContent")
                    name = name.strip() if name else None
                else:
                    name = cell_texts[1] if len(cell_texts) > 1 else None

            # Validate name - must be 2+ words, not contain position keywords
            if not name or len(name.split()) < 2:
                return None
            name_lower = name.lower()
            if any(x in name_lower for x in ["council", "district", "ward", "mayor", "nonpartisan", "democratic", "republican"]):
                return None

            # Extract district/position from cell 0
            district = None
            district_match = re.search(r'district\s*(\d+)', office)
            ward_match = re.search(r'ward\s*(\d+)', office)
            if district_match:
                district = f"District {district_match.group(1)}"
            elif ward_match:
                district = f"Ward {ward_match.group(1)}"
            elif "at-large" in office or "at large" in office:
                district = "At-Large"
            elif "mayor" in office:
                district = "Mayor"

            # Cell 3 or 4: Date assumed office (contains month/day/year)
            term_start = None
            for i in range(2, len(cell_texts)):
                text = cell_texts[i]
                # Look for full date format: "December 10, 2024"
                date_match = re.search(r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d+,?\s*(\d{4})', text.lower())
                if date_match:
                    term_start = int(date_match.group(1))
                    break

            # Last cell is usually term end year
            term_end = None
            if len(cell_texts) >= 4:
                last_cells = cell_texts[-2:]  # Check last 2 cells
                for text in last_cells:
                    year_match = re.search(r'\b(202[4-9]|203\d)\b', text)
                    if year_match:
                        term_end = int(year_match.group(1))

            # If no term_start but have term_end, estimate
            if not term_start and term_end:
                term_start = term_end - 4

            return {
                "name": name,
                "district": district,
                "term_start": term_start,
                "term_end": term_end,
            }

        except Exception as e:
            return None

    async def parse_from_text(self, text, city_key):
        """Fallback: parse council members from page text using various patterns."""
        members = []

        # Ballotpedia format: "City Council District X\nName\nNonpartisan\nDate\nYear"
        # Split by lines and look for patterns
        lines = text.split('\n')

        i = 0
        while i < len(lines) - 3:
            line = lines[i].strip()
            line_lower = line.lower()

            # Look for district/position lines
            district = None
            if 'city council district' in line_lower:
                district_match = re.search(r'district\s*(\d+)', line_lower)
                if district_match:
                    district = f"District {district_match.group(1)}"
            elif 'city council ward' in line_lower:
                ward_match = re.search(r'ward\s*(\d+)', line_lower)
                if ward_match:
                    district = f"Ward {ward_match.group(1)}"
            elif 'at-large' in line_lower or 'at large' in line_lower:
                district = "At-Large"

            if district:
                # Next line should be the name
                name_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                # Validate it looks like a name (2+ words, starts with uppercase)
                if len(name_line.split()) >= 2 and name_line[0].isupper():
                    if not any(x in name_line.lower() for x in ['nonpartisan', 'democratic', 'republican', 'council', 'district']):
                        name = name_line

                        # Look for dates in next few lines
                        term_start = None
                        term_end = None
                        for j in range(i + 2, min(i + 6, len(lines))):
                            context_line = lines[j].strip()
                            # Look for assumed office date
                            date_match = re.search(r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d+,?\s*(\d{4})', context_line.lower())
                            if date_match and not term_start:
                                term_start = int(date_match.group(1))
                            # Look for standalone year (term end)
                            year_match = re.search(r'^(202[6-9])$', context_line.strip())
                            if year_match:
                                term_end = int(year_match.group(1))

                        if term_start or term_end:
                            if not term_start and term_end:
                                term_start = term_end - 4
                            members.append({
                                "name": name,
                                "district": district,
                                "term_start": term_start,
                                "term_end": term_end,
                            })
                            print(f"      Text parse found: {name} ({district})")
                            i += 5
                            continue
            i += 1

        # Also try the original pattern for different formats
        pattern = r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+).*?(?:assumed|took)\s+office.*?(\d{4}).*?term\s+ends?\s*:?\s*(\d{4})'

        for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
            name = match.group(1).strip()
            term_start = int(match.group(2))
            term_end = int(match.group(3))

            # Skip if already found
            if any(m['name'].lower() == name.lower() for m in members):
                continue

            # Try to find district in surrounding text
            context = text[max(0, match.start()-100):match.end()+50]
            district = None
            district_match = re.search(r'district\s*(\d+)', context, re.I)
            if district_match:
                district = f"District {district_match.group(1)}"
            elif "at-large" in context.lower() or "at large" in context.lower():
                district = "At-Large"

            members.append({
                "name": name,
                "district": district,
                "term_start": term_start,
                "term_end": term_end,
            })

        return members

    async def scrape_all_cities(self):
        """Scrape the 3 OC cities that Ballotpedia covers."""
        print("Scraping Ballotpedia for covered OC cities...")
        print("(Only 3 OC cities are in Ballotpedia's top-100 coverage)")
        print("=" * 60)

        for city_key, ballotpedia_slug in COVERED_CITIES.items():
            members = await self.scrape_city(city_key, ballotpedia_slug)
            if members:
                self.results[city_key] = {
                    "members": {self.normalize_name(m["name"]): {
                        "district": m.get("district"),
                        "term_start": m.get("term_start"),
                        "term_end": m.get("term_end"),
                    } for m in members},
                    "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    "source": f"https://ballotpedia.org/{ballotpedia_slug}",
                }

        return self.results

    def save_to_yaml(self, output_path):
        """Save results to YAML file."""
        output = {
            "metadata": {
                "description": "Council member term data from Ballotpedia",
                "generated": datetime.now().isoformat(),
                "source": "Ballotpedia.org",
                "cities_count": len(self.results),
            },
            "cities": self.results,
        }

        with open(output_path, "w") as f:
            yaml.dump(output, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        print(f"\nSaved to {output_path}")


async def main():
    """Main entry point."""
    output_path = Path(__file__).parent.parent / "config" / "known_terms.yaml"

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()

        scraper = BallotpediaScraper(page)
        await scraper.scrape_all_cities()
        scraper.save_to_yaml(output_path)

        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        total_members = sum(len(city.get("members", {})) for city in scraper.results.values())
        print(f"Cities scraped: {len(scraper.results)}")
        print(f"Total members: {total_members}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
