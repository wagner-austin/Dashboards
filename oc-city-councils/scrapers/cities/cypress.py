"""
Cypress City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class CypressScraper(BaseScraper):
    """Cypress - CivicPlus/Granicus with individual profile pages."""

    CITY_NAME = "Cypress"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cypressca.org"
    BASE_URL = "https://www.cypressca.org"
    COUNCIL_URL = "https://www.cypressca.org/government/city-council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """
        Discover council members from the main council page.
        Cypress pattern: Links to council-member-{name} or mayor-pro-tem-{name} pages.
        """
        members = []
        seen_urls = set()

        try:
            # Find all links that look like council member pages
            links = await self.page.query_selector_all('a[href*="/city-council/"]')

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                href_lower = href.lower()

                # Skip navigation/generic links
                skip_patterns = [
                    "mailto:", "#", "javascript:", "calendar", "agenda",
                    "minutes", "policies", "contact", "commission"
                ]
                if any(skip in href_lower for skip in skip_patterns):
                    continue

                # Must be a member-specific URL
                if not re.search(r'/city-council/(council-member-|mayor-pro-tem-|mayor-)[a-z]', href_lower):
                    continue

                # Normalize URL for deduplication
                full_url = urljoin(self.BASE_URL, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Extract name from link text (remove position prefix)
                name = text.strip()
                for prefix in ["Mayor Pro Tem", "Mayor", "Council Member", "Councilmember"]:
                    if name.lower().startswith(prefix.lower()):
                        name = name[len(prefix):].strip()

                if len(name) < 4:
                    continue

                # Initial position guess from text (will verify from individual page)
                position = "Councilmember"
                text_lower = text.lower()
                if "mayor pro tem" in text_lower:
                    position = "Mayor Pro Tem"
                elif "mayor" in text_lower and "pro tem" not in text_lower:
                    position = "Mayor"

                members.append({
                    "name": name,
                    "position": position,
                    "url": full_url,
                })
                print(f"      Found: {name} ({position})")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def detect_position_from_page(self, initial_position="Councilmember"):
        """
        Detect position from the current member's page.
        NOTE: Cypress doesn't update URLs when positions change (Mayor rotates yearly),
        so we TRUST the initial position from the main page which is current.
        URLs may have outdated positions from when the page was created.
        """
        # Trust the main page's position detection - it reflects the CURRENT position
        # Individual page URLs may have old positions (e.g., someone who WAS Mayor Pro Tem
        # but is now a Councilmember still has mayor-pro-tem in their URL)
        return initial_position

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        # Visit main council page
        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")

        if main_result.get("status") != "success":
            print(f"    ERROR: Could not access council page")
            return self.get_results()

        main_phones = main_result.get("phones", [])

        # Discover members dynamically
        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} members")

        # Scrape each member page
        for member in members:
            print(f"    Scraping member: {member['name']}")
            result = await self.visit_page(member["url"], f"member_{member['name']}")

            if result.get("status") == "success":
                position = await self.detect_position_from_page(member["position"])

                photo_url = await self.extract_photo_url(member["name"], self.BASE_URL)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                # Get email
                member_email = None
                if result.get("emails"):
                    member_email = self.match_email_to_name(
                        member["name"],
                        result["emails"],
                        self.CITY_DOMAIN
                    )

                # Get district
                district = None
                text = await self.get_page_text()
                district_match = re.search(r'District\s+(\d+)', text, re.IGNORECASE)
                if district_match:
                    district = f"District {district_match.group(1)}"

                result_phones = result.get("phones", [])
                member_phone = result_phones[0] if result_phones else (main_phones[0] if main_phones else None)

                print(f"      Position: {position}")
                print(f"      District: {district or 'Not found'}")
                print(f"      Email: {member_email or 'Not found'}")

                self.add_council_member(
                    name=member["name"],
                    position=position,
                    district=district,
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
