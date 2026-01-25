"""
Irvine City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class IrvineScraper(BaseScraper):
    """Irvine - Custom CMS with individual profile pages."""

    CITY_NAME = "Irvine"
    PLATFORM = "custom"
    CITY_DOMAIN = "cityofirvine.org"
    BASE_URL = "https://www.cityofirvine.org"
    COUNCIL_URL = "https://www.cityofirvine.org/city-council"

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
                if href_lower.endswith("/city-council") or href_lower.endswith("/city-council/"):
                    continue
                skip_patterns = ["mailto:", "#", "agenda", "minutes", "calendar", "meeting", "contact"]
                if any(skip in href_lower for skip in skip_patterns):
                    continue

                # Must be a member page (mayor, vice-mayor, councilmember)
                if not re.search(r'/city-council/(mayor|vice-mayor|councilmember)', href_lower):
                    continue

                full_url = urljoin(self.BASE_URL, href)
                # Normalize URL (ensure www. prefix for deduplication)
                normalized_url = full_url.replace("://cityofirvine.org", "://www.cityofirvine.org")
                if normalized_url in seen_urls:
                    continue
                seen_urls.add(normalized_url)
                full_url = normalized_url

                # Extract name - clean up prefixes
                name = text.strip()
                for prefix in ["Vice Mayor", "Mayor", "Council Member", "Councilmember"]:
                    if name.lower().startswith(prefix.lower()):
                        name = name[len(prefix):].strip()

                if len(name) < 4:
                    continue

                # Determine position from URL/text
                position = "Councilmember"
                if "vice-mayor" in href_lower or "vice mayor" in text.lower():
                    position = "Vice Mayor"
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
