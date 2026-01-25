"""
Seal Beach City Council Scraper
Dynamically discovers council members from website.
All members on single page - no individual profile pages.
"""
import re
from datetime import datetime
from ..base import BaseScraper


class SealBeachScraper(BaseScraper):
    """Seal Beach - CivicPlus, all members on single page."""

    CITY_NAME = "Seal Beach"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "sealbeachca.gov"
    BASE_URL = "https://www.sealbeachca.gov"
    COUNCIL_URL = "https://www.sealbeachca.gov/Government/City-Council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self, main_emails):
        """
        Discover council members from the main page.
        Seal Beach lists all members with positions on one page.
        """
        members = []
        current_year = datetime.now().year

        try:
            text = await self.get_page_text()

            # Find email addresses first - they contain names (e.g., llandau@)
            # Then find corresponding name and position info nearby
            for email in main_emails:
                local_part = email.split("@")[0].lower()

                # Search for name patterns near the email or anywhere on page
                # Names typically appear as "First Last" or "First M. Last"
                name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-zA-Z]+)'
                name_matches = re.findall(name_pattern, text)

                matched_name = None
                for name in name_matches:
                    name_clean = name.strip()
                    name_parts = name_clean.lower().split()
                    if len(name_parts) < 2:
                        continue

                    first_name = name_parts[0]
                    last_name = name_parts[-1]

                    # Check if email matches this name
                    if (local_part == f"{first_name[0]}{last_name}" or
                        local_part == f"{first_name}{last_name}" or
                        local_part == last_name):
                        matched_name = name_clean
                        break

                if not matched_name:
                    continue

                # Determine position based on year designations
                # Seal Beach format: "2025 & 2026 Mayor" or "2024, 2026 Mayor Pro Tem"
                position = "Councilmember"
                name_escaped = re.escape(matched_name)

                # Get text after the name for position parsing
                name_idx = text.lower().find(matched_name.lower())
                if name_idx >= 0:
                    after_name = text[name_idx:name_idx + 500]
                    current_year_str = str(current_year)

                    # Look for Mayor (not Pro Tem) designation that includes current year
                    # Patterns: "2026 Mayor", "2025 & 2026 Mayor"
                    mayor_match = re.search(
                        rf'(\d{{4}}[,\s&]+)*{current_year_str}[,\s&]*\s*Mayor(?!\s+Pro)',
                        after_name, re.IGNORECASE
                    )

                    # Look for Mayor Pro Tem designation that includes current year
                    # Patterns: "2026 Mayor Pro Tem", "2024, 2026 Mayor Pro Tem"
                    mpt_match = re.search(
                        rf'(\d{{4}}[,\s&]+)*{current_year_str}[,\s&]*\s*Mayor\s+Pro\s+Tem',
                        after_name, re.IGNORECASE
                    )

                    if mayor_match:
                        position = "Mayor"
                    elif mpt_match:
                        position = "Mayor Pro Tem"

                # Find district
                district = None
                district_pattern = rf'{name_escaped}.*?District\s+(One|Two|Three|Four|Five|\d+)'
                district_match = re.search(district_pattern, text, re.IGNORECASE | re.DOTALL)
                if district_match:
                    district_text = district_match.group(1)
                    district_map = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5"}
                    district_num = district_map.get(district_text.lower(), district_text)
                    district = f"District {district_num}"

                # Avoid duplicates
                if any(m["name"].lower() == matched_name.lower() for m in members):
                    continue

                members.append({
                    "name": matched_name,
                    "position": position,
                    "district": district,
                    "email": email,
                })
                print(f"      Found: {matched_name} ({position})")

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
                district=member.get("district"),
                email=member.get("email"),
                phone=main_phones[0] if main_phones else None,
            )

        return self.get_results()
