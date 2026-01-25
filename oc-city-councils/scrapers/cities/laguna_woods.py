"""
Laguna Woods City Council Scraper
Dynamically discovers council members from website.
"""
import re
from ..base import BaseScraper


class LagunaWoodsScraper(BaseScraper):
    """Laguna Woods - WordPress-style site with all members on main page."""

    CITY_NAME = "Laguna Woods"
    PLATFORM = "wordpress"
    CITY_DOMAIN = "cityoflagunawoods.org"
    BASE_URL = "https://www.cityoflagunawoods.org"
    COUNCIL_URL = "https://www.cityoflagunawoods.org/city-council/"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self, main_emails):
        """
        Discover council members from the main council page.
        Laguna Woods lists all members on main page with position before name.
        """
        members = []
        seen_names = set()

        try:
            text = await self.get_page_text()

            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)

            # Laguna Woods format: "Position Name – details"
            # e.g., "Mayor Annie McCary – Elected in 2022..."
            # e.g., "Mayor Pro Tem Pearl Lee – Elected in 2024..."
            # e.g., "Councilmember Shari L. Horne – ..."
            # Name pattern handles names like "McCary" (Mc + capital + lowercase)
            # or normal names, plus optional middle initial
            name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+(?:Mc)?[A-Z][a-z]+)'

            # Match each position pattern separately to avoid conflicts
            patterns = [
                (rf'[Mm]ayor\s+[Pp]ro\s+[Tt]em\s+{name_pattern}', "Mayor Pro Tem"),
                (rf'[Cc]ouncil\s*[Mm]ember\s+{name_pattern}', "Councilmember"),
            ]

            for pattern, position in patterns:
                for match in re.finditer(pattern, text):
                    name = match.group(1).strip()

                    # Validate name structure
                    name_parts = name.split()
                    if len(name_parts) < 2:
                        continue

                    # Skip common words
                    skip_first_words = [
                        "and", "or", "the", "one", "to", "for", "in", "on", "at",
                        "city", "council", "mayor", "member", "with", "has", "was",
                        "elected", "appointed", "serves", "meeting", "contact", "pro", "tem"
                    ]
                    if name_parts[0].lower() in skip_first_words:
                        continue

                    # Skip if already seen
                    if name.lower() in seen_names:
                        continue

                    seen_names.add(name.lower())

                    # Match email from main page
                    email = self.match_email_to_name(name, main_emails, self.CITY_DOMAIN)

                    members.append({
                        "name": name,
                        "position": position,
                        "email": email,
                    })
                    print(f"      Found: {name} ({position})")

            # Now find the Mayor (making sure we don't match "Mayor Pro Tem")
            # Use negative lookahead to exclude "Mayor Pro Tem"
            mayor_pattern = rf'[Mm]ayor\s+(?![Pp]ro){name_pattern}'
            for match in re.finditer(mayor_pattern, text):
                name = match.group(1).strip()

                name_parts = name.split()
                if len(name_parts) < 2:
                    continue

                skip_first_words = ["pro", "tem", "and", "or", "the"]
                if name_parts[0].lower() in skip_first_words:
                    continue

                if name.lower() in seen_names:
                    continue

                seen_names.add(name.lower())
                email = self.match_email_to_name(name, main_emails, self.CITY_DOMAIN)

                members.append({
                    "name": name,
                    "position": "Mayor",
                    "email": email,
                })
                print(f"      Found: {name} (Mayor)")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])
        main_emails = main_result.get("emails", [])

        print("    Discovering council members...")
        members = await self.discover_members(main_emails)

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} members")

        for member in members:
            self.add_council_member(
                name=member["name"],
                position=member["position"],
                email=member.get("email"),
                phone=main_phones[0] if main_phones else None,
                profile_url=self.COUNCIL_URL,
            )

        return self.get_results()
