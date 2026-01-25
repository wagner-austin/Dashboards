"""
Custom scrapers for cities with unique website structures.

All scrapers use BaseScraper.scrape_member_page() for consistent rich data extraction.
"""
from .base import BaseScraper


class OrangeScraper(BaseScraper):
    """City of Orange - custom CMS, sometimes blocks (403)."""

    CITY_NAME = "Orange"
    PLATFORM = "custom_cms"
    CITY_DOMAIN = "cityoforange.org"
    BASE_URL = "https://www.cityoforange.org"
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
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class LagunaBeachScraper(BaseScraper):
    """Laguna Beach - Granicus platform."""

    CITY_NAME = "Laguna Beach"
    PLATFORM = "granicus"
    CITY_DOMAIN = "lagunabeachcity.net"
    BASE_URL = "https://www.lagunabeachcity.net"
    COUNCIL_URL = "https://www.lagunabeachcity.net/government/departments/city-council"

    MEMBERS = [
        {"name": "Alex Rounaghi", "position": "Mayor",
         "url": "https://www.lagunabeachcity.net/government/departments/city-council/alex-rounaghi"},
        {"name": "Mark Orgill", "position": "Mayor Pro Tem",
         "url": "https://www.lagunabeachcity.net/government/departments/city-council/mark-orgill"},
        {"name": "Bob Whalen", "position": "Councilmember",
         "url": "https://www.lagunabeachcity.net/government/departments/city-council/bob-whalen"},
        {"name": "Sue Kempf", "position": "Councilmember",
         "url": "https://www.lagunabeachcity.net/government/departments/city-council/sue-kempf"},
        {"name": "Hallie Jones", "position": "Councilmember",
         "url": "https://www.lagunabeachcity.net/government/departments/city-council/hallie-jones"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class MissionViejoScraper(BaseScraper):
    """Mission Viejo - uses shared council email."""

    CITY_NAME = "Mission Viejo"
    PLATFORM = "custom"
    CITY_DOMAIN = "cityofmissionviejo.org"
    BASE_URL = "https://www.cityofmissionviejo.org"
    COUNCIL_URL = "https://www.cityofmissionviejo.org/government/city-council"

    MEMBERS = [
        {"name": "Ed Sachs", "position": "Mayor",
         "url": "https://www.cityofmissionviejo.org/government/city-council/mayor-ed-sachs"},
        {"name": "Wendy Bucknum", "position": "Mayor Pro Tem",
         "url": "https://www.cityofmissionviejo.org/government/city-council/mayor-pro-tem-wendy-bucknum"},
        {"name": "Greg Raths", "position": "Councilmember",
         "url": "https://www.cityofmissionviejo.org/government/city-council/council-member-greg-raths"},
        {"name": "Trish Kelley", "position": "Councilmember",
         "url": "https://www.cityofmissionviejo.org/government/city-council/council-member-trish-kelley"},
        {"name": "Brian Goodell", "position": "Councilmember",
         "url": "https://www.cityofmissionviejo.org/government/city-council/council-member-brian-goodell"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class TustinScraper(BaseScraper):
    """Tustin - CivicPlus with individual member pages."""

    CITY_NAME = "Tustin"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "tustinca.org"
    BASE_URL = "https://www.tustinca.org"
    COUNCIL_URL = "https://www.tustinca.org/482/City-Council"

    MEMBERS = [
        {"name": "Austin Lumbard", "position": "Mayor",
         "url": "https://www.tustinca.org/499/Mayor-Austin-Lumbard"},
        {"name": "Ray Schnell", "position": "Mayor Pro Tem",
         "url": "https://www.tustinca.org/1396/Council-Member-Ray-Schnell"},
        {"name": "Ryan Gallagher", "position": "Councilmember",
         "url": "https://www.tustinca.org/1207/Council-Member-Ryan-Gallagher"},
        {"name": "Lee K. Fink", "position": "Councilmember",
         "url": "https://www.tustinca.org/1208/Council-Member-Lee-K-Fink"},
        {"name": "John Nielsen", "position": "Councilmember",
         "url": "https://www.tustinca.org/493/Council-Member-John-Nielsen"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class VillaParkScraper(BaseScraper):
    """Villa Park - WordPress-style with bio pages."""

    CITY_NAME = "Villa Park"
    PLATFORM = "wordpress"
    CITY_DOMAIN = "villapark.org"
    BASE_URL = "https://villapark.org"
    COUNCIL_URL = "https://villapark.org/council-and-committees/city-council"

    MEMBERS = [
        {"name": "Jordan Wu", "position": "Mayor",
         "url": "https://villapark.org/Council-and-Committees/City-Council/Jordan-Wu-Bio"},
        {"name": "Robert Frackelton", "position": "Mayor Pro Tem",
         "url": "https://villapark.org/Council-and-Committees/City-Council/Robert-Frackelton-Bio"},
        {"name": "Nicol Jones", "position": "Councilmember",
         "url": "https://villapark.org/Council-and-Committees/City-Council/Nicol-Jones-Bio"},
        {"name": "Kelly McBride", "position": "Councilmember",
         "url": "https://villapark.org/Council-and-Committees/City-Council/Kelly-McBride-Bio"},
        {"name": "Crystal Miles", "position": "Councilmember",
         "url": "https://villapark.org/Council-and-Committees/City-Council/Crystal-Miles-Bio"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class SealBeachScraper(BaseScraper):
    """Seal Beach - CivicPlus, no individual profile pages."""

    CITY_NAME = "Seal Beach"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "sealbeachca.gov"
    BASE_URL = "https://www.sealbeachca.gov"
    COUNCIL_URL = "https://www.sealbeachca.gov/Government/City-Council"

    MEMBERS = [
        {"name": "Lisa Landau", "position": "Mayor", "district": "District 3", "term_end": 2026},
        {"name": "Nathan Steele", "position": "Mayor Pro Tem", "district": "District 5", "term_end": 2026},
        {"name": "Joe Kalmick", "position": "Councilmember", "district": "District 1", "term_end": 2026},
        {"name": "Ben Wong", "position": "Councilmember", "district": "District 2", "term_end": 2028},
        {"name": "Patty Senecal", "position": "Councilmember", "district": "District 4", "term_end": 2028},
    ]

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            self.add_council_member(
                name=member["name"],
                position=member["position"],
                district=member.get("district"),
                phone=main_phones[0] if main_phones else None,
                term_end=member.get("term_end"),
            )

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class StantonScraper(BaseScraper):
    """Stanton - PHP website with individual bio pages."""

    CITY_NAME = "Stanton"
    PLATFORM = "custom"
    CITY_DOMAIN = "stantonca.gov"
    BASE_URL = "https://www.stantonca.gov"
    COUNCIL_URL = "https://www.stantonca.gov/government/city_council.php"

    MEMBERS = [
        {"name": "David J. Shawver", "position": "Mayor", "district": "At-Large",
         "url": "https://www.stantonca.gov/government/bio-dshawver.php"},
        {"name": "Gary Taylor", "position": "Mayor Pro Tem", "district": "District 3",
         "url": "https://www.stantonca.gov/government/bio-gtaylor.php"},
        {"name": "Donald Torres", "position": "Councilmember", "district": "District 1",
         "url": None},  # Bio coming soon
        {"name": "Victor Barrios", "position": "Councilmember", "district": "District 2",
         "url": "https://www.stantonca.gov/government/bio_for_victor_barrios.php"},
        {"name": "John D. Warren", "position": "Councilmember", "district": "District 4",
         "url": "https://www.stantonca.gov/government/bio_for_john_d_warren.php"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS if m["url"]}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class WestminsterScraper(BaseScraper):
    """Westminster - blocks requests, use --stealth --browser firefox."""

    CITY_NAME = "Westminster"
    PLATFORM = "custom"
    CITY_DOMAIN = "westminster-ca.gov"
    BASE_URL = "https://www.westminster-ca.gov"
    COUNCIL_URL = "https://www.westminster-ca.gov/government/mayor-and-city-council-members"

    MEMBERS = [
        {"name": "Chi Charlie Nguyen", "position": "Mayor", "district": "At-Large",
         "url": "https://www.westminster-ca.gov/government/mayor-and-city-council-members/mayor-chi-charlie-nguyen"},
        {"name": "Carlos Manzo", "position": "Vice Mayor", "district": "District 2",
         "url": "https://www.westminster-ca.gov/government/mayor-and-city-council-members/council-member-carlos-manzo-district-2"},
        {"name": "Amy Phan West", "position": "Councilmember", "district": "District 1",
         "url": "https://www.westminster-ca.gov/government/mayor-and-city-council-members/council-member-amy-phan-west-district-1"},
        {"name": "Mark Nguyen", "position": "Councilmember", "district": "District 3",
         "url": "https://www.westminster-ca.gov/government/mayor-and-city-council-members/council-member-mark-nguyen-district-3"},
        {"name": "NamQuan Nguyen", "position": "Councilmember", "district": "District 4",
         "url": "https://www.westminster-ca.gov/government/mayor-and-city-council-members/council-member-namquan-nguyen-district-4"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class NewportBeachScraper(BaseScraper):
    """Newport Beach - Granicus with district profile pages."""

    CITY_NAME = "Newport Beach"
    PLATFORM = "granicus"
    CITY_DOMAIN = "newportbeachca.gov"
    BASE_URL = "https://www.newportbeachca.gov"
    COUNCIL_URL = "https://www.newportbeachca.gov/government/city-council"

    MEMBERS = [
        {"name": "Joe Stapleton", "position": "Mayor", "district": "District 1",
         "url": "https://www.newportbeachca.gov/government/city-council/find-your-council-district/district-1"},
        {"name": "Noah Blom", "position": "Mayor Pro Tem", "district": "District 5",
         "url": "https://www.newportbeachca.gov/government/city-council/find-your-council-district/district-5"},
        {"name": "Michelle Barto", "position": "Councilmember", "district": "District 2",
         "url": "https://www.newportbeachca.gov/government/city-council/find-your-council-district/district-2"},
        {"name": "Erik Weigand", "position": "Councilmember", "district": "District 3",
         "url": "https://www.newportbeachca.gov/government/city-council/find-your-council-district/district-3"},
        {"name": "Robyn Grant", "position": "Councilmember", "district": "District 4",
         "url": "https://www.newportbeachca.gov/government/city-council/find-your-council-district/district-4"},
        {"name": "Lauren Kleiman", "position": "Councilmember", "district": "District 6",
         "url": "https://www.newportbeachca.gov/government/city-council/find-your-council-district/district-6"},
        {"name": "Sara J. Weber", "position": "Councilmember", "district": "District 7",
         "url": "https://www.newportbeachca.gov/government/city-council/find-your-council-district/district-7"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class PlacentiaScraper(BaseScraper):
    """Placentia - CivicPlus with individual profile pages."""

    CITY_NAME = "Placentia"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "placentia.org"
    BASE_URL = "https://www.placentia.org"
    COUNCIL_URL = "https://www.placentia.org/268/Mayor-City-Council"

    MEMBERS = [
        {"name": "Chad P. Wanke", "position": "Mayor", "district": "District 4",
         "url": "https://www.placentia.org/448/Mayor-Chad-P-Wanke-District-4"},
        {"name": "Jeremy B. Yamaguchi", "position": "Mayor Pro Tem", "district": "District 3",
         "url": "https://www.placentia.org/353/Mayor-Pro-Tem-Jeremy-B-Yamaguchi-District-3"},
        {"name": "Thomas Hummer", "position": "Councilmember", "district": "District 1",
         "url": "https://www.placentia.org/721/Councilmember-Thomas-Hummer-District-1"},
        {"name": "Kevin Kirwin", "position": "Councilmember", "district": "District 2",
         "url": "https://www.placentia.org/674/Councilmember-Kevin-Kirwin-District-2"},
        {"name": "Ward L. Smith", "position": "Councilmember", "district": "District 5",
         "url": "https://www.placentia.org/720/Councilmember-Ward-L-Smith-District-5"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class RanchoSantaMargaritaScraper(BaseScraper):
    """Rancho Santa Margarita - CivicPlus with directory pages."""

    CITY_NAME = "Rancho Santa Margarita"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cityofrsm.org"
    BASE_URL = "https://www.cityofrsm.org"
    COUNCIL_URL = "https://www.cityofrsm.org/160/Mayor-City-Council"

    MEMBERS = [
        {"name": "L. Anthony Beall", "position": "Mayor",
         "url": "https://www.cityofrsm.org/Directory.aspx?EID=9"},
        {"name": "Anne D. Figueroa", "position": "Mayor Pro Tem",
         "url": "https://www.cityofrsm.org/Directory.aspx?EID=44"},
        {"name": "Keri Lynn Baert", "position": "Councilmember", "district": "District 3",
         "url": "https://www.cityofrsm.org/Directory.aspx?EID=70"},
        {"name": "Jerry Holloway", "position": "Councilmember",
         "url": "https://www.cityofrsm.org/Directory.aspx?EID=11"},
        {"name": "Bradley J. McGirr", "position": "Councilmember",
         "url": "https://www.cityofrsm.org/Directory.aspx?EID=8"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class SanClementeScraper(BaseScraper):
    """San Clemente - CivicPlus with directory pages."""

    CITY_NAME = "San Clemente"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "san-clemente.org"
    BASE_URL = "https://www.san-clemente.org"
    COUNCIL_URL = "https://www.sanclemente.gov/government/city-council"

    MEMBERS = [
        {"name": "Rick Loeffler", "position": "Mayor",
         "url": "https://www.san-clemente.org/Directory.aspx?EID=58"},
        {"name": "Steve Knoblock", "position": "Mayor Pro Tem",
         "url": "https://www.san-clemente.org/Directory.aspx?EID=57"},
        {"name": "Victor Cabral", "position": "Councilmember",
         "url": "https://www.san-clemente.org/Directory.aspx?EID=55"},
        {"name": "Mark Enmeier", "position": "Councilmember",
         "url": "https://www.san-clemente.org/Directory.aspx?EID=56"},
        {"name": "Zhen Wu", "position": "Councilmember",
         "url": "https://www.san-clemente.org/Directory.aspx?EID=59"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class SanJuanCapistranoScraper(BaseScraper):
    """San Juan Capistrano - CivicPlus with directory pages."""

    CITY_NAME = "San Juan Capistrano"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "sanjuancapistrano.org"
    BASE_URL = "https://sanjuancapistrano.org"
    COUNCIL_URL = "https://sanjuancapistrano.org/318/City-Council"

    MEMBERS = [
        {"name": "John Campbell", "position": "Mayor", "district": "District 3",
         "url": "https://sanjuancapistrano.org/directory.aspx?eid=47"},
        {"name": "John Taylor", "position": "Mayor Pro Tem", "district": "District 4",
         "url": "https://sanjuancapistrano.org/directory.aspx?eid=51"},
        {"name": "Sergio Farias", "position": "Councilmember", "district": "District 1",
         "url": "https://sanjuancapistrano.org/directory.aspx?eid=50"},
        {"name": "Troy A. Bourne", "position": "Councilmember", "district": "District 2",
         "url": "https://sanjuancapistrano.org/directory.aspx?eid=49"},
        {"name": "Howard Hart", "position": "Councilmember", "district": "District 5",
         "url": "https://sanjuancapistrano.org/directory.aspx?eid=48"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class SantaAnaScraper(BaseScraper):
    """Santa Ana - WordPress/ProudCity platform with individual contact pages."""

    CITY_NAME = "Santa Ana"
    PLATFORM = "proudcity"
    CITY_DOMAIN = "santa-ana.org"
    BASE_URL = "https://www.santa-ana.org"
    COUNCIL_URL = "https://www.santa-ana.org/city-council-members/"

    MEMBERS = [
        {"name": "Valerie Amezcua", "position": "Mayor", "district": "At-Large",
         "url": "https://www.santa-ana.org/contacts/valerie-amezcua/"},
        {"name": "Benjamin Vazquez", "position": "Mayor Pro Tem", "district": "Ward 6",
         "url": "https://www.santa-ana.org/contacts/benjamin-vazquez/"},
        {"name": "Johnathan Ryan Hernandez", "position": "Councilmember", "district": "Ward 1",
         "url": "https://www.santa-ana.org/contacts/johnathan-ryan-hernandez/"},
        {"name": "David Penaloza", "position": "Councilmember", "district": "Ward 2",
         "url": "https://www.santa-ana.org/contacts/david-penaloza/"},
        {"name": "Jessie Lopez", "position": "Councilmember", "district": "Ward 3",
         "url": "https://www.santa-ana.org/contacts/jessie-lopez/"},
        {"name": "Phil Bacerra", "position": "Councilmember", "district": "Ward 4",
         "url": "https://www.santa-ana.org/contacts/phil-bacerra/"},
        {"name": "Thai Viet Phan", "position": "Councilmember", "district": "Ward 5",
         "url": "https://www.santa-ana.org/contacts/thai-viet-phan/"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class BuenaParkScraper(BaseScraper):
    """Buena Park - PHP site, no individual profile pages (PDF bios only)."""

    CITY_NAME = "Buena Park"
    PLATFORM = "custom"
    CITY_DOMAIN = "buenapark.com"
    BASE_URL = "https://www.buenapark.com"
    COUNCIL_URL = "https://www.buenapark.com/city_departments/city_council/council_members.php"

    MEMBERS = [
        {"name": "Connor Traut", "position": "Mayor", "district": "District 5",
         "email": "ctraut@buenapark.com"},
        {"name": "Lamiya Hoque", "position": "Vice Mayor", "district": "District 4",
         "email": "lhoque@buenapark.com"},
        {"name": "Joyce Ahn", "position": "Councilmember", "district": "District 1",
         "email": "jahn@buenapark.com"},
        {"name": "Carlos Franco", "position": "Councilmember", "district": "District 2",
         "email": "cfranco@buenapark.com"},
        {"name": "Susan Sonne", "position": "Councilmember", "district": "District 3",
         "email": "ssonne@buenapark.com"},
    ]

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            self.add_council_member(
                name=member["name"],
                position=member["position"],
                district=member.get("district"),
                email=member.get("email"),
                phone=main_phones[0] if main_phones else None,
            )

        return self.get_results()


class CostaMesaScraper(BaseScraper):
    """Costa Mesa - Granicus platform (may block - use Firefox stealth)."""

    CITY_NAME = "Costa Mesa"
    PLATFORM = "granicus"
    CITY_DOMAIN = "costamesaca.gov"
    BASE_URL = "https://www.costamesaca.gov"
    COUNCIL_URL = "https://www.costamesaca.gov/government/mayor-city-council"

    MEMBERS = [
        {"name": "John Stephens", "position": "Mayor", "district": "At-Large",
         "url": "https://www.costamesaca.gov/government/mayor-city-council/mayor-john-stephens"},
        {"name": "Manuel Chavez", "position": "Mayor Pro Tem", "district": "District 4",
         "url": "https://www.costamesaca.gov/government/mayor-city-council/mayor-pro-tem-manuel-chavez"},
        {"name": "Mike Buley", "position": "Councilmember", "district": "District 1",
         "url": "https://www.costamesaca.gov/government/mayor-city-council/council-member-mike-buley"},
        {"name": "Loren Gameros", "position": "Councilmember", "district": "District 2",
         "url": "https://www.costamesaca.gov/government/mayor-city-council/council-member-loren-gameros"},
        {"name": "Andrea Marr", "position": "Councilmember", "district": "District 3",
         "url": "https://www.costamesaca.gov/government/mayor-city-council/council-member-andrea-marr"},
        {"name": "Arlis Reynolds", "position": "Councilmember", "district": "District 5",
         "url": "https://www.costamesaca.gov/government/mayor-city-council/council-member-arlis-reynolds"},
        {"name": "Jeff Pettis", "position": "Councilmember", "district": "District 6",
         "url": "https://www.costamesaca.gov/government/mayor-city-council/council-member-jeff-pettis"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class CypressScraper(BaseScraper):
    """Cypress - CivicPlus with individual profile pages."""

    CITY_NAME = "Cypress"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cypressca.org"
    BASE_URL = "https://www.cypressca.org"
    COUNCIL_URL = "https://www.cypressca.org/government/city-council"

    MEMBERS = [
        {"name": "David Burke", "position": "Mayor",
         "url": "https://www.cypressca.org/government/city-council/council-member-david-burke"},
        {"name": "Leo Medrano", "position": "Mayor Pro Tem", "district": "District 4",
         "url": "https://www.cypressca.org/government/city-council/council-member-leo-medrano"},
        {"name": "Kyle Chang", "position": "Councilmember", "district": "District 3",
         "url": "https://www.cypressca.org/government/city-council/council-member-kyle-change"},
        {"name": "Bonnie Peat", "position": "Councilmember",
         "url": "https://www.cypressca.org/government/city-council/mayor-pro-tem-bonnie-peat"},
        {"name": "Rachel Strong Carnahan", "position": "Councilmember", "district": "District 5",
         "url": "https://www.cypressca.org/government/city-council/council-member-rachel-strong"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class DanaPointScraper(BaseScraper):
    """Dana Point - Granicus platform."""

    CITY_NAME = "Dana Point"
    PLATFORM = "granicus"
    CITY_DOMAIN = "danapoint.org"
    BASE_URL = "https://www.danapoint.org"
    COUNCIL_URL = "https://www.danapoint.org/department/city-council"

    MEMBERS = [
        {"name": "John Gabbard", "position": "Mayor", "district": "District 1",
         "url": "https://www.danapoint.org/City-Government/City-Council/John-Gabbard"},
        {"name": "Mike Frost", "position": "Mayor Pro Tem", "district": "District 4",
         "url": "https://www.danapoint.org/City-Government/City-Council/Mike-Frost"},
        {"name": "Matthew Pagano", "position": "Councilmember", "district": "District 2",
         "url": "https://www.danapoint.org/City-Government/City-Council/Matthew-Pagano"},
        {"name": "Jamey M. Federico", "position": "Councilmember", "district": "District 3",
         "url": "https://www.danapoint.org/City-Government/City-Council/Jamey-M.-Federico"},
        {"name": "Michael Villar", "position": "Councilmember", "district": "District 5",
         "url": "https://www.danapoint.org/City-Government/City-Council/Michael-Villar"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class FountainValleyScraper(BaseScraper):
    """Fountain Valley - CivicPlus with directory pages."""

    CITY_NAME = "Fountain Valley"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "fountainvalley.gov"
    BASE_URL = "https://www.fountainvalley.gov"
    COUNCIL_URL = "https://www.fountainvalley.gov/156/City-Council"

    MEMBERS = [
        {"name": "Ted Bui", "position": "Mayor",
         "url": "https://www.fountainvalley.gov/Directory.aspx?EID=54"},
        {"name": "Jim Cunneen", "position": "Mayor Pro Tem",
         "url": "https://www.fountainvalley.gov/Directory.aspx?EID=178"},
        {"name": "Patrick Harper", "position": "Councilmember",
         "url": "https://www.fountainvalley.gov/Directory.aspx?EID=153"},
        {"name": "Kim Constantine", "position": "Councilmember",
         "url": "https://www.fountainvalley.gov/Directory.aspx?EID=152"},
        {"name": "Glenn Grandis", "position": "Councilmember",
         "url": "https://www.fountainvalley.gov/Directory.aspx?EID=55"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class FullertonScraper(BaseScraper):
    """Fullerton - CivicPlus with individual profile pages."""

    CITY_NAME = "Fullerton"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cityoffullerton.com"
    BASE_URL = "https://www.cityoffullerton.com"
    COUNCIL_URL = "https://www.cityoffullerton.com/government/city-council"

    MEMBERS = [
        {"name": "Fred Jung", "position": "Mayor", "district": "District 1",
         "url": "https://www.cityoffullerton.com/government/city-council/mayor-fred-jung"},
        {"name": "Nicholas Dunlap", "position": "Mayor Pro Tem", "district": "District 2",
         "url": "https://www.cityoffullerton.com/government/city-council/mayor-pro-tem-nicholas-dunlap"},
        {"name": "Dr. Shana Charles", "position": "Councilmember", "district": "District 3",
         "url": "https://www.cityoffullerton.com/government/city-council/council-member-shana-charles"},
        {"name": "Jamie Valencia", "position": "Councilmember", "district": "District 4",
         "url": "https://www.cityoffullerton.com/government/city-council/council-member-jamie-valencia"},
        {"name": "Dr. Ahmad Zahra", "position": "Councilmember", "district": "District 5",
         "url": "https://www.cityoffullerton.com/government/city-council/council-member-ahmad-zahra"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class GardenGroveScraper(BaseScraper):
    """Garden Grove - Granicus platform."""

    CITY_NAME = "Garden Grove"
    PLATFORM = "granicus"
    CITY_DOMAIN = "ggcity.org"
    BASE_URL = "https://ggcity.org"
    COUNCIL_URL = "https://ggcity.org/city-council"

    MEMBERS = [
        {"name": "Stephanie Klopfenstein", "position": "Mayor", "district": "Citywide",
         "url": "https://ggcity.org/city-council/stephanie-klopfenstein"},
        {"name": "George S. Brietigam III", "position": "Mayor Pro Tem", "district": "District 1",
         "url": "https://ggcity.org/city-council/george-brietigam"},
        {"name": "Phillip Nguyen", "position": "Councilmember", "district": "District 2",
         "url": "https://ggcity.org/city-council/phillip-nguyen"},
        {"name": "Cindy Ngoc Tran", "position": "Councilmember", "district": "District 3",
         "url": "https://ggcity.org/city-council/cindy-tran"},
        {"name": "Joe DoVinh", "position": "Councilmember", "district": "District 4",
         "url": "https://ggcity.org/city-council/joe-dovinh"},
        {"name": "Yesenia Muñeton", "position": "Councilmember", "district": "District 5",
         "url": "https://ggcity.org/city-council/yesenia-muneton"},
        {"name": "Ariana Arestegui", "position": "Councilmember", "district": "District 6",
         "url": "https://ggcity.org/city-council/ariana-arestegui"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class HuntingtonBeachScraper(BaseScraper):
    """Huntington Beach - Custom site, no individual profile pages."""

    CITY_NAME = "Huntington Beach"
    PLATFORM = "custom"
    CITY_DOMAIN = "huntingtonbeachca.gov"
    BASE_URL = "https://www.huntingtonbeachca.gov"
    COUNCIL_URL = "https://www.huntingtonbeachca.gov/government/city_council/index.php"

    # No individual profile pages - all members on main council page
    MEMBERS = [
        {"name": "Casey McKeon", "position": "Mayor",
         "email": "casey.mckeon@huntingtonbeachca.gov"},
        {"name": "Butch Twining", "position": "Mayor Pro Tem",
         "email": "butch.twining@huntingtonbeachca.gov"},
        {"name": "Pat Burns", "position": "Councilmember",
         "email": "pat.burns@huntingtonbeachca.gov"},
        {"name": "Don Kennedy", "position": "Councilmember",
         "email": "don.kennedy@huntingtonbeachca.gov"},
        {"name": "Gracey Larrea-Van Der Mark", "position": "Councilmember",
         "email": "gracey.larrea@huntingtonbeachca.gov"},
        {"name": "Chad Williams", "position": "Councilmember",
         "email": "chad.williams@huntingtonbeachca.gov"},
        {"name": "Andrew Gruel", "position": "Councilmember",
         "email": "andrew.gruel@huntingtonbeachca.gov"},
    ]

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            self.add_council_member(
                name=member["name"],
                position=member["position"],
                email=member.get("email"),
                phone=main_phones[0] if main_phones else None,
            )

        return self.get_results()


class IrvineScraper(BaseScraper):
    """Irvine - Custom site with individual profile pages."""

    CITY_NAME = "Irvine"
    PLATFORM = "custom"
    CITY_DOMAIN = "cityofirvine.org"
    BASE_URL = "https://www.cityofirvine.org"
    COUNCIL_URL = "https://www.cityofirvine.org/city-council"

    MEMBERS = [
        {"name": "Larry Agran", "position": "Mayor", "district": "At-Large",
         "url": "https://cityofirvine.org/city-council/mayor-larry-agran"},
        {"name": "James Mai", "position": "Vice Mayor", "district": "District 3",
         "url": "https://cityofirvine.org/city-council/vice-mayor-james-mai-district-3"},
        {"name": "Melinda Liu", "position": "Councilmember", "district": "District 1",
         "url": "https://cityofirvine.org/city-council/councilmember-melinda-liu-district-1"},
        {"name": "William Go", "position": "Councilmember", "district": "District 2",
         "url": "https://cityofirvine.org/city-council/councilmember-william-go-district-2"},
        {"name": "Mike Carroll", "position": "Councilmember", "district": "District 4",
         "url": "https://cityofirvine.org/city-council/councilmember-mike-carroll-district-4"},
        {"name": "Betty Martinez Franco", "position": "Councilmember", "district": "District 5",
         "url": "https://cityofirvine.org/city-council/councilmember-betty-martinez-franco-%E2%80%93-district-5"},
        {"name": "Kathleen Treseder", "position": "Councilmember", "district": "At-Large",
         "url": "https://cityofirvine.org/city-council/councilmember-kathleen-treseder-large"},
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            data = await self.scrape_member_page(member, self.BASE_URL, self.CITY_DOMAIN, main_phones)
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()


class LagunaNiguelScraper(BaseScraper):
    """Laguna Niguel - CivicPlus, no individual profile pages."""

    CITY_NAME = "Laguna Niguel"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cityoflagunaniguel.org"
    BASE_URL = "https://www.cityoflagunaniguel.org"
    COUNCIL_URL = "https://www.cityoflagunaniguel.org/396/Mayor-City-Council"

    # No individual profile pages - all members on main council page
    MEMBERS = [
        {"name": "Gene Johns", "position": "Mayor",
         "email": "GJohns@cityoflagunaniguel.org"},
        {"name": "Kelly Jennings", "position": "Mayor Pro Tem",
         "email": "KJennings@cityoflagunaniguel.org"},
        {"name": "Ray Gennawey", "position": "Councilmember",
         "email": "RGennawey@cityoflagunaniguel.org"},
        {"name": "Stephanie Oddo", "position": "Councilmember",
         "email": "SOddo@cityoflagunaniguel.org"},
        {"name": "Stephanie Winstead", "position": "Councilmember",
         "email": "SWinstead@cityoflagunaniguel.org"},
    ]

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            self.add_council_member(
                name=member["name"],
                position=member["position"],
                email=member.get("email"),
                phone=main_phones[0] if main_phones else None,
            )

        return self.get_results()


class LakeForestScraper(BaseScraper):
    """Lake Forest - Custom site, no individual profile pages."""

    CITY_NAME = "Lake Forest"
    PLATFORM = "custom"
    CITY_DOMAIN = "lakeforestca.gov"
    BASE_URL = "https://www.lakeforestca.gov"
    COUNCIL_URL = "https://www.lakeforestca.gov/city_government/city_council/index.php"

    # No individual profile pages - all members on main council page
    MEMBERS = [
        {"name": "Robert Pequeño", "position": "Mayor", "district": "District 5",
         "email": "rpequeno@lakeforestca.gov"},
        {"name": "Doug Cirbo", "position": "Mayor Pro Tem", "district": "District 1",
         "email": "dcirbo@lakeforestca.gov"},
        {"name": "Mark Tettemer", "position": "Councilmember", "district": "District 4",
         "email": "mtettemer@lakeforestca.gov"},
        {"name": "Scott Voigts", "position": "Councilmember", "district": "District 3",
         "email": "svoigts@lakeforestca.gov"},
        {"name": "Benjamin Yu", "position": "Councilmember", "district": "District 2",
         "email": "byu@lakeforestca.gov"},
    ]

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            self.add_council_member(
                name=member["name"],
                position=member["position"],
                district=member.get("district"),
                email=member.get("email"),
                phone=main_phones[0] if main_phones else None,
            )

        return self.get_results()


class LosAlamitosScraper(BaseScraper):
    """Los Alamitos - CivicPlus, no individual profile pages."""

    CITY_NAME = "Los Alamitos"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cityoflosalamitos.org"
    BASE_URL = "https://cityoflosalamitos.org"
    COUNCIL_URL = "https://cityoflosalamitos.org/165/City-Council"

    # No individual profile pages - all members on main council page
    MEMBERS = [
        {"name": "Tanya Doby", "position": "Mayor",
         "email": "tdoby@cityoflosalamitos.org"},
        {"name": "Jordan Nefulda", "position": "Mayor Pro Tem",
         "email": "jnefulda@cityoflosalamitos.org"},
        {"name": "Gary Loe", "position": "Councilmember", "district": "District 2",
         "email": "Gloe@cityoflosalamitos.org"},
        {"name": "Shelley Hasselbrink", "position": "Councilmember", "district": "District 4",
         "email": "shasselbrink@cityoflosalamitos.org"},
        {"name": "Emily Hibard", "position": "Councilmember", "district": "District 5",
         "email": "ehibard@cityoflosalamitos.org"},
    ]

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        for member in self.MEMBERS:
            self.add_council_member(
                name=member["name"],
                position=member["position"],
                district=member.get("district"),
                email=member.get("email"),
                phone=main_phones[0] if main_phones else None,
            )

        return self.get_results()
