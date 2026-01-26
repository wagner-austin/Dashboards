"""
Brea City Council Scraper
Dynamically discovers council members from website.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class BreaScraper(BaseScraper):
    """Brea - CivicPlus platform with Directory.aspx pattern + Swagit meetings."""

    CITY_NAME = "Brea"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cityofbrea.gov"
    BASE_URL = "https://www.cityofbrea.gov"
    COUNCIL_URL = "https://www.cityofbrea.gov/511/City-Council"
    MEETINGS_URL = "https://www.cityofbrea.gov/509/Meeting-Agendas-Minutes"
    SWAGIT_URL = "https://breaca.new.swagit.com/videos"

    # Known term dates - Brea has 5 by-district seats, 4-year staggered terms
    KNOWN_TERMS = {
        "cecilia hupp": {"district": "District 1", "term_start": 2022, "term_end": 2026},
        "marty simonoff": {"district": "District 2", "term_start": 2024, "term_end": 2028},
        "blair stewart": {"district": "District 3", "term_start": 2024, "term_end": 2028},
        "christine marick": {"district": "District 4", "term_start": 2024, "term_end": 2028},
        "steven vargas": {"district": "District 5", "term_start": 2022, "term_end": 2026},
    }

    def get_member_info(self, name):
        """Get district and term info for a member."""
        name_lower = name.lower().strip()
        for known_name, info in self.KNOWN_TERMS.items():
            if known_name in name_lower or name_lower in known_name:
                return info
            # Check last name match
            known_last = known_name.split()[-1]
            if known_last in name_lower:
                return info
        return None

    def get_urls(self):
        return {
            "council": self.COUNCIL_URL,
            "meetings": self.MEETINGS_URL,
            "swagit": self.SWAGIT_URL,
        }

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st and 3rd Tuesdays",
            "meeting_time": "7:00 PM",
            "meeting_location": {
                "name": "City Council Chambers",
                "address": "1 Civic Center Circle",
                "city_state_zip": "Brea, CA 92821"
            },
            "zoom": {},
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Spectrum", "channel": "3"},
                {"provider": "AT&T U-Verse", "channel": "99"}
            ],
            "live_stream": self.SWAGIT_URL,
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(714) 990-7756",
                "email": None
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,
                "ecomment": False,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": None
            },
            "portals": {
                "granicus": None,
                "ecomment": None,
                "live_stream": self.SWAGIT_URL,
            },
            "council": {
                "size": 5,
                "districts": 5,
                "at_large": 0,
                "mayor_elected": False,
                "expanded_date": None
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["District 1", "District 5"],
                "term_length": 4,
                "election_system": "by-district"
            }
        }

        return city_info

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

                # Always use KNOWN_TERMS for district/term data
                member_info = self.get_member_info(member["name"])
                if member_info:
                    district = member_info.get("district")
                    term_start = member_info.get("term_start")
                    term_end = member_info.get("term_end")
                else:
                    district = None

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
                # Page failed, add with basic info from KNOWN_TERMS
                member_info = self.get_member_info(member["name"])
                self.add_council_member(
                    name=member["name"],
                    position="Councilmember",
                    profile_url=member["url"],
                    district=member_info.get("district") if member_info else None,
                    term_start=member_info.get("term_start") if member_info else None,
                    term_end=member_info.get("term_end") if member_info else None,
                )

        # Final email matching pass
        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)

        # Scrape city-level info
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        return self.get_results()
