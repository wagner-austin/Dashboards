"""
CivicPlus platform scraper - used by many OC cities.
Cities: Aliso Viejo, Brea, La Habra, La Palma, Laguna Hills, etc.
"""
from .base import BaseScraper


class CivicPlusScraper(BaseScraper):
    """
    Scraper for CivicPlus-based city websites.

    CivicPlus sites typically have:
    - Council page at /XXX/City-Council
    - Directory at /Directory.aspx?did=XX
    - Individual member pages at /XXX/Member-Name
    - Emails often in mailto: links or "Email" buttons
    """

    PLATFORM = "civicplus"
    MEMBERS = []  # Override in subclass with council member definitions
    CITY_DOMAIN = None  # e.g., "avcity.org" - for email matching

    def __init__(self, page, city_name, council_url, directory_url=None, member_pages=None):
        self.CITY_NAME = city_name
        super().__init__(page)
        self.council_url = council_url
        self.directory_url = directory_url
        self.member_pages = member_pages or []

    def get_urls(self):
        urls = {"council": self.council_url}
        if self.directory_url:
            urls["directory"] = self.directory_url
        for i, url in enumerate(self.member_pages):
            urls[f"member_{i}"] = url
        return urls

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        # 1. Main council page
        main_result = await self.visit_page(self.council_url, "council_main")
        main_phones = main_result.get("phones", [])

        # 2. Directory page (often has emails)
        if self.directory_url:
            await self.visit_page(self.directory_url, "directory")

        # 3. Individual member pages
        for url in self.member_pages:
            await self.visit_page(url, "member_page")

        # 4. Try to discover member pages from council page
        await self.discover_member_pages()

        # 5. Add council members if defined
        if self.MEMBERS:
            for member in self.MEMBERS:
                self.add_council_member(
                    name=member.get("name"),
                    position=member.get("position"),
                    email=None,
                    phone=main_phones[0] if main_phones else None,
                    district=member.get("district"),
                    profile_url=member.get("url")
                )
            # Match emails to members
            if self.CITY_DOMAIN:
                self.match_emails_to_members(city_domain=self.CITY_DOMAIN)

        return self.get_results()

    async def discover_member_pages(self):
        """Try to find member page links from council page"""
        try:
            # Go back to council page
            await self.page.goto(self.council_url, timeout=20000)
            await self.page.wait_for_timeout(1000)

            # Look for links containing member-related keywords
            selectors = [
                'a[href*="Mayor"]',
                'a[href*="Council"][href*="member" i]',
                'a[href*="Pro-Tem"]',
                'a[href*="Councilmember"]'
            ]

            found_urls = set()
            for selector in selectors:
                try:
                    links = await self.page.query_selector_all(selector)
                    for link in links:
                        href = await link.get_attribute('href')
                        if href:
                            # Make absolute
                            if href.startswith('/'):
                                from urllib.parse import urljoin
                                href = urljoin(self.council_url, href)
                            # Skip if already visited
                            visited = [p["url"] for p in self.results["pages_visited"]]
                            if href not in visited and href not in found_urls:
                                found_urls.add(href)
                except:
                    pass

            # Visit discovered pages
            for url in list(found_urls)[:10]:  # Limit to 10
                await self.visit_page(url, "discovered_member")

        except Exception as e:
            self.results["errors"].append(f"discover_member_pages: {str(e)}")


# Pre-configured scrapers for specific CivicPlus cities
class AlisoViejoScraper(CivicPlusScraper):
    CITY_DOMAIN = "avcity.org"
    MEMBERS = [
        {"name": "Max Duncan", "position": "Mayor", "url": "https://avcity.org/294/Mayor-Max-Duncan"},
        {"name": "Mike Munzing", "position": "Mayor Pro Tem", "url": "https://avcity.org/292/Mayor-Pro-Tem-Mike-Munzing"},
        {"name": "Tiffany Ackley", "position": "Councilmember", "url": "https://avcity.org/293/Councilmember-Tiffany-Ackley"},
        {"name": "Garrett Dwyer", "position": "Councilmember", "url": "https://avcity.org/295/Councilmember-Garrett-Dwyer"},
        {"name": "Tim Zandbergen", "position": "Councilmember", "url": "https://avcity.org/291/Councilmember-Tim-Zandbergen"},
    ]

    def __init__(self, page):
        super().__init__(
            page,
            city_name="Aliso Viejo",
            council_url="https://avcity.org/222/City-Council",
            directory_url="https://avcity.org/Directory.aspx?did=1",
            member_pages=[
                "https://avcity.org/294/Mayor-Max-Duncan",
                "https://avcity.org/292/Mayor-Pro-Tem-Mike-Munzing",
                "https://avcity.org/293/Councilmember-Tiffany-Ackley",
                "https://avcity.org/295/Councilmember-Garrett-Dwyer",
                "https://avcity.org/291/Councilmember-Tim-Zandbergen"
            ]
        )


