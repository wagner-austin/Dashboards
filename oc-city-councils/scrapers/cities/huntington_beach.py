"""
Huntington Beach City Council Scraper
Dynamically discovers council members from website.
All members on single page - no individual profile pages.
Scrapes meeting archives from Granicus and city-level info.
"""
import re
from datetime import datetime
from ..base import BaseScraper


class HuntingtonBeachScraper(BaseScraper):
    """Huntington Beach - Custom PHP, all members on single page + Granicus meetings."""

    CITY_NAME = "Huntington Beach"
    PLATFORM = "custom"
    CITY_DOMAIN = "surfcity-hb.org"
    BASE_URL = "https://www.huntingtonbeachca.gov"
    COUNCIL_URL = "https://www.huntingtonbeachca.gov/government/city_council/index.php"
    GRANICUS_URL = "https://huntingtonbeach.granicus.com/ViewPublisher.php?view_id=9"
    LEGISTAR_URL = "https://huntingtonbeach.legistar.com/"
    AGENDA_COMMENTS_URL = "https://huntingtonbeachca.gov/government/city_clerk/agenda_comments.php"
    LIVE_STREAM_URL = "https://reflect-huntingtonbeach.cablecast.tv/CablecastPublicSite/?channel=1"

    def get_urls(self):
        return {
            "council": self.COUNCIL_URL,
            "granicus": self.GRANICUS_URL,
            "legistar": self.LEGISTAR_URL,
            "agenda_comments": self.AGENDA_COMMENTS_URL,
            "live_stream": self.LIVE_STREAM_URL,
        }

    # Known term end dates (at-large elections, staggered 4-year terms)
    # 2022 elected -> term ends 2026, 2024 elected -> term ends 2028
    KNOWN_TERMS = {
        "casey mckeon": (2022, 2026),
        "casey mc keon": (2022, 2026),  # Handle space in name
        "mckeon": (2022, 2026),  # Just last name
        "pat burns": (2022, 2026),
        "gracey van der mark": (2022, 2026),
        "andrew gruel": (2025, 2026),  # Appointed March 2025 to fill vacancy
        "butch twining": (2024, 2028),
        "don kennedy": (2024, 2028),
        "chad williams": (2024, 2028),
    }

    async def discover_members(self, page_text, main_emails):
        """Discover council members from the main page text with photos and terms."""
        members = []

        # Extract photo URLs from page
        photo_map = await self._extract_photos()

        # Match name patterns from emails (e.g., Chad.Williams@ -> Chad Williams)
        for email in main_emails:
            local_part = email.split("@")[0]

            # Handle first.last pattern
            if "." in local_part:
                parts = local_part.split(".")
                if len(parts) == 2:
                    first_name = parts[0].capitalize()
                    last_name = parts[1]

                    # Handle camelCase last names (VanDerMark -> Van Der Mark)
                    last_name_spaced = re.sub(r'([A-Z])', r' \1', last_name).strip()
                    last_name_display = last_name_spaced.title()

                    name = f"{first_name} {last_name_display}"

                    # Check if any part of the name appears in page text
                    name_check = last_name.lower()
                    if name_check in page_text.lower() or last_name_spaced.lower() in page_text.lower():
                        # Determine position from page text
                        position = self._detect_position(name, page_text)

                        # Get photo URL
                        photo_url = self._find_photo_for_member(name, photo_map)

                        # Get term dates
                        term_start, term_end = self._get_term_dates(name)

                        members.append({
                            "name": name,
                            "position": position,
                            "email": email,
                            "photo_url": photo_url,
                            "term_start": term_start,
                            "term_end": term_end,
                        })
                        print(f"      Found: {name} ({position}) - Term: {term_start}-{term_end}")

        return members

    async def _extract_photos(self):
        """Extract photo URLs from the council page."""
        photo_map = {}
        try:
            imgs = await self.page.query_selector_all('img[src*="Headshot"], img[src*="headshot"], img[src*="Council"]')
            for img in imgs:
                src = await img.get_attribute("src") or ""
                alt = (await img.get_attribute("alt") or "").lower()

                if not src or "logo" in src.lower() or "icon" in src.lower():
                    continue

                # Make absolute URL
                if src.startswith("/"):
                    src = f"{self.BASE_URL}{src}"
                elif not src.startswith("http"):
                    src = f"{self.BASE_URL}/{src}"

                # Try to match name from filename or alt text
                src_lower = src.lower()
                for name_key in ["mckeon", "twining", "burns", "kennedy", "vandermark", "vandemark",
                                 "williams", "gruel", "gracey", "casey", "butch", "pat", "don", "chad", "andrew"]:
                    if name_key in src_lower or name_key in alt:
                        photo_map[name_key] = src
                        break

        except Exception as e:
            print(f"      Photo extraction error: {e}")
        return photo_map

    def _find_photo_for_member(self, name, photo_map):
        """Find photo URL for a member from the photo map."""
        name_lower = name.lower()
        name_parts = name_lower.split()

        # Check various name parts
        for part in name_parts:
            if part in photo_map:
                return photo_map[part]

        # Check combined names (VanDerMark)
        combined = "".join(name_parts)
        for key, url in photo_map.items():
            if key in combined or combined in key:
                return url

        return None

    def _get_term_dates(self, name):
        """Get term start/end dates for a member."""
        name_lower = name.lower()
        for known_name, (start, end) in self.KNOWN_TERMS.items():
            if known_name in name_lower or name_lower in known_name:
                return start, end
            # Check last name match
            known_last = known_name.split()[-1]
            name_last = name_lower.split()[-1]
            if known_last == name_last:
                return start, end
        return None, None

    def _detect_position(self, name, text):
        """Detect position for a member from page text."""
        text_lower = text.lower()
        name_lower = name.lower()
        first_name = name_lower.split()[0]

        # Search for position mentions near the name
        # Check for Mayor Pro Tem first (more specific)
        pro_tem_patterns = [
            rf'mayor\s+pro\s+tem[:\s]*{first_name}',
            rf'{first_name}[^,\n]{{0,20}}mayor\s+pro\s+tem',
        ]
        for pattern in pro_tem_patterns:
            if re.search(pattern, text_lower):
                return "Mayor Pro Tem"

        # Check for Mayor (use negative lookahead only)
        mayor_patterns = [
            rf'mayor[:\s]*{first_name}',
            rf'{first_name}[^,\n]{{0,20}}mayor(?!\s+pro)',
        ]
        for pattern in mayor_patterns:
            match = re.search(pattern, text_lower)
            if match:
                # Make sure it's not actually "mayor pro tem"
                matched_text = text_lower[max(0, match.start()-10):match.end()+15]
                if "pro tem" not in matched_text:
                    return "Mayor"

        return "Councilmember"

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])
        main_emails = [e for e in main_result.get("emails", [])
                       if self.CITY_DOMAIN.lower() in e.lower()]

        page_text = await self.get_page_text()

        print("    Discovering council members...")
        members = await self.discover_members(page_text, main_emails)

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} members")

        for member in members:
            self.add_council_member(
                name=member["name"],
                position=member["position"],
                email=member["email"],
                phone=main_phones[0] if main_phones else None,
                photo_url=member.get("photo_url"),
                term_start=member.get("term_start"),
                term_end=member.get("term_end"),
                profile_url=self.COUNCIL_URL,  # All members on same page
            )

        # Scrape city-level info
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        # Scrape meetings from Granicus
        meetings = await self.scrape_meetings()
        self.results["meetings"] = meetings

        return self.get_results()

    async def scrape_city_info(self):
        """Scrape city-level info: meeting schedule, public comment, clerk."""
        city_info = {
            "city_name": self.CITY_NAME,
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st and 3rd Tuesdays",
            "meeting_time": "6:00 PM",
            "meeting_location": {
                "name": "City Council Chambers",
                "address": "2000 Main Street",
                "city_state_zip": "Huntington Beach, CA 92648"
            },
            "zoom": {},  # HB returned to in-person only, no current Zoom
            "phone_numbers": [],
            "tv_channels": [],  # HBTV streams online, not traditional cable
            "live_stream": self.LIVE_STREAM_URL,
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(714) 536-5227",
                "email": "cityclerk@surfcity-hb.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # No Zoom currently
                "written_email": True,
                "email": "SupplementalComm@Surfcity-hb.org",
                "time_limit": "3 minutes per speaker",  # Standard HB limit
                "deadline": "Written comments by 9:00 AM day of meeting",
                "ecomment": False,
            },
            "portals": {
                "granicus": self.GRANICUS_URL,
                "legistar": self.LEGISTAR_URL,
                "live_stream": self.LIVE_STREAM_URL,
                "video_archive": self.GRANICUS_URL,
            },
            "broadcast": {
                "hbtv": self.LIVE_STREAM_URL,
                "youtube": True,
                "facebook": True,
            },
            "council": {
                "size": 7,
                "districts": 0,
                "at_large": 7,
                "mayor_elected": True,  # Directly elected
                "term_length": 4,
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["4 at-large seats"],
                "election_system": "at-large",
                "term_length": 4,
            }
        }

        # Try to scrape additional info from agenda comments page
        print("    Scraping agenda comments page...")
        try:
            await self.page.goto(self.AGENDA_COMMENTS_URL, timeout=60000, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)
            text = await self.page.inner_text("body")
            print(f"      Got {len(text)} chars from agenda comments page")

            # Look for any Zoom info (in case they add it back)
            zoom_match = re.search(r"(https?://[^\s]*zoom\.us/[jw]/\d+)", text, re.I)
            if zoom_match:
                city_info["zoom"]["url"] = zoom_match.group(1)
                city_info["public_comment"]["remote_live"] = True
                print(f"      Found Zoom URL: {zoom_match.group(1)}")

            # Time limit - look for specific patterns like "three (3) minutes" or "maximum of 3 minutes"
            # Only update if we find a clear time limit reference
            time_match = re.search(r"(?:maximum|limit)?\s*(?:of\s+)?(?:three|3)\s*\(?3?\)?\s*minutes?\s*(?:per|each|to speak)", text, re.I)
            if time_match:
                city_info["public_comment"]["time_limit"] = "3 minutes per speaker"

        except Exception as e:
            print(f"      Agenda comments page error: {str(e)}")

        return city_info

    async def scrape_meetings(self):
        """Scrape meeting data from Granicus portal."""
        meetings = []
        seen_keys = set()

        print("    Scraping meetings from Granicus...")

        try:
            await self.page.goto(self.GRANICUS_URL, timeout=60000, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # Scroll to load content
            for _ in range(5):
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.page.wait_for_timeout(500)

            agenda_links = await self.page.query_selector_all('a[href*="AgendaViewer"]')
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
                    row_upper = row_text.upper()
                    if "CITY COUNCIL" not in row_upper:
                        continue

                    # Parse date
                    row_text_clean = row_text.replace('\xa0', ' ')
                    date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", row_text_clean)
                    if not date_match:
                        date_match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", row_text_clean)
                        if date_match:
                            month_str = date_match.group(1)
                            day_str = date_match.group(2)
                            year_str = date_match.group(3)
                            date_str = f"{month_str} {day_str}, {year_str}"
                        else:
                            continue
                    else:
                        # Convert MM/DD/YY to full date
                        date_parts = date_match.group(1).split("/")
                        if len(date_parts) == 3:
                            month_num = int(date_parts[0])
                            day_num = int(date_parts[1])
                            year_num = int(date_parts[2])
                            if year_num < 100:
                                year_num += 2000
                            month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                                          'July', 'August', 'September', 'October', 'November', 'December']
                            date_str = f"{month_names[month_num]} {day_num}, {year_num}"
                        else:
                            continue

                    lines = [l.strip() for l in row_text.split('\n') if l.strip()]
                    name_text = "City Council Meeting"
                    for line in lines:
                        if "council" in line.lower():
                            name_text = re.sub(r'\s+', ' ', line).strip()[:100]
                            break

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
                            video_url = f"https://huntingtonbeach.granicus.com/player/clip/{clip_match.group(1)}?view_id=9"

                    key = f"{date_str}|{agenda_url}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    meetings.append({
                        "name": name_text,
                        "date": date_str,
                        "agenda_url": agenda_url,
                        "minutes_url": minutes_url,
                        "video_url": video_url,
                        "source": "granicus"
                    })

                except Exception:
                    continue

            def parse_date(date_str):
                try:
                    return datetime.strptime(date_str, "%B %d, %Y")
                except ValueError:
                    return datetime.min

            meetings.sort(key=lambda m: parse_date(m["date"]), reverse=True)
            print(f"      Found {len(meetings)} City Council meetings")

        except Exception as e:
            self.results["errors"].append(f"scrape_meetings: {str(e)}")
            print(f"      ERROR: {str(e)}")

        return meetings
