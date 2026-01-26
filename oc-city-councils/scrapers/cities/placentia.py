"""
Placentia City Council Scraper
Dynamically discovers council members, scrapes meeting archives from Granicus,
and extracts city-level info.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class PlacentiaScraper(BaseScraper):
    """Placentia - CivicPlus with /ID/Position-Name-District-X URLs + Granicus meetings."""

    CITY_NAME = "Placentia"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "placentia.org"
    BASE_URL = "https://www.placentia.org"
    COUNCIL_URL = "https://www.placentia.org/268/Mayor-City-Council"
    GRANICUS_URL = "https://placentia.granicus.com/ViewPublisher.php?view_id=4"

    # Known term dates - Placentia has 5 by-district seats, 4-year staggered terms
    KNOWN_TERMS = {
        "chad wanke": {"district": "District 4", "term_start": 2024, "term_end": 2028},
        "chad p wanke": {"district": "District 4", "term_start": 2024, "term_end": 2028},
        "jeremy yamaguchi": {"district": "District 3", "term_start": 2024, "term_end": 2028},
        "jeremy b yamaguchi": {"district": "District 3", "term_start": 2024, "term_end": 2028},
        "ward smith": {"district": "District 5", "term_start": 2022, "term_end": 2026},
        "ward l smith": {"district": "District 5", "term_start": 2022, "term_end": 2026},
        "thomas hummer": {"district": "District 1", "term_start": 2022, "term_end": 2026},
        "kevin kirwin": {"district": "District 2", "term_start": 2024, "term_end": 2028},
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
            "granicus": self.GRANICUS_URL,
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
                "address": "401 E. Chapman Avenue",
                "city_state_zip": "Placentia, CA 92870"
            },
            "zoom": {},
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "AT&T U-Verse", "channel": "99"},
                {"provider": "Spectrum", "channel": "3"}
            ],
            "live_stream": self.GRANICUS_URL,
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(714) 993-8117",
                "email": None
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # No Zoom - live stream via Granicus/TV only
                "ecomment": True,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": None
            },
            "portals": {
                "granicus": self.GRANICUS_URL,
                "ecomment": None,
                "live_stream": self.GRANICUS_URL,
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
                            video_url = f"https://placentia.granicus.com/player/clip/{clip_match.group(1)}?view_id=4"

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
        """
        Discover council members from the main council page.
        Placentia URLs: /721/Councilmember-Thomas-Hummer-District-1
        """
        members = []
        seen_urls = set()
        seen_ids = set()

        try:
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or len(text) < 3:
                    continue

                if href.startswith(("mailto:", "javascript:", "#", "tel:")):
                    continue

                # Match URLs with council member patterns
                # /ID/Mayor-Name-District-X or /ID/Councilmember-Name-District-X
                href_lower = href.lower()
                if not re.search(r'/\d+/(mayor|councilmember)', href_lower):
                    continue

                # Skip meeting/archive pages
                if any(skip in href_lower for skip in ["archive", "meeting", "agenda"]):
                    continue

                full_url = urljoin(self.BASE_URL, href)
                # Normalize URL (ensure www. prefix)
                full_url = full_url.replace("://placentia.org", "://www.placentia.org")
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Skip main council page
                if "/268/" in full_url:
                    continue

                # Extract page ID and skip duplicates by ID
                id_match = re.search(r'/(\d+)/', full_url)
                if id_match:
                    page_id = id_match.group(1)
                    if page_id in seen_ids:
                        continue
                    seen_ids.add(page_id)

                # Extract position and name from URL
                # Pattern: /ID/Position-FirstName-MiddleInit-LastName-District-X
                match = re.search(r'/\d+/(Mayor(?:-Pro-Tem)?|Councilmember)-(.+?)(?:-District|$)', href, re.IGNORECASE)
                if not match:
                    continue

                position_raw = match.group(1).replace("-", " ").title()
                name_part = match.group(2).replace("-", " ").strip()

                # Clean up position
                if "pro tem" in position_raw.lower():
                    position = "Mayor Pro Tem"
                elif "mayor" in position_raw.lower():
                    position = "Mayor"
                else:
                    position = "Councilmember"

                # Clean name - remove trailing district info and truncated words
                name = re.sub(r'\s+distric.*$', '', name_part, flags=re.IGNORECASE).strip()
                name = re.sub(r'\s+district.*$', '', name, flags=re.IGNORECASE).strip()

                if len(name) < 3:
                    continue

                # Skip if name looks like a page title
                if name.lower() in ["city council", "mayor city council"]:
                    continue

                members.append({
                    "name": name,
                    "position": position,
                    "url": full_url,
                })
                print(f"      Found: {name} ({position})")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")

        if main_result.get("status") != "success":
            print(f"    ERROR: Could not access council page")
            return self.get_results()

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
                photo_url = await self.extract_photo_url(member["name"], self.BASE_URL)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                member_email = None
                if result.get("emails"):
                    # First try city domain email
                    member_email = self.match_email_to_name(
                        member["name"], result["emails"], self.CITY_DOMAIN
                    )
                    # Fall back to any email on member's page (some use personal domains)
                    if not member_email and len(result["emails"]) == 1:
                        member_email = result["emails"][0]

                result_phones = result.get("phones", [])
                member_phone = result_phones[0] if result_phones else (main_phones[0] if main_phones else None)

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
