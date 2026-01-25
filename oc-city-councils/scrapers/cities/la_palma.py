"""
La Palma City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class LaPalmaScraper(BaseScraper):
    """La Palma - CivicPlus platform with name/position text pattern."""

    CITY_NAME = "La Palma"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "lapalmaca.gov"
    BASE_URL = "https://www.lapalmaca.gov"
    COUNCIL_URL = "https://www.lapalmaca.gov/66/City-Council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """
        Discover council members from the main council page.
        La Palma lists members with name, position, and district on separate lines.
        """
        members = []
        seen_names = set()

        try:
            text = await self.get_page_text()

            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)

            # La Palma format: "Position (District) Name"
            # e.g., "Mayor (At-Large) Nitesh P. Patel"
            # e.g., "Mayor Pro Tem (District 1) Debbie S. Baker"
            # e.g., "Council Member (District 5) Mark I. Waldman"
            # Pattern matches: Position, optional district info, then name
            pattern = r'([Mm]ayor(?:\s+[Pp]ro\s+[Tt]em)?|[Cc]ouncil\s*[Mm]ember)\s+\([^)]+\)\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)'

            for match in re.finditer(pattern, text):
                position_raw = match.group(1).strip()
                name = match.group(2).strip()

                # Validate name structure
                name_parts = name.split()
                if len(name_parts) < 2:
                    continue

                # Skip common words
                skip_first_words = [
                    "and", "or", "the", "one", "to", "for", "in", "on", "at",
                    "city", "council", "mayor", "member", "with", "has", "was",
                    "elected", "appointed", "serves"
                ]
                if name_parts[0].lower() in skip_first_words:
                    continue

                # Skip if already seen
                if name.lower() in seen_names:
                    continue

                # Normalize position
                pos_lower = position_raw.lower()
                if "mayor pro tem" in pos_lower:
                    position = "Mayor Pro Tem"
                elif "mayor" in pos_lower:
                    position = "Mayor"
                else:
                    position = "Councilmember"

                seen_names.add(name.lower())

                members.append({
                    "name": name,
                    "position": position,
                })
                print(f"      Found: {name} ({position})")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])
        main_emails = main_result.get("emails", [])

        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} members")

        # La Palma uses a shared council email - find it
        shared_email = None
        for email in main_emails:
            if "citycouncil" in email.lower() or "council" in email.lower():
                shared_email = email
                break

        for member in members:
            # Try individual email first, fall back to shared
            email = self.match_email_to_name(member["name"], main_emails, self.CITY_DOMAIN)

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                email=email or shared_email,
                phone=main_phones[0] if main_phones else None,
                profile_url=self.COUNCIL_URL,
            )

        return self.get_results()
