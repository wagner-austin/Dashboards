"""
Aliso Viejo City Council Scraper
Dynamically discovers council members, scrapes meeting archives from Granicus,
and extracts city-level info.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class AlisoViejoScraper(BaseScraper):
    """Aliso Viejo - CivicPlus platform with dynamic member discovery + Granicus meetings."""

    CITY_NAME = "Aliso Viejo"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "avcity.org"
    BASE_URL = "https://avcity.org"
    COUNCIL_URL = "https://avcity.org/222/City-Council"
    GRANICUS_URL = "https://alisoviejoca.granicus.com/ViewPublisher.php?view_id=3"

    # Known term dates - Aliso Viejo transitioned to by-district in 2024
    # Districts 1, 3, 5 elected 2024 (term ends 2028)
    # Districts 2, 4 elected 2022 at-large (term ends 2026)
    KNOWN_TERMS = {
        "max duncan": {"district": "District 2", "term_start": 2022, "term_end": 2026},
        "tiffany ackley": {"district": "District 4", "term_start": 2022, "term_end": 2026},
        "mike munzing": {"district": "District 5", "term_start": 2024, "term_end": 2028},
        "tim zandbergen": {"district": "District 1", "term_start": 2024, "term_end": 2028},
        "garrett dwyer": {"district": "District 3", "term_start": 2025, "term_end": 2028},  # Appointed to fill Hurt's vacancy
    }

    def get_member_info(self, name):
        """Get district and term info for a member."""
        name_lower = name.lower().strip()
        for known_name, info in self.KNOWN_TERMS.items():
            if known_name in name_lower or name_lower in known_name:
                return info
            known_last = known_name.split()[-1]
            if known_last in name_lower:
                return info
        return None

    def get_urls(self):
        return {
            "council": self.COUNCIL_URL,
            "granicus": self.GRANICUS_URL,
        }

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st and 3rd Wednesdays",
            "meeting_time": "7:00 PM",
            "meeting_location": {
                "name": "City Hall Council Chambers",
                "address": "12 Journey, Suite 100",
                "city_state_zip": "Aliso Viejo, CA 92656"
            },
            "zoom": {},  # No Zoom - in-person only
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Cox", "channel": "851"},
                {"provider": "AT&T U-Verse", "channel": "99"}
            ],
            "live_stream": self.GRANICUS_URL,
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(949) 425-2510",
                "email": "City-council@avcity.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # No Zoom participation
                "ecomment": False,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "City-council@avcity.org"
            },
            "portals": {
                "granicus": self.GRANICUS_URL,
                "ecomment": None,
                "live_stream": self.GRANICUS_URL,
            },
            "council": {
                "size": 5,
                "districts": 5,  # Transitioned to by-district in 2024
                "at_large": 0,
                "mayor_elected": False,  # Mayor rotates among council
                "expanded_date": None
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["District 2", "District 4"],
                "term_length": 4,
                "election_system": "by-district"
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

            for _ in range(5):
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
                    month_map = {'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Apr': 'April',
                                 'May': 'May', 'Jun': 'June', 'Jul': 'July', 'Aug': 'August',
                                 'Sep': 'September', 'Oct': 'October', 'Nov': 'November', 'Dec': 'December'}
                    if month_str in month_map:
                        month_str = month_map[month_str]
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
                            video_url = f"https://alisoviejoca.granicus.com/player/clip/{clip_match.group(1)}?view_id=3"

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

    async def discover_members(self):
        """Discover council members from profile links on main page."""
        members = []
        seen_urls = set()

        try:
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                text_lower = text.lower()

                # Look for position keywords in link text
                position = None
                if "mayor pro tem" in text_lower:
                    position = "Mayor Pro Tem"
                elif "mayor" in text_lower and "pro tem" not in text_lower:
                    position = "Mayor"
                elif "councilmember" in text_lower or "council member" in text_lower:
                    position = "Councilmember"

                if not position:
                    continue

                # Extract name (remove position prefix)
                name = text
                for prefix in ["Mayor Pro Tem", "Mayor", "Councilmember", "Council Member"]:
                    name = re.sub(rf"^{prefix}\s*", "", name, flags=re.IGNORECASE).strip()

                # Skip bad parses
                if len(name) < 3 or any(kw in name.lower() for kw in ["mayor", "council", "contact"]):
                    continue

                url = urljoin(self.BASE_URL, href)
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                members.append({"name": name, "position": position, "url": url})
                print(f"      Found: {position} {name}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} council members")

        for member in members:
            print(f"    Scraping member: {member['name']}")
            result = await self.visit_page(member["url"], f"member_{member['name']}")

            if result.get("status") == "success":
                photo_url = await self.extract_photo_url(member["name"], self.BASE_URL)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                member_email = None
                if result.get("emails"):
                    member_email = self.match_email_to_name(
                        member["name"], result["emails"], self.CITY_DOMAIN
                    )

                member_phone = result.get("phones", [None])[0] or (main_phones[0] if main_phones else None)

                # Use KNOWN_TERMS for district/term data
                member_info = self.get_member_info(member["name"])
                if member_info:
                    district = member_info.get("district")
                    term_start = member_info.get("term_start")
                    term_end = member_info.get("term_end")
                else:
                    district = None

                self.add_council_member(
                    name=member["name"],
                    position=member["position"],
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
                member_info = self.get_member_info(member["name"])
                self.add_council_member(
                    name=member["name"],
                    position=member["position"],
                    profile_url=member["url"],
                    district=member_info.get("district") if member_info else None,
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
