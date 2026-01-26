"""
Mission Viejo City Council Scraper
Dynamically discovers council members, scrapes meeting archives from Granicus,
and extracts city-level info (meeting schedule, Zoom, public comment, clerk).
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class MissionViejoScraper(BaseScraper):
    """Mission Viejo - Granicus-style with dynamic member discovery + meeting archive."""

    CITY_NAME = "Mission Viejo"
    PLATFORM = "granicus"
    CITY_DOMAIN = "cityofmissionviejo.org"
    BASE_URL = "https://www.cityofmissionviejo.org"
    COUNCIL_URL = "https://www.cityofmissionviejo.org/government/city-council"
    GRANICUS_URL = "https://missionviejo.granicus.com/ViewPublisher.php?view_id=12"
    AGENDA_ONLINE_URL = "https://dms.cityofmissionviejo.org/OnBaseAgendaOnline"

    # Known term dates - Mission Viejo has 5 at-large seats, 4-year staggered terms
    KNOWN_TERMS = {
        "trish kelley": {"district": "At-Large", "term_start": 2022, "term_end": 2026, "position": "Mayor"},
        "wendy bucknum": {"district": "At-Large", "term_start": 2022, "term_end": 2026, "position": "Mayor Pro Tem"},
        "brian goodell": {"district": "At-Large", "term_start": 2024, "term_end": 2028, "position": "Councilmember"},
        "bob ruesch": {"district": "At-Large", "term_start": 2022, "term_end": 2026, "position": "Councilmember"},
        "cynthia vasquez": {"district": "At-Large", "term_start": 2024, "term_end": 2028, "position": "Councilmember"},
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
            "agenda_online": self.AGENDA_ONLINE_URL,
        }

    async def discover_members(self):
        """Discover council members dynamically from the council page."""
        members = []
        seen_names = set()

        try:
            # Get all links on the page
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                # Skip non-relevant links
                if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                    continue

                # Look for council member profile links
                # Pattern 1: /departments/city-manager/name-slug
                # Pattern 2: /government/city-council/position-name
                href_lower = href.lower()
                if not any(pattern in href_lower for pattern in [
                    "/departments/city-manager/",
                    "/government/city-council/mayor",
                    "/government/city-council/council"
                ]):
                    continue

                # Skip staff/department links
                skip_patterns = ["agenda", "meeting", "minute", "archive", "contact",
                                 "city-manager$", "city-council$"]
                if any(re.search(p, href_lower) for p in skip_patterns):
                    continue

                # Extract name from URL or link text
                name = None
                position = "Councilmember"

                # Try to get name from URL path
                path_match = re.search(r'/([a-z]+-[a-z]+(?:-[a-z]+)?)/?$', href_lower)
                if path_match:
                    name_slug = path_match.group(1)
                    # Remove position prefixes
                    name_slug = re.sub(r'^(mayor-pro-tem-|mayor-|council-member-)', '', name_slug)
                    # Convert slug to name: "wendy-bucknum" -> "Wendy Bucknum"
                    name = " ".join(word.title() for word in name_slug.split("-"))

                # Detect position from URL
                if "mayor-pro-tem" in href_lower:
                    position = "Mayor Pro Tem"
                elif "mayor" in href_lower and "pro-tem" not in href_lower:
                    position = "Mayor"

                if not name or len(name) < 3:
                    continue

                # Skip if already seen
                if name.lower() in seen_names:
                    continue
                seen_names.add(name.lower())

                # Build full URL
                full_url = urljoin(self.BASE_URL, href)

                members.append({
                    "name": name,
                    "position": position,
                    "url": full_url,
                })
                print(f"      Found: {name} ({position})")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st and 3rd Mondays",
            "meeting_time": "5:00 PM",
            "meeting_location": {
                "name": "City Hall Council Chamber",
                "address": "200 Civic Center",
                "city_state_zip": "Mission Viejo, CA 92691"
            },
            "zoom": {},
            "phone_numbers": [],
            "tv_channels": [],
            "live_stream": "https://missionviejo.granicus.com/ViewPublisher.php?view_id=12",
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(949) 470-3050",
                "email": "citycouncil@cityofmissionviejo.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # No Zoom - written comments via email only
                "ecomment": True,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "citycouncil@cityofmissionviejo.org"
            },
            "portals": {
                "granicus": self.GRANICUS_URL,
                "ecomment": self.AGENDA_ONLINE_URL,
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
                "seats_up": ["Mayor", "Mayor Pro Tem", "Councilmember"],
                "term_length": 4,
                "election_system": "at-large"
            }
        }

        # Scrape Zoom info from latest agenda
        print("    Scraping Zoom info from agenda...")
        try:
            await self.page.goto(self.GRANICUS_URL, timeout=60000, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # Find first agenda link
            agenda_link = await self.page.query_selector('a[href*="AgendaViewer"]')
            if agenda_link:
                agenda_url = await agenda_link.get_attribute("href")
                if agenda_url:
                    if agenda_url.startswith("//"):
                        agenda_url = "https:" + agenda_url
                    await self.page.goto(agenda_url, timeout=30000)
                    await self.page.wait_for_timeout(2000)
                    agenda_text = await self.page.inner_text("body")

                    # Zoom meeting ID
                    zoom_id_match = re.search(r"(?:Meeting ID|Webinar ID)[:\s]*(\d{3}[-\s]?\d{3,4}[-\s]?\d{3,4})", agenda_text, re.I)
                    if zoom_id_match:
                        zoom_id = zoom_id_match.group(1).replace(" ", "-").replace("--", "-")
                        if 9 <= len(zoom_id.replace("-", "")) <= 11:
                            city_info["zoom"]["meeting_id"] = zoom_id

                    # Zoom passcode
                    passcode_match = re.search(r"(?:passcode|password)[:\s]*([A-Za-z0-9]{6,})", agenda_text, re.I)
                    if passcode_match:
                        passcode = passcode_match.group(1)
                        if passcode.lower() not in ["passcode", "password", "meeting", "webinar", "public", "comment", "below"]:
                            city_info["zoom"]["passcode"] = passcode

                    # Zoom URL
                    zoom_url_match = re.search(r"(https?://(?:us\d*\.)?zoom(?:gov)?\.(?:us|com)/[jw]/\d+[^\s\"'<>]*)", agenda_text)
                    if zoom_url_match:
                        city_info["zoom"]["url"] = zoom_url_match.group(1).rstrip(",.")

                    # Phone dial-in
                    phone_matches = re.findall(r"\+?1?[-\s]?(\d{3})[-\s]?(\d{3})[-\s]?(\d{4})", agenda_text)
                    for area, mid, last in phone_matches:
                        phone = f"{area}-{mid}-{last}"
                        if phone not in city_info["phone_numbers"] and area not in ["000", "123"]:
                            if area.startswith(("669", "833", "888", "877")):
                                city_info["phone_numbers"].append(phone)

        except Exception as e:
            self.results["errors"].append(f"scrape_zoom_info: {str(e)}")

        return city_info

    async def scrape_meetings(self):
        """Scrape meeting data from Granicus portal."""
        meetings = []
        seen_keys = set()

        print(f"    Scraping meetings from Granicus...")

        try:
            await self.page.goto(self.GRANICUS_URL, timeout=60000, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # Scroll to load content
            for _ in range(5):
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.page.wait_for_timeout(500)

            # Get all agenda links
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

                    # Filter for City Council meetings
                    if "CITY COUNCIL" not in row_text.upper():
                        continue

                    # Parse date
                    row_text_clean = row_text.replace('\xa0', ' ')
                    date_match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", row_text_clean)
                    if not date_match:
                        continue

                    month_str = date_match.group(1)
                    day_str = date_match.group(2)
                    year_str = date_match.group(3)

                    month_map = {
                        'Jan': 'January', 'Feb': 'February', 'Mar': 'March',
                        'Apr': 'April', 'May': 'May', 'Jun': 'June',
                        'Jul': 'July', 'Aug': 'August', 'Sep': 'September',
                        'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
                    }
                    if month_str in month_map:
                        month_str = month_map[month_str]

                    date_str = f"{month_str} {day_str}, {year_str}"

                    # Get meeting name
                    lines = [l.strip() for l in row_text.split('\n') if l.strip()]
                    name_text = lines[0] if lines else "City Council Meeting"
                    name_text = re.sub(r'\s+', ' ', name_text).strip()[:100]

                    # Get URLs
                    agenda_url = await link.get_attribute("href")
                    if agenda_url and agenda_url.startswith("//"):
                        agenda_url = "https:" + agenda_url

                    minutes_link = await row_el.query_selector('a[href*="MinutesViewer"]')
                    minutes_url = None
                    if minutes_link:
                        minutes_url = await minutes_link.get_attribute("href")
                        if minutes_url and minutes_url.startswith("//"):
                            minutes_url = "https:" + minutes_url

                    # Video URL
                    video_url = None
                    if agenda_url:
                        clip_match = re.search(r"clip_id=(\d+)", agenda_url)
                        if clip_match:
                            video_url = f"https://missionviejo.granicus.com/player/clip/{clip_match.group(1)}?view_id=12"

                    # Deduplicate
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
                        "name": name_text,
                        "date": date_str,
                        "agenda_url": agenda_url,
                        "minutes_url": minutes_url,
                        "video_url": video_url,
                        "event_id": event_id
                    })

                except Exception:
                    continue

            # Sort by date
            def parse_date(date_str):
                try:
                    return datetime.strptime(date_str, "%B %d, %Y")
                except ValueError:
                    return datetime.min

            meetings.sort(key=lambda m: parse_date(m["date"]), reverse=True)
            print(f"      Found {len(meetings)} City Council meetings")

        except Exception as e:
            self.results["errors"].append(f"scrape_meetings: {str(e)}")
            print(f"      ERROR scraping meetings: {e}")

        return meetings

    async def detect_position_from_page(self):
        """Detect position from page content."""
        try:
            text = await self.get_page_text()
            text_lower = text.lower()

            # Look for position in page content
            if re.search(r'\bmayor\s+pro\s+tem\b', text_lower):
                return "Mayor Pro Tem"
            elif re.search(r'\bmayor\b(?!\s+pro)', text_lower[:500]):
                # Check first 500 chars for "Mayor" not followed by "Pro"
                if "mayor pro tem" not in text_lower[:500]:
                    return "Mayor"

        except Exception:
            pass
        return "Councilmember"

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_emails = main_result.get("emails", [])
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
                # Try to detect position from individual page
                page_position = await self.detect_position_from_page()
                position = page_position if page_position != "Councilmember" else member["position"]

                photo_url = await self.extract_photo_url(member["name"], self.BASE_URL)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                # Get email from member page or main page
                member_email = None
                page_emails = result.get("emails", [])
                if page_emails:
                    member_email = self.match_email_to_name(
                        member["name"], page_emails, self.CITY_DOMAIN
                    )
                    # Fallback: if only one email on page, use it
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
                    position=member_info.get("position", "Councilmember") if member_info else member["position"],
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
