"""
Custom scrapers for cities with unique website structures.
"""
from .base import BaseScraper


class OrangeScraper(BaseScraper):
    """
    City of Orange scraper.

    Uses a custom CMS. Council page lists members but emails are on individual pages.
    Website sometimes blocks automated requests (403).
    """

    CITY_NAME = "Orange"
    PLATFORM = "custom_cms"

    COUNCIL_URL = "https://www.cityoforange.org/our-city/local-government/city-council"

    MEMBERS = [
        {"name": "Dan Slater", "position": "Mayor", "district": "At-Large",
         "url": "https://www.cityoforange.org/our-city/local-government/city-council/mayor-dan-slater"},
        {"name": "Denis Bilodeau", "position": "Mayor Pro Tem", "district": "District 4",
         "url": "https://www.cityoforange.org/our-city/local-government/city-council/mayor-pro-tem-denis-bilodeau"},
        {"name": "Arianna Barrios", "position": "Councilmember", "district": "District 1",
         "url": "https://www.cityoforange.org/our-city/local-government/city-council/council-member-arianna-barrios"},
        {"name": "Jon Dumitru", "position": "Councilmember", "district": "District 2",
         "url": "https://www.cityoforange.org/our-city/local-government/city-council/council-member-jon-dumitru"},
        {"name": "Kathy Tavoularis", "position": "Councilmember", "district": "District 3",
         "url": "https://www.cityoforange.org/our-city/local-government/city-council/council-member-kathy-tavoularis"},
        {"name": "Ana Gutierrez", "position": "Councilmember", "district": "District 5",
         "url": "https://www.cityoforange.org/our-city/local-government/city-council/council-member-ana-gutierrez"},
        {"name": "John Gyllenhammer", "position": "Councilmember", "district": "District 6",
         "url": "https://www.cityoforange.org/our-city/local-government/city-council/council-member-john-gyllenhammer"},
    ]

    def get_urls(self):
        urls = {"council": self.COUNCIL_URL}
        for m in self.MEMBERS:
            urls[m["name"]] = m["url"]
        return urls

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        # Try main council page first - this often has all emails
        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        # Visit each member page (may fail with 403)
        for member in self.MEMBERS:
            result = await self.visit_page(member["url"], f"member_{member['name']}")

            member_email = None
            member_phone = None

            # Look for email from individual page
            if result.get("status") == "success" and result.get("emails"):
                # Prefer city domain emails
                for email in result["emails"]:
                    if "@cityoforange.org" in email.lower():
                        member_email = email
                        break
                # If no city email, use any email found (could be personal)
                if not member_email and len(result["emails"]) == 1:
                    member_email = result["emails"][0]

            if result.get("phones"):
                member_phone = result["phones"][0]
            elif main_phones:
                member_phone = main_phones[0]  # Use main page phone as fallback

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                email=member_email,
                phone=member_phone,
                district=member["district"],
                profile_url=member["url"]
            )

        # Match emails from main page to members who don't have emails yet
        self.match_emails_to_members(city_domain="cityoforange.org")

        return self.get_results()


class LagunaBeachScraper(BaseScraper):
    """
    Laguna Beach scraper.

    Uses Granicus/custom platform. Has a contact council page but
    individual emails might not be public.
    """

    CITY_NAME = "Laguna Beach"
    PLATFORM = "granicus"

    URLS = {
        "council": "https://www.lagunabeachcity.net/live-here/city-council",
        "contact": "https://www.lagunabeachcity.net/government/departments/city-council/contact-city-council",
        "directory": "https://www.lagunabeachcity.net/government/departments/city-council"
    }

    MEMBERS = [
        {"name": "Alex Rounaghi", "position": "Mayor"},
        {"name": "Mark Orgill", "position": "Mayor Pro Tem"},
        {"name": "Bob Whalen", "position": "Councilmember"},
        {"name": "Sue Kempf", "position": "Councilmember"},
        {"name": "Hallie Jones", "position": "Councilmember"}
    ]

    def get_urls(self):
        return self.URLS

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        # Visit all known pages first to collect emails
        main_phones = []
        for page_type, url in self.URLS.items():
            result = await self.visit_page(url, page_type)
            if result.get("phones") and not main_phones:
                main_phones = result["phones"]

        # Try individual member pages
        base = "https://www.lagunabeachcity.net/government/departments/city-council"
        for member in self.MEMBERS:
            slug = member["name"].lower().replace(" ", "-")
            member_url = f"{base}/{slug}"
            result = await self.visit_page(member_url, f"member_{member['name']}")

            member_email = None
            for email in result.get("emails", []):
                if "@lagunabeachcity.net" in email.lower():
                    member_email = email
                    break

            member_phone = None
            if result.get("phones"):
                member_phone = result["phones"][0]
            elif main_phones:
                member_phone = main_phones[0]

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                email=member_email,
                phone=member_phone,
                profile_url=member_url if result["status"] == "success" else None
            )

        # Match emails from main pages to members who don't have emails yet
        self.match_emails_to_members(city_domain="lagunabeachcity.net")

        return self.get_results()


class MissionViejoScraper(BaseScraper):
    """
    Mission Viejo scraper.

    Uses shared council email - check if individual emails exist.
    """

    CITY_NAME = "Mission Viejo"
    PLATFORM = "custom"

    COUNCIL_URL = "https://www.cityofmissionviejo.org/government/city-council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        # Visit council page
        result = await self.visit_page(self.COUNCIL_URL, "council_main")

        # Try directory
        await self.visit_page(
            "https://www.cityofmissionviejo.org/contacts",
            "contacts"
        )

        return self.get_results()


class TustinScraper(BaseScraper):
    """
    Tustin scraper - CivicPlus but only has shared email.
    """

    CITY_NAME = "Tustin"
    PLATFORM = "civicplus"

    def get_urls(self):
        return {
            "council": "https://www.tustinca.org/168/City-Council",
            "directory": "https://www.tustinca.org/Directory.aspx?did=12"
        }

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        for page_type, url in self.get_urls().items():
            await self.visit_page(url, page_type)

        return self.get_results()
