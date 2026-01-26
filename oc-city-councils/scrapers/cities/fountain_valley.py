"""
Fountain Valley City Council Scraper
Dynamically discovers council members from website.
Scrapes meeting archives from Granicus portal.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class FountainValleyScraper(BaseScraper):
    """Fountain Valley - CivicPlus with Directory.aspx pattern + Granicus meetings."""

    CITY_NAME = "Fountain Valley"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "fountainvalley.gov"
    BASE_URL = "https://www.fountainvalley.gov"
    COUNCIL_URL = "https://www.fountainvalley.gov/156/City-Council"
    # Note: Fountain Valley's Granicus is not publicly accessible without login
    # Videos are available through the Agenda Center by clicking TV icons
    GRANICUS_URL = "https://fountainvalley.granicus.com/"  # Requires login for full access
    AGENDA_CENTER_URL = "https://www.fountainvalley.gov/AgendaCenter/City-Council-2"

    # Known term dates - Fountain Valley is at-large
    # 2 seats elected 2020, re-elected 2024 (term ends 2028)
    # 3 seats elected 2022 (term ends 2026)
    KNOWN_TERMS = {
        "ted bui": {"term_start": 2024, "term_end": 2028},
        "glenn grandis": {"term_start": 2024, "term_end": 2028},
        "jim cunneen": {"term_start": 2022, "term_end": 2026},
        "kim constantine": {"term_start": 2022, "term_end": 2026},
        "patrick harper": {"term_start": 2022, "term_end": 2026},
    }

    def get_member_info(self, name):
        """Get term info for a member."""
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
            "granicus": self.GRANICUS_URL,
        }

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

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st and 3rd Tuesdays",
            "meeting_time": "6:00 PM",
            "meeting_location": {
                "name": "Council Chambers, City Hall",
                "address": "10200 Slater Avenue",
                "city_state_zip": "Fountain Valley, CA 92708"
            },
            "zoom": {
                "meeting_id": "851 5107 5391",
                "passcode": "883147",
                "url": "https://bit.ly/4kDYQHD"
            },
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Local Cable", "channel": "3"}
            ],
            "live_stream": "https://www.fountainvalley.gov/213/Watch-FV-Television",
            "clerk": {
                "name": "Rick Miller",
                "title": "City Clerk",
                "phone": "(714) 593-4400",
                "email": "Rick.Miller@fountainvalley.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": True,  # Zoom participation available
                "ecomment": False,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "Rick.Miller@fountainvalley.org"
            },
            "portals": {
                "agenda_center": self.AGENDA_CENTER_URL,
                "live_stream": "https://www.fountainvalley.gov/213/Watch-FV-Television",
            },
            "council": {
                "size": 5,
                "districts": 0,
                "at_large": 5,
                "mayor_elected": False,  # Mayor rotates among council
                "expanded_date": None
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["At-Large (3 seats)"],
                "term_length": 4,
                "election_system": "at-large"
            }
        }
        return city_info

    async def scrape_meetings(self):
        """Scrape meeting data from Granicus portal."""
        meetings = []
        seen_keys = set()

        print(f"    Scraping meetings from Granicus...")

        try:
            await self.page.goto(self.GRANICUS_URL, timeout=60000, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # Scroll to load more meetings
            for _ in range(3):
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.page.wait_for_timeout(500)

            agenda_links = await self.page.query_selector_all('a[href*="AgendaViewer"], a[href*="GeneratedAgendaViewer"]')
            print(f"      Found {len(agenda_links)} agenda links")

            for link in agenda_links:
                try:
                    row = await link.evaluate_handle("el => el.closest('tr')")
                    if not row:
                        continue
                    row_el = row.as_element()
                    if not row_el:
                        continue

                    row_text = await row_el.inner_text()
                    if "CITY COUNCIL" not in row_text.upper():
                        continue

                    row_text_clean = row_text.replace('\xa0', ' ')
                    date_match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", row_text_clean)
                    if not date_match:
                        continue

                    month_str, day_str, year_str = date_match.groups()
                    date_str = f"{month_str} {day_str}, {year_str}"

                    lines = [l.strip() for l in row_text.split('\n') if l.strip()]
                    name_text = re.sub(r'\s+', ' ', lines[0] if lines else "City Council Meeting").strip()[:100]

                    agenda_url = await link.get_attribute("href")
                    if agenda_url and agenda_url.startswith("//"):
                        agenda_url = "https:" + agenda_url

                    minutes_link = await row_el.query_selector('a[href*="MinutesViewer"]')
                    minutes_url = None
                    if minutes_link:
                        minutes_url = await minutes_link.get_attribute("href")
                        if minutes_url and minutes_url.startswith("//"):
                            minutes_url = "https:" + minutes_url

                    video_url = None
                    if agenda_url:
                        clip_match = re.search(r"clip_id=(\d+)", agenda_url)
                        if clip_match:
                            video_url = f"https://fountainvalley.granicus.com/player/clip/{clip_match.group(1)}?view_id=1"

                    event_id = None
                    if agenda_url:
                        event_match = re.search(r"event_id=(\d+)", agenda_url)
                        if event_match:
                            event_id = event_match.group(1)

                    key = f"{date_str}|{event_id or agenda_url}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    meetings.append({
                        "name": name_text, "date": date_str, "agenda_url": agenda_url,
                        "minutes_url": minutes_url, "video_url": video_url, "event_id": event_id
                    })
                except Exception:
                    continue

            def parse_date(d):
                try:
                    return datetime.strptime(d, "%B %d, %Y")
                except ValueError:
                    return datetime.min
            meetings.sort(key=lambda m: parse_date(m["date"]), reverse=True)
            print(f"      Found {len(meetings)} City Council meetings")

        except Exception as e:
            self.results["errors"].append(f"scrape_meetings: {str(e)}")

        return meetings

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

                # Use KNOWN_TERMS for reliable term data
                member_info = self.get_member_info(member["name"])
                if member_info:
                    term_start = member_info.get("term_start") or term_start
                    term_end = member_info.get("term_end") or term_end

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
                # Get term info even if page visit failed
                member_info = self.get_member_info(member["name"])
                self.add_council_member(
                    name=member["name"],
                    position="Councilmember",
                    profile_url=member["url"],
                    term_start=member_info.get("term_start") if member_info else None,
                    term_end=member_info.get("term_end") if member_info else None,
                )

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)

        # Scrape city-level info
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        # Scrape meetings from Granicus
        meetings = await self.scrape_meetings()
        self.results["meetings"] = meetings

        return self.get_results()
