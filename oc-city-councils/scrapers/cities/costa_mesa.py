"""
Costa Mesa City Council Scraper
Dynamically discovers council members from website.
Note: May return 403 to direct requests - use Firefox with Playwright.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class CostaMesaScraper(BaseScraper):
    """Costa Mesa - Granicus platform (may block - use Firefox stealth)."""

    CITY_NAME = "Costa Mesa"
    PLATFORM = "granicus"
    CITY_DOMAIN = "costamesaca.gov"
    BASE_URL = "https://www.costamesaca.gov"
    COUNCIL_URL = "https://www.costamesaca.gov/government/mayor-city-council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """
        Discover council members from the main council page.
        Costa Mesa/Granicus pattern: Links to individual member pages.
        """
        members = []
        seen_urls = set()

        try:
            # Find all links that look like council member pages
            links = await self.page.query_selector_all('a[href*="mayor-city-council/"]')

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                # Skip navigation/generic links
                href_lower = href.lower()
                skip_url_patterns = [
                    "mailto:", "#", "javascript:", "calendar", "agenda", "minutes",
                    "goals", "objectives", "policies", "compensation", "contact",
                    "disclosures", "notices", "past-mayors", "public-notices"
                ]
                if any(skip in href_lower for skip in skip_url_patterns):
                    continue

                # Must be a member-specific URL with name pattern (mayor-, council-member-)
                if not re.search(r'/mayor-city-council/(mayor-[a-z]|council-member-[a-z])', href_lower):
                    continue

                # Normalize URL for deduplication
                full_url = urljoin(self.BASE_URL, href)

                # Skip duplicates
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Extract name from link text
                name = text.strip()

                # Skip if name looks like a navigation element
                skip_names = ["city council", "mayor", "contact", "meeting", "agenda", "more"]
                if name.lower() in skip_names:
                    continue

                # Clean up name - remove position prefix if present
                for prefix in ["Mayor Pro Tem", "Mayor", "Council Member", "Councilmember"]:
                    if name.lower().startswith(prefix.lower()):
                        name = name[len(prefix):].strip()

                if len(name) < 4:
                    continue

                # Determine position from URL/text
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

    async def detect_position_from_page(self, name):
        """Detect position from the current member's page."""
        try:
            # Most reliable: Check the URL pattern for the actual member path
            url = self.page.url.lower()
            # Extract just the last path segment (the member-specific part)
            path_parts = url.split('/')
            last_segment = path_parts[-1] if path_parts else ""

            if last_segment.startswith("mayor-pro-tem-"):
                return "Mayor Pro Tem"
            elif last_segment.startswith("mayor-") and "pro-tem" not in last_segment:
                return "Mayor"
            elif last_segment.startswith("council-member-"):
                return "Councilmember"

            # Check page title
            title = await self.page.title()
            title_lower = title.lower() if title else ""

            if "mayor pro tem" in title_lower:
                return "Mayor Pro Tem"
            elif "mayor" in title_lower and "pro tem" not in title_lower:
                return "Mayor"

            # Check h1 heading
            h1 = await self.page.query_selector("h1")
            if h1:
                h1_text = (await h1.inner_text()).lower()
                if "mayor pro tem" in h1_text:
                    return "Mayor Pro Tem"
                elif "mayor" in h1_text and "pro tem" not in h1_text:
                    return "Mayor"

        except Exception as e:
            self.results["errors"].append(f"detect_position: {str(e)}")

        return "Councilmember"

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        # Visit main council page
        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")

        if main_result.get("status") != "success":
            print(f"    ERROR: Could not access council page - {main_result.get('error')}")
            return self.get_results()

        main_phones = main_result.get("phones", [])

        # Discover members dynamically
        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    WARNING: No council members found on main page!")
            print("    Trying alternative discovery method...")
            # Try looking for any links with name patterns
            return self.get_results()

        print(f"    Found {len(members)} members")

        # Scrape each member page
        for member in members:
            print(f"    Scraping member: {member['name']}")
            result = await self.visit_page(member["url"], f"member_{member['name']}")

            if result.get("status") == "success":
                # Detect position from individual page (more accurate)
                position = await self.detect_position_from_page(member["name"])

                # Extract rich data
                photo_url = await self.extract_photo_url(member["name"], self.BASE_URL)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                # Get email from page using name matching
                member_email = None
                if result.get("emails"):
                    member_email = self.match_email_to_name(
                        member["name"],
                        result["emails"],
                        self.CITY_DOMAIN
                    )

                # Get district from page text
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
                # Page failed, add with basic info
                self.add_council_member(
                    name=member["name"],
                    position=member["position"],
                    profile_url=member["url"],
                )

        # Final email matching pass
        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()
