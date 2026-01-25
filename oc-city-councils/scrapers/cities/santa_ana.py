"""
Santa Ana City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class SantaAnaScraper(BaseScraper):
    """Santa Ana - WordPress-style with /contacts/name-slug/ URLs."""

    CITY_NAME = "Santa Ana"
    PLATFORM = "wordpress"
    CITY_DOMAIN = "santa-ana.org"
    BASE_URL = "https://www.santa-ana.org"
    COUNCIL_URL = "https://www.santa-ana.org/city-council-members/"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """Discover council members from /contacts/ links."""
        members = []
        seen_urls = set()

        try:
            links = await self.page.query_selector_all('a[href*="/contacts/"]')

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                # Must be a council member contact page
                if "/contacts/" not in href:
                    continue

                # Skip navigation/generic links
                if any(skip in href.lower() for skip in ["category", "page", "search"]):
                    continue

                full_url = urljoin(self.BASE_URL, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Use link text as name
                name = text.strip()

                # Skip if name looks generic
                skip_names = ["contact", "email", "phone", "more", "view"]
                if name.lower() in skip_names:
                    continue

                # Initial position guess
                position = "Councilmember"

                members.append({
                    "name": name,
                    "position": position,
                    "url": full_url,
                })
                print(f"      Found: {name}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def detect_position_from_page(self):
        """Detect position from page content."""
        try:
            title = await self.page.title()
            if title:
                title_lower = title.lower()
                if "mayor pro tem" in title_lower:
                    return "Mayor Pro Tem"
                elif "mayor" in title_lower and "pro tem" not in title_lower:
                    return "Mayor"

            text = await self.get_page_text()
            first_1000 = text[:1000].lower()
            if "mayor pro tem" in first_1000:
                return "Mayor Pro Tem"
            elif "mayor" in first_1000 and "pro tem" not in first_1000:
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
                if result.get("emails"):
                    member_email = self.match_email_to_name(
                        member["name"], result["emails"], self.CITY_DOMAIN
                    )

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
