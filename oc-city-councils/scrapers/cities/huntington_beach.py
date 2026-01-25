"""
Huntington Beach City Council Scraper
Dynamically discovers council members from website.
All members on single page - no individual profile pages.
"""
import re
from ..base import BaseScraper


class HuntingtonBeachScraper(BaseScraper):
    """Huntington Beach - Custom PHP, all members on single page."""

    CITY_NAME = "Huntington Beach"
    PLATFORM = "custom"
    CITY_DOMAIN = "surfcity-hb.org"
    BASE_URL = "https://www.huntingtonbeachca.gov"
    COUNCIL_URL = "https://www.huntingtonbeachca.gov/government/city_council/index.php"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self, page_text, main_emails):
        """Discover council members from the main page text."""
        members = []

        # Match name patterns from emails (e.g., Chad.Williams@ -> Chad Williams)
        for email in main_emails:
            local_part = email.split("@")[0]

            # Handle first.last pattern
            if "." in local_part:
                parts = local_part.split(".")
                if len(parts) == 2:
                    first_name = parts[0].capitalize()
                    last_name = parts[1]

                    # Handle camelCase last names (VanDerMark -> Van Der Mark)
                    # Split on capital letters
                    last_name_spaced = re.sub(r'([A-Z])', r' \1', last_name).strip()
                    last_name_display = last_name_spaced.title()

                    name = f"{first_name} {last_name_display}"

                    # Check if any part of the name appears in page text
                    name_check = last_name.lower()
                    if name_check in page_text.lower() or last_name_spaced.lower() in page_text.lower():
                        # Determine position from page text
                        position = self._detect_position(name, page_text)

                        members.append({
                            "name": name,
                            "position": position,
                            "email": email,
                        })
                        print(f"      Found: {name} ({position})")

        return members

    def _detect_position(self, name, text):
        """Detect position for a member from page text."""
        text_lower = text.lower()
        name_lower = name.lower()
        first_name = name_lower.split()[0]

        # Search for position mentions near the name
        # Check for Mayor Pro Tem first (more specific)
        pro_tem_patterns = [
            rf'mayor\s+pro\s+tem[:\s]*{first_name}',
            rf'{first_name}[^,\n]{{0,20}}mayor\s+pro\s+tem',
        ]
        for pattern in pro_tem_patterns:
            if re.search(pattern, text_lower):
                return "Mayor Pro Tem"

        # Check for Mayor (use negative lookahead only)
        mayor_patterns = [
            rf'mayor[:\s]*{first_name}',
            rf'{first_name}[^,\n]{{0,20}}mayor(?!\s+pro)',
        ]
        for pattern in mayor_patterns:
            match = re.search(pattern, text_lower)
            if match:
                # Make sure it's not actually "mayor pro tem"
                matched_text = text_lower[max(0, match.start()-10):match.end()+15]
                if "pro tem" not in matched_text:
                    return "Mayor"

        return "Councilmember"

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])
        main_emails = [e for e in main_result.get("emails", [])
                       if self.CITY_DOMAIN.lower() in e.lower()]

        page_text = await self.get_page_text()

        print("    Discovering council members...")
        members = await self.discover_members(page_text, main_emails)

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} members")

        for member in members:
            self.add_council_member(
                name=member["name"],
                position=member["position"],
                email=member["email"],
                phone=main_phones[0] if main_phones else None,
            )

        return self.get_results()
