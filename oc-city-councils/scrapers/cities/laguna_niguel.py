"""
Laguna Niguel City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class LagunaNiguelScraper(BaseScraper):
    """Laguna Niguel - CivicPlus with individual profile pages."""

    CITY_NAME = "Laguna Niguel"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cityoflagunaniguel.org"
    BASE_URL = "https://www.cityoflagunaniguel.org"
    COUNCIL_URL = "https://www.cityoflagunaniguel.org/396/Mayor-City-Council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """Discover council members from the main council page."""
        members = []
        seen_urls = set()

        try:
            # Look for links to member profile pages
            links = await self.page.query_selector_all('a[href*="/"]')

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                href_lower = href.lower()

                # Skip non-member pages
                skip_patterns = ["mailto:", "#", "agenda", "minutes", "calendar", "meeting", "contact"]
                if any(skip in href_lower for skip in skip_patterns):
                    continue

                # Must contain member-related keywords
                if not re.search(r'(mayor|council-?member)', href_lower):
                    continue

                # Must not be the main council page
                if href_lower.endswith("/mayor-city-council") or "/396/" in href_lower:
                    continue

                full_url = urljoin(self.BASE_URL, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Extract name from link text
                name = text.strip()
                for prefix in ["Mayor Pro Tem", "Mayor", "Council Member", "Councilmember"]:
                    if name.lower().startswith(prefix.lower()):
                        name = name[len(prefix):].strip()

                if len(name) < 4:
                    continue

                # Determine position
                position = "Councilmember"
                if "mayor-pro-tem" in href_lower or "pro tem" in text.lower():
                    position = "Mayor Pro Tem"
                elif "mayor" in href_lower.split("/")[-1].split("-")[0] or text.lower().startswith("mayor"):
                    position = "Mayor"

                members.append({
                    "name": name,
                    "position": position,
                    "url": full_url,
                })
                print(f"      Found: {name} ({position})")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} members")

        for member in members:
            data = await self.scrape_member_page(
                member, self.BASE_URL, self.CITY_DOMAIN, main_phones
            )
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()
