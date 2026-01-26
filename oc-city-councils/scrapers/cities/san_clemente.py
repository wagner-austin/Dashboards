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
    YOUTUBE_CHANNEL = "https://www.youtube.com/channel/UCMJuEbFMmHeG8RBe-m6s7JQ"
    AGENDAS_URL = "https://www.sanclemente.gov/AgendaCenter/City-Council-13"

    # Known term dates - San Clemente transitioned to 4 districts + at-large mayor in 2024
    # Districts 3, 4 elected 2024 (term ends 2028)
    # Districts 1, 2 + Mayor at-large election 2026
    # Pre-2024 at-large members (Knoblock, Cabral, Enmeier) serving until 2026
    KNOWN_TERMS = {
        "rick loeffler": {"district": "District 3", "term_start": 2024, "term_end": 2028},
        "zhen wu": {"district": "District 4", "term_start": 2024, "term_end": 2028},
        "steve knoblock": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "victor cabral": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "mark enmeier": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
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
            "youtube": self.YOUTUBE_CHANNEL,
            "agendas": self.AGENDAS_URL,
        }

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

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st and 3rd Tuesdays",
            "meeting_time": "5:30 PM",
            "meeting_location": {
                "name": "City Council Chambers",
                "address": "910 Calle Negocio, 2nd Floor",
                "city_state_zip": "San Clemente, CA 92673"
            },
            "zoom": {},  # No Zoom - in-person only
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Cox", "channel": "854"}
            ],
            "live_stream": self.YOUTUBE_CHANNEL,
            "clerk": {
                "name": "Laura Campagnolo",
                "title": "City Clerk",
                "phone": "(949) 361-8301",
                "email": "campagnolol@san-clemente.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # No Zoom public comment
                "ecomment": False,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "campagnolol@san-clemente.org"
            },
            "portals": {
                "agenda_center": self.AGENDAS_URL,
                "youtube": self.YOUTUBE_CHANNEL,
                "live_stream": self.YOUTUBE_CHANNEL,
            },
            "council": {
                "size": 5,
                "districts": 4,  # 4 districts + at-large mayor
                "at_large": 1,  # Mayor is at-large (starting 2026)
                "mayor_elected": True,  # At-large mayor starting 2026 (2-year terms)
                "expanded_date": None,
                "notes": "4 districts + at-large mayor (2-year terms starting 2026)"
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["Mayor (At-Large)", "District 1", "District 2"],
                "term_length": 4,  # 4 years for council, 2 years for mayor
                "election_system": "mixed"
            }
        }
        return city_info

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

                # Get district and term info from KNOWN_TERMS
                member_info = self.get_member_info(member["name"])
                if member_info:
                    district = member_info.get("district")
                    term_start = member_info.get("term_start") or term_start
                    term_end = member_info.get("term_end") or term_end
                else:
                    district = None

                result_phones = result.get("phones", [])
                member_phone = result_phones[0] if result_phones else (main_phones[0] if main_phones else None)

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
                # Get term info even if page visit failed
                member_info = self.get_member_info(member["name"])
                self.add_council_member(
                    name=member["name"],
                    position="Councilmember",
                    profile_url=member["url"],
                    district=member_info.get("district") if member_info else None,
                    term_start=member_info.get("term_start") if member_info else None,
                    term_end=member_info.get("term_end") if member_info else None,
                )

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)

        # Scrape city-level info
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        return self.get_results()
