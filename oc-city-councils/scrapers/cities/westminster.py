"""
Westminster City Council Scraper
Uses stealth mode - site blocks bots.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class WestminsterScraper(BaseScraper):
    """Westminster - Granicus platform, requires Firefox stealth mode."""

    CITY_NAME = "Westminster"
    PLATFORM = "granicus"
    CITY_DOMAIN = "westminster-ca.gov"
    BASE_URL = "https://www.westminster-ca.gov"
    COUNCIL_URL = "https://www.westminster-ca.gov/government/mayor-and-city-council-members"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """
        Discover council members from the main page.
        Westminster pattern: URLs contain mayor- or council-member- prefix.
        """
        members = []
        seen_names = set()

        try:
            links = await self.page.query_selector_all("a[href]")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text:
                    continue

                # Clean href - remove fragments and tracking params
                clean_href = href.split("#")[0].split("?")[0].rstrip("/")

                # Westminster member pages have specific patterns in URL
                href_lower = clean_href.lower()
                if not any(pattern in href_lower for pattern in
                          ["mayor-chi", "council-member-", "vice-mayor-"]):
                    continue

                # Skip non-member pages by URL pattern
                if any(skip in href_lower for skip in
                      ["code-of-ethics", "videos", "agendas", "minutes", "meetings"]):
                    continue

                # Determine position from URL (be specific to avoid false matches)
                if "/mayor-chi" in href_lower:
                    position = "Mayor"
                elif "/vice-mayor-" in href_lower:
                    position = "Vice Mayor"
                elif "/council-member-" in href_lower:
                    position = "Councilmember"
                else:
                    position = "Councilmember"

                # Extract name - clean up thoroughly
                name = text
                for prefix in ["Mayor", "Vice Mayor", "Council Member", "Councilmember"]:
                    name = re.sub(rf"^{prefix}\s*", "", name, flags=re.IGNORECASE)
                name = re.sub(r'\s*[-,]?\s*District\s*\d*', '', name, flags=re.IGNORECASE)
                name = re.sub(r',+$', '', name)  # Remove trailing commas
                name = name.strip()

                if len(name) < 3:
                    continue

                # Normalize for duplicate check
                name_key = name.lower().replace(",", "").strip()
                if name_key in seen_names:
                    continue
                seen_names.add(name_key)

                url = urljoin(self.BASE_URL, clean_href)
                members.append({"name": name, "position": position, "url": url})
                print(f"      Found: {name} ({position})")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")
        print("    NOTE: Use --stealth --browser firefox if getting blocked")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found! Try stealth mode.")
            return self.get_results()

        print(f"    Found {len(members)} members")

        for member in members:
            data = await self.scrape_member_page(
                member, self.BASE_URL, self.CITY_DOMAIN, main_phones
            )
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()
