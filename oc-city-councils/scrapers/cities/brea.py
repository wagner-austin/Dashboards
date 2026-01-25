"""
Brea City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class BreaScraper(BaseScraper):
    """Brea - CivicPlus platform with Directory.aspx pattern."""

    CITY_NAME = "Brea"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cityofbrea.gov"
    BASE_URL = "https://www.cityofbrea.gov"
    COUNCIL_URL = "https://www.cityofbrea.gov/511/City-Council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """
        Discover council members from the main council page.
        Brea pattern: Directory.aspx?EID=X links for council members.
        Position is determined from individual member pages.
        """
        members = []
        seen_eids = set()

        try:
            # Find all Directory.aspx links
            links = await self.page.query_selector_all('a[href*="Directory.aspx?EID="]')

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                # Extract EID to avoid duplicates
                eid_match = re.search(r'EID=(\d+)', href)
                if not eid_match:
                    continue
                eid = eid_match.group(1)

                if eid in seen_eids:
                    continue

                # Skip non-council links (staff, etc.)
                skip_words = ["city manager", "clerk", "staff", "department", "director",
                              "assistant", "secretary", "administrator"]
                if any(w in text.lower() for w in skip_words):
                    continue

                name = text.strip()
                seen_eids.add(eid)
                url = urljoin(self.BASE_URL, href)

                # Position will be determined from individual page
                members.append({"name": name, "position": "Councilmember", "url": url})
                print(f"      Found: {name}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def detect_position_from_page(self):
        """
        Detect position (Mayor, Mayor Pro Tem, Councilmember) from current page.
        For Directory.aspx pages, the title appears in a specific location.
        """
        try:
            # Check page title first (most reliable)
            title = await self.page.title()
            title_lower = title.lower() if title else ""

            if "mayor pro tem" in title_lower:
                return "Mayor Pro Tem"
            elif "mayor" in title_lower and "pro tem" not in title_lower:
                return "Mayor"

            # For Directory pages, look for the Title field specifically
            # The structure is: Name, Department, Title, Contact info
            # Look for elements that might contain the title
            title_selectors = [
                ".directoryTitle",  # Common CivicPlus class
                ".staffTitle",
                ".position",
                "td:has-text('Title')",  # Table cell
            ]

            for selector in title_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for el in elements:
                        el_text = (await el.inner_text()).lower()
                        if "mayor pro tem" in el_text:
                            return "Mayor Pro Tem"
                        elif "mayor" in el_text and "pro tem" not in el_text and "council" not in el_text:
                            return "Mayor"
                except:
                    pass

            # Look for "Title: X" pattern used in Directory.aspx pages
            text = await self.get_page_text()
            lines = text.split('\n')

            for line in lines[:30]:  # Check first 30 lines
                line_lower = line.strip().lower()

                # Look for "Title: Mayor Pro Tem" or similar
                if line_lower.startswith("title:"):
                    title_value = line_lower.replace("title:", "").strip()
                    if "mayor pro tem" in title_value:
                        return "Mayor Pro Tem"
                    elif "mayor" in title_value and "pro tem" not in title_value:
                        return "Mayor"
                    elif "council" in title_value:
                        return "Councilmember"

                # Also check for exact standalone matches
                if line_lower == "mayor pro tem":
                    return "Mayor Pro Tem"
                elif line_lower == "mayor":
                    return "Mayor"
                elif line_lower in ["council member", "councilmember"]:
                    return "Councilmember"

            # Check h1/h2 headings
            headings = await self.page.query_selector_all("h1, h2")
            for h in headings:
                h_text = (await h.inner_text()).lower()
                if "mayor pro tem" in h_text:
                    return "Mayor Pro Tem"
                # Only match "mayor" if it's a standalone position, not part of bio
                elif h_text.strip() == "mayor":
                    return "Mayor"

        except Exception as e:
            self.results["errors"].append(f"detect_position: {str(e)}")

        return "Councilmember"

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

        print(f"    Found {len(members)} members")

        # Scrape each member page and detect position
        for member in members:
            print(f"    Scraping member: {member['name']}")
            result = await self.visit_page(member["url"], f"member_{member['name']}")

            if result.get("status") == "success":
                # Detect position from individual page
                position = await self.detect_position_from_page()
                member["position"] = position

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

                # Get phone
                member_phone = result.get("phones", [None])[0] or (main_phones[0] if main_phones else None)

                print(f"      Position: {position}")
                print(f"      Photo: {'Found' if photo_url else 'Not found'}")
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
                # Page failed, add with basic info
                self.add_council_member(
                    name=member["name"],
                    position="Councilmember",
                    profile_url=member["url"],
                )

        # Final email matching pass
        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()
