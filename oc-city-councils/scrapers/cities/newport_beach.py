"""
Newport Beach City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class NewportBeachScraper(BaseScraper):
    """Newport Beach - Granicus with district-based profile pages."""

    CITY_NAME = "Newport Beach"
    PLATFORM = "granicus"
    CITY_DOMAIN = "newportbeachca.gov"
    BASE_URL = "https://www.newportbeachca.gov"
    COUNCIL_URL = "https://www.newportbeachca.gov/government/city-council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """Discover council members from district page links."""
        members = []
        seen_districts = set()

        try:
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href:
                    continue

                href_lower = href.lower()

                # Look for district profile links
                # Pattern: /find-your-council-district/district-X
                match = re.search(r'/find-your-council-district/(district-\d+)', href_lower)
                if not match:
                    continue

                district = match.group(1)
                if district in seen_districts:
                    continue
                seen_districts.add(district)

                full_url = urljoin(self.BASE_URL, href)

                # District number for reference
                district_num = re.search(r'district-(\d+)', district).group(1)

                members.append({
                    "district": f"District {district_num}",
                    "position": "Councilmember",  # Will detect Mayor/MPT on page
                    "url": full_url,
                })
                print(f"      Found: District {district_num}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        # Sort by district number
        members.sort(key=lambda m: int(re.search(r'\d+', m["district"]).group()))
        return members

    async def extract_member_name_from_page(self):
        """Extract the council member's name from their profile page."""
        try:
            # Try to find name in page title
            title = await self.page.title()
            if title:
                # Title might be like "District 1 - Joe Stapleton | Newport Beach"
                name_match = re.search(r'District\s+\d+\s*[-–]\s*([^|]+)', title)
                if name_match:
                    return name_match.group(1).strip()

            # Try to find name in h1 or h2 headers
            for selector in ["h1", "h2", ".council-member-name", ".member-name"]:
                elements = await self.page.query_selector_all(selector)
                for el in elements:
                    text = (await el.inner_text()).strip()
                    # Look for a name pattern (First Last)
                    if re.match(r'^[A-Z][a-z]+\s+[A-Z]', text) and len(text) < 50:
                        # Clean up any titles
                        name = re.sub(r'^(Mayor|Council\s*Member|Mayor Pro Tem)\s+', '', text, flags=re.IGNORECASE)
                        return name.strip()

            # Try extracting from page content
            text = await self.get_page_text()
            # Look for name pattern near the top
            first_500 = text[:500]
            name_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)\b', first_500)
            if name_match:
                return name_match.group(1)

        except Exception:
            pass
        return None

    async def detect_position_from_page(self):
        """Detect position from page content."""
        try:
            title = await self.page.title()
            if title:
                title_lower = title.lower()
                if "mayor pro tem" in title_lower:
                    return "Mayor Pro Tem"
                elif "mayor" in title_lower:
                    return "Mayor"

            text = await self.get_page_text()
            first_1000 = text[:1000].lower()

            if re.search(r'\bmayor\s+pro\s+tem\b', first_1000):
                return "Mayor Pro Tem"
            elif re.search(r'\bmayor\b', first_1000) and "pro tem" not in first_1000:
                return "Mayor"

        except Exception:
            pass
        return "Councilmember"

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} districts")

        for member in members:
            print(f"    Scraping: {member['district']}")
            result = await self.visit_page(member["url"], f"member_{member['district']}")

            if result.get("status") == "success":
                # Extract name from the district page
                name = await self.extract_member_name_from_page()
                if not name:
                    print(f"      WARNING: Could not extract name for {member['district']}")
                    continue

                position = await self.detect_position_from_page()
                photo_url = await self.extract_photo_url(name, self.BASE_URL)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                member_email = None
                page_emails = result.get("emails", [])
                if page_emails:
                    member_email = self.match_email_to_name(
                        name, page_emails, self.CITY_DOMAIN
                    )
                    if not member_email and len(page_emails) == 1:
                        member_email = page_emails[0]

                result_phones = result.get("phones", [])
                member_phone = result_phones[0] if result_phones else (main_phones[0] if main_phones else None)

                self.add_council_member(
                    name=name,
                    position=position,
                    district=member["district"],
                    email=member_email,
                    phone=member_phone,
                    profile_url=member["url"],
                    photo_url=photo_url,
                    bio=bio,
                    term_start=term_start,
                    term_end=term_end,
                )

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()
