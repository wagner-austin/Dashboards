"""
Fountain Valley City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class FountainValleyScraper(BaseScraper):
    """Fountain Valley - CivicPlus with Directory.aspx pattern."""

    CITY_NAME = "Fountain Valley"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "fountainvalley.gov"
    BASE_URL = "https://www.fountainvalley.gov"
    COUNCIL_URL = "https://www.fountainvalley.gov/156/City-Council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """Discover council members from the main council page."""
        members = []
        seen_eids = set()

        try:
            links = await self.page.query_selector_all('a[href*="Directory.aspx?EID="], a[href*="directory.aspx?EID="]')

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                eid_match = re.search(r'EID=(\d+)', href, re.IGNORECASE)
                if not eid_match:
                    continue

                eid = eid_match.group(1)
                if eid in seen_eids:
                    continue

                skip_words = ["city manager", "clerk", "staff", "department"]
                if any(w in text.lower() for w in skip_words):
                    continue

                seen_eids.add(eid)
                url = urljoin(self.BASE_URL, f"/Directory.aspx?EID={eid}")

                # Clean name - remove trailing commas/punctuation
                name = text.strip().rstrip(",.")

                members.append({
                    "name": name,
                    "position": "Councilmember",
                    "url": url,
                })
                print(f"      Found: {name}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def detect_position_from_page(self):
        """Detect position from current page."""
        try:
            title = await self.page.title()
            if title:
                title_lower = title.lower()
                if "mayor pro tem" in title_lower or "vice mayor" in title_lower:
                    return "Mayor Pro Tem"
                elif "mayor" in title_lower:
                    return "Mayor"

            text = await self.get_page_text()
            first_lines = text[:500].lower()
            if "mayor pro tem" in first_lines or "vice mayor" in first_lines:
                return "Mayor Pro Tem"
            elif "mayor" in first_lines and "pro tem" not in first_lines:
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

                print(f"      Position: {position}")
                print(f"      Email: {member_email or 'Not found'}")

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
