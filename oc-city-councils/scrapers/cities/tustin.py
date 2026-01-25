"""
Tustin City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class TustinScraper(BaseScraper):
    """Tustin - CivicPlus with dynamic member discovery."""

    CITY_NAME = "Tustin"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "tustinca.org"
    BASE_URL = "https://www.tustinca.org"
    COUNCIL_URL = "https://www.tustinca.org/482/City-Council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """Discover council members from CivicPlus-style links."""
        members = []
        seen_ids = set()

        try:
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or len(text) < 3:
                    continue

                href_lower = href.lower()

                # Look for council member profile links
                # Pattern: /ID/Mayor-Name or /ID/Mayor-Pro-Tem-Name or /ID/Council-Member-Name
                match = re.search(r'/(\d+)/(mayor-pro-tem|mayor|council-member)-(.+?)/?$', href_lower)
                if not match:
                    continue

                page_id = match.group(1)
                position_slug = match.group(2)
                name_slug = match.group(3)

                # Skip main council page
                if page_id == "482":
                    continue

                if page_id in seen_ids:
                    continue
                seen_ids.add(page_id)

                # Determine position from URL
                if position_slug == "mayor-pro-tem":
                    position = "Mayor Pro Tem"
                elif position_slug == "mayor":
                    position = "Mayor"
                else:
                    position = "Councilmember"

                # Convert name slug to proper name
                # Handle middle initials: "lee-k-fink" -> "Lee K. Fink"
                name_parts = name_slug.split("-")
                name_formatted = []
                for i, part in enumerate(name_parts):
                    if len(part) == 1:
                        # Single letter = initial, add period
                        name_formatted.append(part.upper() + ".")
                    else:
                        name_formatted.append(part.title())
                name = " ".join(name_formatted)

                full_url = urljoin(self.BASE_URL, href)

                members.append({
                    "name": name,
                    "position": position,
                    "url": full_url,
                })
                print(f"      Found: {name} ({position})")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def detect_position_from_page(self):
        """Detect position from page content - check for Mayor Pro Tem."""
        try:
            text = await self.get_page_text()
            text_lower = text.lower()

            # Look for Mayor Pro Tem indication
            if re.search(r'\bmayor\s+pro\s+tem\b', text_lower[:1000]):
                return "Mayor Pro Tem"

            # Check page title
            title = await self.page.title()
            if title and "mayor pro tem" in title.lower():
                return "Mayor Pro Tem"

        except Exception:
            pass
        return None  # Return None to keep URL-based position

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

        for member in members:
            print(f"    Scraping member: {member['name']}")
            result = await self.visit_page(member["url"], f"member_{member['name']}")

            if result.get("status") == "success":
                # Check if page indicates Mayor Pro Tem
                page_position = await self.detect_position_from_page()
                position = page_position if page_position else member["position"]

                photo_url = await self.extract_photo_url(member["name"], self.BASE_URL)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                member_email = None
                page_emails = result.get("emails", [])
                if page_emails:
                    member_email = self.match_email_to_name(
                        member["name"], page_emails, self.CITY_DOMAIN
                    )
                    if not member_email and len(page_emails) == 1:
                        member_email = page_emails[0]

                result_phones = result.get("phones", [])
                member_phone = result_phones[0] if result_phones else (main_phones[0] if main_phones else None)

                self.add_council_member(
                    name=member["name"],
                    position=position,
                    email=member_email,
                    phone=member_phone,
                    profile_url=member["url"],
                    photo_url=photo_url,
                    bio=bio,
                    term_start=term_start,
                    term_end=term_end,
                )
            else:
                self.add_council_member(
                    name=member["name"],
                    position=member["position"],
                    profile_url=member["url"],
                )

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()
