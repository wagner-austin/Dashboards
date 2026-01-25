"""
Fullerton City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class FullertonScraper(BaseScraper):
    """Fullerton - CivicPlus with individual profile pages."""

    CITY_NAME = "Fullerton"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cityoffullerton.com"
    BASE_URL = "https://www.cityoffullerton.com"
    COUNCIL_URL = "https://www.cityoffullerton.com/government/city-council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """Discover council members from the main council page."""
        members = []
        seen_urls = set()

        try:
            links = await self.page.query_selector_all('a[href*="/city-council/"]')

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                href_lower = href.lower()

                # Skip non-member pages
                skip_patterns = ["mailto:", "#", "agendas", "minutes", "calendar", "contact"]
                if any(skip in href_lower for skip in skip_patterns):
                    continue

                # Must be a member page (mayor- or council-member-)
                if not re.search(r'/(mayor-|council-member-)[a-z]', href_lower):
                    continue

                full_url = urljoin(self.BASE_URL, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Clean up name - remove prefixes
                name = text.strip()
                for prefix in ["Mayor Pro Tem", "Mayor", "Council Member", "Councilmember", "Dr.", "Dr"]:
                    if name.startswith(prefix):
                        name = name[len(prefix):].strip()
                    name = name.lstrip(". ")

                if len(name) < 4:
                    continue

                # Determine position from link text
                position = "Councilmember"
                text_lower = text.lower()
                if "mayor pro tem" in text_lower:
                    position = "Mayor Pro Tem"
                elif "mayor" in text_lower:
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
