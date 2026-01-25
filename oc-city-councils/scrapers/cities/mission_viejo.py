"""
Mission Viejo City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class MissionViejoScraper(BaseScraper):
    """Mission Viejo - Granicus-style with dynamic member discovery."""

    CITY_NAME = "Mission Viejo"
    PLATFORM = "granicus"
    CITY_DOMAIN = "cityofmissionviejo.org"
    BASE_URL = "https://www.cityofmissionviejo.org"
    COUNCIL_URL = "https://www.cityofmissionviejo.org/government/city-council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """Discover council members dynamically from the council page."""
        members = []
        seen_names = set()

        try:
            # Get all links on the page
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                # Skip non-relevant links
                if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                    continue

                # Look for council member profile links
                # Pattern 1: /departments/city-manager/name-slug
                # Pattern 2: /government/city-council/position-name
                href_lower = href.lower()
                if not any(pattern in href_lower for pattern in [
                    "/departments/city-manager/",
                    "/government/city-council/mayor",
                    "/government/city-council/council"
                ]):
                    continue

                # Skip staff/department links
                skip_patterns = ["agenda", "meeting", "minute", "archive", "contact",
                                 "city-manager$", "city-council$"]
                if any(re.search(p, href_lower) for p in skip_patterns):
                    continue

                # Extract name from URL or link text
                name = None
                position = "Councilmember"

                # Try to get name from URL path
                path_match = re.search(r'/([a-z]+-[a-z]+(?:-[a-z]+)?)/?$', href_lower)
                if path_match:
                    name_slug = path_match.group(1)
                    # Remove position prefixes
                    name_slug = re.sub(r'^(mayor-pro-tem-|mayor-|council-member-)', '', name_slug)
                    # Convert slug to name: "wendy-bucknum" -> "Wendy Bucknum"
                    name = " ".join(word.title() for word in name_slug.split("-"))

                # Detect position from URL
                if "mayor-pro-tem" in href_lower:
                    position = "Mayor Pro Tem"
                elif "mayor" in href_lower and "pro-tem" not in href_lower:
                    position = "Mayor"

                if not name or len(name) < 3:
                    continue

                # Skip if already seen
                if name.lower() in seen_names:
                    continue
                seen_names.add(name.lower())

                # Build full URL
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
        """Detect position from page content."""
        try:
            text = await self.get_page_text()
            text_lower = text.lower()

            # Look for position in page content
            if re.search(r'\bmayor\s+pro\s+tem\b', text_lower):
                return "Mayor Pro Tem"
            elif re.search(r'\bmayor\b(?!\s+pro)', text_lower[:500]):
                # Check first 500 chars for "Mayor" not followed by "Pro"
                if "mayor pro tem" not in text_lower[:500]:
                    return "Mayor"

        except Exception:
            pass
        return "Councilmember"

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_emails = main_result.get("emails", [])
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
                # Try to detect position from individual page
                page_position = await self.detect_position_from_page()
                position = page_position if page_position != "Councilmember" else member["position"]

                photo_url = await self.extract_photo_url(member["name"], self.BASE_URL)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                # Get email from member page or main page
                member_email = None
                page_emails = result.get("emails", [])
                if page_emails:
                    member_email = self.match_email_to_name(
                        member["name"], page_emails, self.CITY_DOMAIN
                    )
                    # Fallback: if only one email on page, use it
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
