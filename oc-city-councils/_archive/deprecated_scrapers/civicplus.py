"""
CivicPlus platform scraper - used by many OC cities.

Dynamically discovers council members from the main council page.
No hardcoded member lists - automatically adapts to council changes.
"""
import re
from urllib.parse import urljoin
from .base import BaseScraper


class CivicPlusScraper(BaseScraper):
    """
    Base scraper for CivicPlus-based city websites.

    AUTOMATICALLY discovers council members from the main page.
    No hardcoded MEMBERS list needed.

    Subclasses only need to define:
    - CITY_NAME, CITY_DOMAIN, BASE_URL, COUNCIL_URL
    """

    PLATFORM = "civicplus"
    CITY_NAME = "Unknown"
    CITY_DOMAIN = None
    BASE_URL = None
    COUNCIL_URL = None

    # Position keywords to identify council member links
    POSITION_KEYWORDS = ["mayor", "councilmember", "council member", "vice mayor", "mayor pro tem"]

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """
        Dynamically discover council members from the main council page.
        Returns list of dicts with name, position, url.
        """
        members = []

        try:
            # Find all links on the page
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href")
                text = (await link.inner_text()).strip()

                if not href or not text:
                    continue

                text_lower = text.lower()

                # Check if link text contains position keywords
                position = None
                for keyword in self.POSITION_KEYWORDS:
                    if keyword in text_lower:
                        # Determine position from text
                        if "mayor pro tem" in text_lower:
                            position = "Mayor Pro Tem"
                        elif "vice mayor" in text_lower:
                            position = "Vice Mayor"
                        elif "mayor" in text_lower and "pro tem" not in text_lower:
                            position = "Mayor"
                        else:
                            position = "Councilmember"
                        break

                if position:
                    # Extract name from text (remove position prefix)
                    name = text
                    for keyword in ["Mayor Pro Tem", "Vice Mayor", "Mayor", "Councilmember", "Council Member"]:
                        name = re.sub(rf"^{keyword}\s*", "", name, flags=re.IGNORECASE).strip()

                    # Skip if name looks like a generic link or contains city name
                    if len(name) < 3 or name.lower() in ["contact", "email", "more", "city council"]:
                        continue

                    # Skip if name still contains position keywords (bad parse)
                    if any(kw in name.lower() for kw in ["mayor", "council"]):
                        continue

                    # Make URL absolute
                    url = urljoin(self.BASE_URL, href)

                    # Avoid duplicates by name OR url
                    if not any(m["name"] == name or m["url"] == url for m in members):
                        members.append({
                            "name": name,
                            "position": position,
                            "url": url
                        })
                        print(f"      Found: {position} {name}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        # Visit main council page
        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        # Dynamically discover members
        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    WARNING: No council members found!")
            self.results["errors"].append("No council members discovered")
            return self.get_results()

        print(f"    Found {len(members)} council members")

        # Scrape each member's page
        for member in members:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


# === CITY SCRAPERS ===
# Only config needed - members discovered automatically

class AlisoViejoScraper(CivicPlusScraper):
    """Aliso Viejo - CivicPlus."""
    CITY_NAME = "Aliso Viejo"
    CITY_DOMAIN = "avcity.org"
    BASE_URL = "https://avcity.org"
    COUNCIL_URL = "https://avcity.org/222/City-Council"


class AnaheimScraper(CivicPlusScraper):
    """Anaheim - CivicPlus."""
    CITY_NAME = "Anaheim"
    CITY_DOMAIN = "anaheim.net"
    BASE_URL = "https://www.anaheim.net"
    COUNCIL_URL = "https://www.anaheim.net/173/City-Council"


class BreaScraper(CivicPlusScraper):
    """Brea - CivicPlus with directory pages."""
    CITY_NAME = "Brea"
    CITY_DOMAIN = "cityofbrea.gov"
    BASE_URL = "https://www.cityofbrea.gov"
    COUNCIL_URL = "https://www.cityofbrea.gov/511/City-Council"


class LaHabraScraper(CivicPlusScraper):
    """La Habra - CivicPlus."""
    CITY_NAME = "La Habra"
    CITY_DOMAIN = "lahabraca.gov"
    BASE_URL = "https://www.lahabraca.gov"
    COUNCIL_URL = "https://www.lahabraca.gov/153/City-Council"


class LaPalmaScraper(CivicPlusScraper):
    """La Palma - CivicPlus."""
    CITY_NAME = "La Palma"
    CITY_DOMAIN = "lapalmaca.gov"
    BASE_URL = "https://www.lapalmaca.gov"
    COUNCIL_URL = "https://www.lapalmaca.gov/66/City-Council"


class LagunaHillsScraper(CivicPlusScraper):
    """Laguna Hills - CivicPlus."""
    CITY_NAME = "Laguna Hills"
    CITY_DOMAIN = "lagunahillsca.gov"
    BASE_URL = "https://www.lagunahillsca.gov"
    COUNCIL_URL = "https://www.lagunahillsca.gov/129/City-Council"


class LagunaWoodsScraper(CivicPlusScraper):
    """Laguna Woods - WordPress-style site."""
    CITY_NAME = "Laguna Woods"
    PLATFORM = "wordpress"
    CITY_DOMAIN = "cityoflagunawoods.org"
    BASE_URL = "https://www.cityoflagunawoods.org"
    COUNCIL_URL = "https://www.cityoflagunawoods.org/city-council/"


class YorbaLindaScraper(CivicPlusScraper):
    """Yorba Linda - CivicPlus."""
    CITY_NAME = "Yorba Linda"
    CITY_DOMAIN = "yorbalindaca.gov"
    BASE_URL = "https://www.yorbalindaca.gov"
    COUNCIL_URL = "https://www.yorbalindaca.gov/190/City-Council"
