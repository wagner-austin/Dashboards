"""
Laguna Beach City Council Scraper
Dynamically discovers council members, scrapes meeting archives from Granicus,
and extracts city-level info.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class LagunaBeachScraper(BaseScraper):
    """Laguna Beach - Granicus platform with dynamic member discovery + meeting archive."""

    CITY_NAME = "Laguna Beach"
    PLATFORM = "granicus"
    CITY_DOMAIN = "lagunabeachcity.net"
    BASE_URL = "https://www.lagunabeachcity.net"
    COUNCIL_URL = "https://www.lagunabeachcity.net/government/departments/city-council"
    GRANICUS_URL = "https://lagunabeachcity.granicus.com/ViewPublisher.php?view_id=3"
    MEETINGS_URL = "https://www.lagunabeachcity.net/live-here/city-council/meetings-agendas-and-minutes"

    # Known term dates - Laguna Beach has 5 at-large seats, 4-year staggered terms
    # Mayor rotates annually among council
    KNOWN_TERMS = {
        "mark orgill": {"district": "At-Large", "term_start": 2024, "term_end": 2028, "position": "Mayor"},
        "bob whalen": {"district": "At-Large", "term_start": 2022, "term_end": 2026, "position": "Mayor Pro Tem"},
        "alex rounaghi": {"district": "At-Large", "term_start": 2024, "term_end": 2028, "position": "Councilmember"},
        "hallie jones": {"district": "At-Large", "term_start": 2024, "term_end": 2028, "position": "Councilmember"},
        "sue kempf": {"district": "At-Large", "term_start": 2022, "term_end": 2026, "position": "Councilmember"},
    }

    def get_member_info(self, name):
        """Get district, term, and position info for a member."""
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
            "meetings": self.MEETINGS_URL,
        }

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "2nd and 4th Tuesdays",
            "meeting_time": "5:00 PM",
            "meeting_location": {
                "name": "Council Chambers",
                "address": "505 Forest Avenue",
                "city_state_zip": "Laguna Beach, CA 92651"
            },
            "zoom": {},
            "phone_numbers": [],
            "tv_channels": [],
            "live_stream": self.GRANICUS_URL,
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(949) 497-0705",
                "email": "cityclerk@lagunabeachcity.net"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # Zoom discontinued after incident, not restored
                "ecomment": True,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "cityclerk@lagunabeachcity.net"
            },
            "portals": {
                "granicus": self.GRANICUS_URL,
                "ecomment": self.MEETINGS_URL,
                "live_stream": self.GRANICUS_URL,
            },
            "council": {
                "size": 5,
                "districts": 0,
                "at_large": 5,
                "mayor_elected": False,
                "expanded_date": None
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["Councilmember", "Councilmember"],
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
                            video_url = f"https://lagunabeachcity.granicus.com/player/clip/{clip_match.group(1)}?view_id=3"

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

                # Always use KNOWN_TERMS for district/term/position data
                member_info = self.get_member_info(member["name"])
                if member_info:
                    position = member_info.get("position", position)
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
                member_info = self.get_member_info(member["name"])
                self.add_council_member(
                    name=member["name"],
                    position=member_info.get("position", "Councilmember") if member_info else "Councilmember",
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
