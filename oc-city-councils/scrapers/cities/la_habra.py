"""
La Habra City Council Scraper
Dynamically discovers council members from website.
"""
import re
from ..base import BaseScraper


class LaHabraScraper(BaseScraper):
    """La Habra - CivicPlus platform with PDF bios (no profile pages)."""

    CITY_NAME = "La Habra"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "lahabraca.gov"
    BASE_URL = "https://www.lahabraca.gov"
    COUNCIL_URL = "https://www.lahabraca.gov/153/City-Council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self, main_emails):
        """
        Discover council members from the main council page.
        La Habra lists all members on one page with photos.
        """
        members = []
        seen_names = set()

        try:
            text = await self.get_page_text()

            # Normalize whitespace (collapse multiple spaces/newlines into single space)
            # This helps match "Name,\nMayor" patterns
            text = re.sub(r'\s+', ' ', text)

            # Find council member patterns in text
            # La Habra format: "Name, Position" (comma separator)
            # Match patterns like "Jose Medrano, Mayor" or "James Gomez, Mayor Pro Tem"
            # Use strict capitalization for names (First Last) to avoid matching "COUNCIL Jose"
            # Position matching is case-insensitive via alternation
            pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*,?\s*([Mm]ayor(?:\s+[Pp]ro\s+[Tt]em)?|[Cc]ouncil\s*[Mm]ember)'

            for match in re.finditer(pattern, text):
                name = match.group(1).strip()
                position_raw = match.group(2).strip()

                # Validate name structure - must be proper name (First Last)
                name_parts = name.split()
                if len(name_parts) < 2:
                    continue

                # Skip if first word is a common word (not a name)
                skip_first_words = [
                    "and", "or", "the", "one", "to", "for", "in", "on", "at",
                    "pro", "tem", "acts", "who", "each", "another", "elected",
                    "city", "council", "mayor", "member", "with", "has", "was"
                ]
                if name_parts[0].lower() in skip_first_words:
                    continue

                # Each name part must be at least 2 characters
                if any(len(part) < 2 for part in name_parts):
                    continue

                # Name must be at least 5 characters total (e.g., "Al Li")
                if len(name) < 5:
                    continue

                # Skip if already seen
                if name.lower() in seen_names:
                    continue

                # Skip generic words that aren't names
                skip_words = ["city", "council", "meeting", "agenda", "mayor", "member"]
                if any(w in name.lower() for w in skip_words):
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

                # Match email
                email = self.match_email_to_name(name, main_emails, self.CITY_DOMAIN)

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
        main_emails = main_result.get("emails", [])

        print("    Discovering council members...")
        members = await self.discover_members(main_emails)

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} members")

        # La Habra uses a shared council email - assign to all members
        shared_email = None
        for email in main_emails:
            if "citycouncil" in email.lower() or "council" in email.lower():
                shared_email = email
                break

        for member in members:
            self.add_council_member(
                name=member["name"],
                position=member["position"],
                email=member.get("email") or shared_email,
                phone=main_phones[0] if main_phones else None,
                profile_url=self.COUNCIL_URL,  # All on main page
            )

        return self.get_results()
