"""
Lake Forest City Council Scraper
Dynamically discovers council members from website.
All members on single page - no individual profile pages.
"""
import re
import unicodedata
from ..base import BaseScraper


class LakeForestScraper(BaseScraper):
    """Lake Forest - Custom PHP, all members on single page."""

    CITY_NAME = "Lake Forest"
    PLATFORM = "custom"
    CITY_DOMAIN = "lakeforestca.gov"
    BASE_URL = "https://www.lakeforestca.gov"
    COUNCIL_URL = "https://www.lakeforestca.gov/city_government/city_council/index.php"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    def _normalize(self, text):
        """Remove accents and normalize text for matching."""
        normalized = unicodedata.normalize('NFKD', text)
        return ''.join(c for c in normalized if not unicodedata.combining(c)).lower()

    async def discover_members(self, main_emails):
        """Discover council members from the main page."""
        members = []

        try:
            text = await self.get_page_text()
            text_normalized = self._normalize(text)

            for email in main_emails:
                local_part = email.split("@")[0].lower()

                # Derive last name from email (flast pattern)
                if len(local_part) < 3:
                    continue

                # Email is first initial + last name (e.g., rpequeno, dcirbo)
                email_last = local_part[1:]  # Remove first initial

                # Search for name in text: [First] [Last] where Last matches email
                # Use normalized text for searching
                pattern = rf'([A-Za-z]+)\s+({email_last}[a-z]*)'
                match = re.search(pattern, text_normalized, re.IGNORECASE)

                if not match:
                    continue

                first_name = match.group(1).title()
                last_name = match.group(2).title()
                name = f"{first_name} {last_name}"

                # Avoid duplicates
                if any(m["name"].lower() == name.lower() for m in members):
                    continue

                # Determine position from context
                position = "Councilmember"
                match_start = match.start()
                start = max(0, match_start - 100)
                end = min(len(text_normalized), match.end() + 50)
                context = text_normalized[start:end]

                if "mayor pro tem" in context or "pro tem" in context:
                    position = "Mayor Pro Tem"
                elif "mayor" in context and "pro tem" not in context:
                    position = "Mayor"

                members.append({
                    "name": name,
                    "position": position,
                    "email": email,
                })
                print(f"      Found: {name} ({position})")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])
        main_emails = [e for e in main_result.get("emails", [])
                       if self.CITY_DOMAIN.lower() in e.lower()]

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
            )

        return self.get_results()
