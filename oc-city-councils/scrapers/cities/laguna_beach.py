"""
Laguna Beach City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class LagunaBeachScraper(BaseScraper):
    """Laguna Beach - Granicus platform with dynamic member discovery."""

    CITY_NAME = "Laguna Beach"
    PLATFORM = "granicus"
    CITY_DOMAIN = "lagunabeachcity.net"
    BASE_URL = "https://www.lagunabeachcity.net"
    COUNCIL_URL = "https://www.lagunabeachcity.net/government/departments/city-council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """Discover council members dynamically from links on the council page."""
        members = []
        seen_names = set()

        try:
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or len(text) < 3:
                    continue

                href_lower = href.lower()

                # Look for council member profile links
                # Pattern: /government/departments/city-council/name-slug
                if "/government/departments/city-council/" not in href_lower:
                    continue

                # Skip the main council page and non-member pages
                skip_patterns = [
                    r'/city-council/?$',
                    r'/city-council/agendas',
                    r'/city-council/meetings',
                    r'/city-council/contact',
                    r'/city-council/calendar',
                    r'/city-council/priorities',
                    r'/city-council/rules',
                    r'/city-council/decorum',
                    r'/city-council/city-council-',  # Skip pages starting with city-council-
                ]
                if any(re.search(p, href_lower) for p in skip_patterns):
                    continue

                # Extract name from URL slug
                match = re.search(r'/city-council/([a-z]+-[a-z]+(?:-[a-z]+)?)/?$', href_lower)
                if not match:
                    continue

                name_slug = match.group(1)
                # Convert slug to name: "alex-rounaghi" -> "Alex Rounaghi"
                name = " ".join(word.title() for word in name_slug.split("-"))

                if name.lower() in seen_names:
                    continue
                seen_names.add(name.lower())

                full_url = urljoin(self.BASE_URL, href)

                members.append({
                    "name": name,
                    "position": "Councilmember",  # Will detect on individual page
                    "url": full_url,
                })
                print(f"      Found: {name}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def detect_position_from_page(self):
        """Detect position from page content."""
        try:
            # Check page title first
            title = await self.page.title()
            if title:
                title_lower = title.lower()
                if "mayor pro tem" in title_lower:
                    return "Mayor Pro Tem"
                elif "mayor" in title_lower:
                    return "Mayor"

            # Check page content for position near the top
            text = await self.get_page_text()
            # Look in first 1000 chars for position indicators
            first_part = text[:1000].lower()

            # Look for explicit position statements
            if re.search(r'\bmayor\s+pro\s+tem\b', first_part):
                return "Mayor Pro Tem"
            elif re.search(r'\bmayor\b', first_part) and "pro tem" not in first_part:
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

        print(f"    Found {len(members)} members")

        for member in members:
            print(f"    Scraping member: {member['name']}")
            result = await self.visit_page(member["url"], f"member_{member['name']}")

            if result.get("status") == "success":
                position = await self.detect_position_from_page()
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
                    position="Councilmember",
                    profile_url=member["url"],
                )

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()
