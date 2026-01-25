"""
San Juan Capistrano City Council Scraper
Dynamically discovers council members from website.
"""
import re
from ..base import BaseScraper


class SanJuanCapistranoScraper(BaseScraper):
    """San Juan Capistrano - text pattern matching for council members."""

    CITY_NAME = "San Juan Capistrano"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "sanjuancapistrano.org"
    BASE_URL = "https://sanjuancapistrano.org"
    COUNCIL_URL = "https://sanjuancapistrano.org/318/City-Council"
    DIRECTORY_URL = "https://sanjuancapistrano.org/Directory.aspx?did=35"

    def get_urls(self):
        return {"council": self.COUNCIL_URL, "directory": self.DIRECTORY_URL}

    async def discover_members(self):
        """Discover council members by matching name patterns on page.

        Format on SJC page: "Name" followed by "Position, District X"
        e.g., "John Campbell" then "Mayor, District 3"
        """
        members = []
        seen_names = set()

        try:
            text = await self.get_page_text()
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)

            # Pattern: Name followed by position/district info
            # e.g., "John Campbell Mayor, District 3" or "Sergio Farias District 1"
            name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)'

            # Find Mayor Pro Tem - "Name Mayor Pro Tem, District X"
            for match in re.finditer(rf'{name_pattern}\s+Mayor\s+Pro\s+Tem[,\s]+District\s+\d', text):
                name = match.group(1).strip()
                if name.lower() not in seen_names and len(name.split()) >= 2:
                    seen_names.add(name.lower())
                    members.append({"name": name, "position": "Mayor Pro Tem"})
                    print(f"      Found: {name} (Mayor Pro Tem)")

            # Find Mayor (not Pro Tem) - "Name Mayor, District X"
            for match in re.finditer(rf'{name_pattern}\s+Mayor[,\s]+District\s+\d', text):
                name = match.group(1).strip()
                if name.lower() not in seen_names and len(name.split()) >= 2:
                    seen_names.add(name.lower())
                    members.append({"name": name, "position": "Mayor"})
                    print(f"      Found: {name} (Mayor)")

            # Find Council Members - "Name District X" (no explicit title)
            for match in re.finditer(rf'{name_pattern}\s+District\s+\d', text):
                name = match.group(1).strip()
                if name.lower() not in seen_names and len(name.split()) >= 2:
                    seen_names.add(name.lower())
                    members.append({"name": name, "position": "Councilmember"})
                    print(f"      Found: {name} (Councilmember)")

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

        # Visit directory page to get emails
        print("    Getting emails from directory...")
        dir_result = await self.visit_page(self.DIRECTORY_URL, "directory")
        dir_emails = dir_result.get("emails", [])
        dir_phones = dir_result.get("phones", [])

        print(f"      Found {len(dir_emails)} emails in directory")

        # Add members with matched emails
        for member in members:
            email = self.match_email_to_name(member["name"], dir_emails, self.CITY_DOMAIN)
            phone = dir_phones[0] if dir_phones else (main_phones[0] if main_phones else None)

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                email=email,
                phone=phone,
            )

        return self.get_results()
