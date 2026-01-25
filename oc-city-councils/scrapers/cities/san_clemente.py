"""
San Clemente City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class SanClementeScraper(BaseScraper):
    """San Clemente - CivicPlus with Directory.aspx?EID=X URLs."""

    CITY_NAME = "San Clemente"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "san-clemente.org"
    BASE_URL = "https://www.sanclemente.gov"
    COUNCIL_URL = "https://www.sanclemente.gov/159/City-Council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """Discover council members from Directory.aspx links."""
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
                name = text.strip().rstrip(",.")

                # Convert "Last, First" to "First Last"
                if ", " in name:
                    parts = name.split(", ", 1)
                    name = f"{parts[1]} {parts[0]}"

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
        """Detect position from page content.

        San Clemente uses "Title: Mayor" format on Directory.aspx pages.
        """
        try:
            text = await self.get_page_text()
            text_lower = text.lower()

            # Look for explicit "Title: X" format
            if re.search(r'title:\s*mayor\s+pro\s+tem', text_lower):
                return "Mayor Pro Tem"
            elif re.search(r'title:\s*mayor(?!\s+pro)', text_lower):
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
