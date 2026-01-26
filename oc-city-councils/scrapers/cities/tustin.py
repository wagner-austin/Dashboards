"""
Tustin City Council Scraper
Dynamically discovers council members, scrapes meeting archives from Granicus,
and extracts city-level info (meeting schedule, Zoom, public comment, clerk).
"""
import re
import tempfile
from datetime import datetime
from urllib.parse import urljoin

import requests

from ..base import BaseScraper


class TustinScraper(BaseScraper):
    """Tustin - CivicPlus with dynamic member discovery + Granicus meetings."""

    CITY_NAME = "Tustin"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "tustinca.org"
    BASE_URL = "https://www.tustinca.org"
    COUNCIL_URL = "https://www.tustinca.org/482/City-Council"
    MEETINGS_URL = "https://www.tustinca.org/282/Meetings-Agendas"
    GRANICUS_URL = "https://tustin.granicus.com/ViewPublisher.php?view_id=5"
    # PDF with Zoom meeting info for City Council
    ZOOM_PDF_URL = "https://www.tustinca.org/DocumentCenter/View/4729/PUBLIC-INPUT-INSTRUCTIONS"

    # Known term dates - Tustin has 5 at-large seats, 4-year staggered terms
    KNOWN_TERMS = {
        "austin lumbard": {"district": "At-Large", "term_start": 2024, "term_end": 2028},
        "ray schnell": {"district": "At-Large", "term_start": 2024, "term_end": 2028},
        "ryan gallagher": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "lee k. fink": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "lee fink": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "fink": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "john nielsen": {"district": "At-Large", "term_start": 2024, "term_end": 2028},
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
            "granicus": self.GRANICUS_URL,
        }

    async def discover_members(self):
        """Discover council members from CivicPlus-style links."""
        members = []
        seen_ids = set()

        try:
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or len(text) < 3:
                    continue

                href_lower = href.lower()

                # Look for council member profile links
                # Pattern: /ID/Mayor-Name or /ID/Mayor-Pro-Tem-Name or /ID/Council-Member-Name
                match = re.search(r'/(\d+)/(mayor-pro-tem|mayor|council-member)-(.+?)/?$', href_lower)
                if not match:
                    continue

                page_id = match.group(1)
                position_slug = match.group(2)
                name_slug = match.group(3)

                # Skip main council page
                if page_id == "482":
                    continue

                if page_id in seen_ids:
                    continue
                seen_ids.add(page_id)

                # Determine position from URL
                if position_slug == "mayor-pro-tem":
                    position = "Mayor Pro Tem"
                elif position_slug == "mayor":
                    position = "Mayor"
                else:
                    position = "Councilmember"

                # Convert name slug to proper name
                # Handle middle initials: "lee-k-fink" -> "Lee K. Fink"
                name_parts = name_slug.split("-")
                name_formatted = []
                for i, part in enumerate(name_parts):
                    if len(part) == 1:
                        # Single letter = initial, add period
                        name_formatted.append(part.upper() + ".")
                    else:
                        name_formatted.append(part.title())
                name = " ".join(name_formatted)

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

    async def detect_position_from_page(self):
        """Detect position from page content - check for Mayor Pro Tem."""
        try:
            text = await self.get_page_text()
            text_lower = text.lower()

            # Look for Mayor Pro Tem indication
            if re.search(r'\bmayor\s+pro\s+tem\b', text_lower[:1000]):
                return "Mayor Pro Tem"

            # Check page title
            title = await self.page.title()
            if title and "mayor pro tem" in title.lower():
                return "Mayor Pro Tem"

        except Exception:
            pass
        return None  # Return None to keep URL-based position

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st and 3rd Tuesdays",
            "meeting_time": "6:00 PM",
            "meeting_location": {
                "name": "City Hall Council Chamber",
                "address": "300 Centennial Way",
                "city_state_zip": "Tustin, CA 92780"
            },
            "zoom": {},
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Spectrum", "channel": "3"}
            ],
            "live_stream": None,
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(714) 573-3025",
                "email": "CityCouncil@tustinca.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": True,
                "ecomment": True,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "CityCouncil@tustinca.org"
            },
            "portals": {
                "granicus": self.GRANICUS_URL,
                "ecomment": None,
                "live_stream": None,
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
                "seats_up": ["Mayor Pro Tem", "Councilmember", "Councilmember"],
                "term_length": 4,
                "election_system": "at-large"
            }
        }

        # Scrape meeting info page for additional details
        print("    Scraping meeting info...")
        try:
            await self.page.goto(self.MEETINGS_URL, timeout=30000)
            await self.page.wait_for_timeout(2000)
            text = await self.page.inner_text("body")

            # TV channels
            if "spectrum" in text.lower():
                city_info["tv_channels"].append({"provider": "Spectrum", "channel": "3"})
            if "cox" in text.lower():
                city_info["tv_channels"].append({"provider": "Cox", "channel": "3"})

        except Exception as e:
            self.results["errors"].append(f"scrape_city_info: {str(e)}")

        # Scrape Zoom info from the PUBLIC-INPUT-INSTRUCTIONS PDF
        print("    Scraping Zoom info from PDF...")
        try:
            # Download the PDF
            response = requests.get(self.ZOOM_PDF_URL, timeout=30)
            if response.status_code == 200:
                # Save to temp file and parse with pdfplumber
                import pdfplumber
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    f.write(response.content)
                    temp_path = f.name

                with pdfplumber.open(temp_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text() or ""

                        # Zoom meeting ID - PDF may have garbled text like "Mee(cid:415)ng ID"
                        # Look for pattern: 3 digits, space, 4 digits, space, 4 digits
                        zoom_id_match = re.search(r"(\d{3})\s+(\d{4})\s+(\d{4})", text)
                        if zoom_id_match:
                            zoom_id = f"{zoom_id_match.group(1)} {zoom_id_match.group(2)} {zoom_id_match.group(3)}"
                            city_info["zoom"]["meeting_id"] = zoom_id
                            print(f"      Zoom ID: {zoom_id}")

                        # Zoom passcode (6 digits after "Passcode:" or standalone 6 digits near passcode text)
                        passcode_match = re.search(r"(?:Passcode|Password)[:\s]*(\d{6})", text, re.I)
                        if passcode_match:
                            city_info["zoom"]["passcode"] = passcode_match.group(1)
                            print(f"      Passcode: {passcode_match.group(1)}")

                        # Phone dial-in (669-900-6833 pattern - may have newline in PDF)
                        phone_match = re.search(r"(669[-.\s]*\d{3}[-.\s]*\d{4})", text)
                        if phone_match:
                            # Clean up: remove newlines/spaces, normalize to dashes
                            phone = re.sub(r"[\s\n]+", "", phone_match.group(1))
                            phone = phone.replace(".", "-")
                            # Format as XXX-XXX-XXXX
                            if len(phone) == 10:
                                phone = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
                            if phone not in city_info["phone_numbers"]:
                                city_info["phone_numbers"].append(phone)
                                print(f"      Phone: {phone}")

                        # If we found all Zoom info, stop
                        if city_info["zoom"].get("meeting_id") and city_info["zoom"].get("passcode"):
                            break

                # Clean up temp file
                import os
                os.unlink(temp_path)

        except Exception as e:
            self.results["errors"].append(f"scrape_zoom_info: {str(e)}")
            print(f"      Error scraping Zoom PDF: {e}")

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
                    if "CITY COUNCIL" not in row_text.upper() and "COUNCIL" not in row_text.upper():
                        # Check if it's a planning commission or other meeting
                        if "PLANNING" in row_text.upper() or "COMMISSION" in row_text.upper():
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
                            video_url = f"https://tustin.granicus.com/player/clip/{clip_match.group(1)}?view_id=5"

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
                # URL-based position is authoritative (page content may have historical references)
                position = member["position"]

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