class LaHabraScraper(CivicPlusScraper):
    CITY_DOMAIN = "lahabraca.gov"
    MEMBERS = [
        {"name": "Jose Medrano", "position": "Mayor"},
        {"name": "James Gomez", "position": "Mayor Pro Tem"},
        {"name": "Rose Espinoza", "position": "Councilmember"},
        {"name": "Daren Nigsarian", "position": "Councilmember"},
        {"name": "Delwin Lampkin", "position": "Councilmember"},
    ]

    def __init__(self, page):
        super().__init__(
            page,
            city_name="La Habra",
            council_url="https://www.lahabraca.gov/153/City-Council",
            directory_url="https://www.lahabraca.gov/Directory.aspx?did=7"
        )


class LaPalmaScraper(CivicPlusScraper):
    CITY_DOMAIN = "lapalmaca.gov"
    MEMBERS = [
        {"name": "Nitesh Patel", "position": "Mayor"},
        {"name": "Debbie Baker", "position": "Mayor Pro Tem"},
        {"name": "Mark Waldman", "position": "Councilmember"},
        {"name": "Vikesh Patel", "position": "Councilmember"},
        {"name": "Janet Keo Conklin", "position": "Councilmember"},
    ]

    def __init__(self, page):
        super().__init__(
            page,
            city_name="La Palma",
            council_url="https://www.lapalmaca.gov/66/City-Council",
            directory_url="https://www.lapalmaca.gov/Directory.aspx?did=3"
        )


class LagunaHillsScraper(CivicPlusScraper):
    CITY_DOMAIN = "lagunahillsca.gov"
    MEMBERS = [
        {"name": "Don Caskey", "position": "Mayor", "url": "https://www.lagunahillsca.gov/527/Don-Caskey-Mayor"},
        {"name": "Jared Mathis", "position": "Mayor Pro Tem", "url": "https://www.lagunahillsca.gov/447/Jared-Mathis-Mayor-Pro-Tempore"},
        {"name": "Erica Pezold", "position": "Councilmember", "url": "https://www.lagunahillsca.gov/475/Erica-Pezold"},
        {"name": "Joshua Sweeney", "position": "Councilmember", "url": "https://www.lagunahillsca.gov/234/Joshua-Sweeney"},
        {"name": "Dave Wheeler", "position": "Councilmember", "url": "https://www.lagunahillsca.gov/476/Dave-Wheeler"},
    ]

    def __init__(self, page):
        super().__init__(
            page,
            city_name="Laguna Hills",
            council_url="https://www.lagunahillsca.gov/129/City-Council",
            directory_url="https://www.lagunahillsca.gov/Directory.aspx?did=1",
            member_pages=[
                "https://www.lagunahillsca.gov/527/Don-Caskey-Mayor",
                "https://www.lagunahillsca.gov/447/Jared-Mathis-Mayor-Pro-Tempore",
                "https://www.lagunahillsca.gov/475/Erica-Pezold",
                "https://www.lagunahillsca.gov/234/Joshua-Sweeney",
                "https://www.lagunahillsca.gov/476/Dave-Wheeler"
            ]
        )


class LagunaWoodsScraper(CivicPlusScraper):
    """Laguna Woods uses WordPress but similar structure"""
    def __init__(self, page):
        super().__init__(
            page,
            city_name="Laguna Woods",
            council_url="https://www.cityoflagunawoods.org/city-council/",
            directory_url=None
        )
        self.PLATFORM = "wordpress"


class BreaScraper(CivicPlusScraper):
    CITY_DOMAIN = "cityofbrea.gov"
    MEMBERS = [
        {"name": "Christine Marick", "position": "Mayor"},
        {"name": "Cecilia Hupp", "position": "Mayor Pro Tem"},
        {"name": "Steven Vargas", "position": "Councilmember"},
        {"name": "Marty Simonoff", "position": "Councilmember"},
        {"name": "Glenn Parker", "position": "Councilmember"},
    ]

    def __init__(self, page):
        super().__init__(
            page,
            city_name="Brea",
            council_url="https://www.cityofbrea.gov/511/City-Council",
            directory_url="https://www.cityofbrea.gov/Directory.aspx?did=2"
        )
