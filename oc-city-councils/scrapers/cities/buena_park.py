"""
Buena Park City Council Scraper
Dynamically discovers council members from website.
"""
import re
from ..base import BaseScraper


class BuenaParkScraper(BaseScraper):
    """Buena Park - PHP site with all info on main council page."""

    CITY_NAME = "Buena Park"
    PLATFORM = "custom"
    CITY_DOMAIN = "buenapark.com"
    BASE_URL = "https://www.buenapark.com"
    COUNCIL_URL = "https://www.buenapark.com/city_departments/city_council/council_members.php"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """
        Discover council members from the main council page.
        Buena Park pattern: All members on one page with photos and info.
        Look for patterns like "Mayor Connor Traut" or "Council Member Joyce Ahn"
        """
        members = []

        try:
            text = await self.get_page_text()
            text_lines = text.split('\n')

            # Pattern to match member lines
            # Examples: "Mayor Connor Traut", "Vice Mayor Lamiya Hoque", "Council Member Carlos Franco"
            # Name must start with capital letter and be a proper name (not words like "and", "to", "serve")
            member_pattern = re.compile(
                r'(Mayor|Vice Mayor|Council\s*Member)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                re.IGNORECASE
            )

            # Skip words that indicate descriptive text, not names
            skip_first_words = ["and", "to", "the", "one", "each", "another", "who", "elected"]

            seen_names = set()

            for line in text_lines:
                match = member_pattern.search(line)
                if match:
                    position_raw = match.group(1).strip()
                    name = match.group(2).strip()

                    # Skip if name starts with descriptive words (not a real name)
                    first_word = name.split()[0].lower() if name.split() else ""
                    if first_word in skip_first_words:
                        continue

                    # Skip very short names or names that look like text fragments
                    if len(name) < 5 or len(name.split()) < 2:
                        continue

                    # Normalize position
                    pos_lower = position_raw.lower()
                    if "vice mayor" in pos_lower:
                        position = "Vice Mayor"
                    elif "mayor" in pos_lower:
                        position = "Mayor"
                    else:
                        position = "Councilmember"

                    # Skip duplicates
                    if name.lower() in seen_names:
                        continue
                    seen_names.add(name.lower())

                    # Try to find district from nearby text
                    district = None
                    district_match = re.search(rf'{re.escape(name)}.*?District\s*(\d+)', text, re.IGNORECASE | re.DOTALL)
                    if district_match:
                        district = f"District {district_match.group(1)}"

                    members.append({
                        "name": name,
                        "position": position,
                        "district": district,
                        "url": None  # No individual profile pages
                    })
                    print(f"      Found: {name} ({position}) - {district or 'No district'}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def extract_emails_for_members(self, members):
        """Match emails to member names from page."""
        try:
            text = await self.get_page_text()
            emails = self.extract_emails(text)

            # Also get mailto links
            mailto_emails = await self.get_mailto_links()
            all_emails = list(set(emails + mailto_emails))

            for member in members:
                matched_email = self.match_email_to_name(
                    member["name"],
                    all_emails,
                    self.CITY_DOMAIN
                )
                if matched_email:
                    member["email"] = matched_email
                    print(f"      Email matched: {member['name']} -> {matched_email}")

        except Exception as e:
            self.results["errors"].append(f"extract_emails: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        # Visit main council page
        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        # Discover members dynamically
        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        # Match emails to members
        print("    Matching emails to members...")
        members = await self.extract_emails_for_members(members)

        print(f"    Found {len(members)} members")

        # Add all members
        for member in members:
            self.add_council_member(
                name=member["name"],
                position=member["position"],
                district=member.get("district"),
                email=member.get("email"),
                phone=main_phones[0] if main_phones else None,
                profile_url=self.COUNCIL_URL,  # All on main page
            )

        return self.get_results()
