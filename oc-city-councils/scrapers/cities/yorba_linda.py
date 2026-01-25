"""
Yorba Linda City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class YorbaLindaScraper(BaseScraper):
    """Yorba Linda - CivicPlus platform with dynamic member discovery."""

    CITY_NAME = "Yorba Linda"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "yorbalindaca.gov"
    BASE_URL = "https://www.yorbalindaca.gov"
    COUNCIL_URL = "https://www.yorbalindaca.gov/190/City-Council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """
        Discover council members from the main council page.
        CivicPlus pattern: links contain /XXX/Name-Title format
        """
        members = []
        seen_urls = set()

        try:
            links = await self.page.query_selector_all("a[href]")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                # Skip empty, mailto, or already seen
                if not href or href.startswith("mailto:") or href in seen_urls:
                    continue

                # CivicPlus member pages have numeric ID pattern: /123/Name
                if not re.search(r'/\d+/', href):
                    continue

                text_lower = text.lower()

                # Must contain a position keyword
                if not any(kw in text_lower for kw in ["mayor", "council"]):
                    continue

                # Skip generic links
                if any(skip in text_lower for skip in ["email all", "contact", "agendas", "meetings"]):
                    continue

                # Determine position
                if "mayor pro tem" in text_lower:
                    position = "Mayor Pro Tem"
                elif "mayor" in text_lower:
                    position = "Mayor"
                else:
                    position = "Councilmember"

                # Extract clean name - remove position prefixes
                name = text
                for prefix in ["Mayor Pro Tem", "Mayor Pro Tempore", "Vice Mayor",
                               "Mayor", "Councilmember", "Council Member"]:
                    name = re.sub(rf"^{prefix}\s*", "", name, flags=re.IGNORECASE)
                name = name.strip()

                # Remove trailing position (e.g., "John Smith, Mayor" -> "John Smith")
                name = re.sub(r',\s*(Mayor|Council\s*member|Vice\s*Mayor).*$', '', name, flags=re.IGNORECASE)
                name = name.strip()

                # Skip if name too short or looks wrong
                if len(name) < 4 or name.lower() in ["city council"]:
                    continue

                url = urljoin(self.BASE_URL, href)
                seen_urls.add(href)

                # Avoid duplicate names
                if not any(m["name"].lower() == name.lower() for m in members):
                    members.append({"name": name, "position": position, "url": url})
                    print(f"      Found: {name} ({position})")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        # Visit main council page
        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        # Discover members dynamically
        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} members")

        # Scrape each member
        for member in members:
            data = await self.scrape_member_page(
                member, self.BASE_URL, self.CITY_DOMAIN, main_phones
            )
            self.add_council_member(**data)

        # Final email matching pass
        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()
