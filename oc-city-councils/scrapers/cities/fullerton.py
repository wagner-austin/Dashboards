"""
Fullerton City Council Scraper
Dynamically discovers council members, scrapes meeting archives from Granicus,
and extracts city-level info (meeting schedule, Zoom, public comment, clerk).
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class FullertonScraper(BaseScraper):
    """Fullerton - CivicPlus with individual profile pages + Granicus meetings."""

    CITY_NAME = "Fullerton"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cityoffullerton.com"
    BASE_URL = "https://www.cityoffullerton.com"
    COUNCIL_URL = "https://www.cityoffullerton.com/government/city-council"
    MEETINGS_URL = "https://www.cityoffullerton.com/government/city-council/city-council-meetings"
    PARTICIPATE_URL = "https://www.cityoffullerton.com/government/departments/city-manager-s-office/public-information/participating-in-city-council-meetings"
    GRANICUS_URL = "https://fullerton.granicus.com/ViewPublisher.php?view_id=2"
    LEGISTAR_URL = "https://fullerton.legistar.com/"
    DISTRICT_MAP_URL = "https://www.cityoffullerton.com/government/departments/city-clerk/elections/find-my-district"

    # District assignments (by-district elections since 2022)
    # District 1: NW Fullerton (Sunny Hills), District 2: Coyote Hills/Hillcrest Park,
    # District 3: Central, District 4: SW Fullerton, District 5: South Fullerton
    # Based on 2022/2024 election results and official city council pages
    KNOWN_DISTRICTS = {
        "fred jung": "District 1",
        "nicholas dunlap": "District 2",
        "shana charles": "District 3",
        "jamie valencia": "District 4",
        "ahmad zahra": "District 5",
    }

    # Term dates for members (4-year terms, staggered)
    # Districts 1,2,4 elected 2024 (end 2028), Districts 3,5 elected 2022 (end 2026)
    KNOWN_TERMS = {
        "fred jung": (2024, 2028),
        "nicholas dunlap": (2020, 2028),  # Re-elected 2024
        "shana charles": (2022, 2026),
        "jamie valencia": (2024, 2028),
        "ahmad zahra": (2018, 2026),  # Re-elected 2022
    }

    def get_term_dates(self, name):
        """Get term dates for a member."""
        name_lower = name.lower().strip()
        for known_name, (start, end) in self.KNOWN_TERMS.items():
            if known_name in name_lower or name_lower in known_name:
                return start, end
        return None, None

    def get_urls(self):
        return {
            "council": self.COUNCIL_URL,
            "meetings": self.MEETINGS_URL,
            "participate": self.PARTICIPATE_URL,
            "granicus": self.GRANICUS_URL,
            "legistar": self.LEGISTAR_URL,
            "district_map": self.DISTRICT_MAP_URL,
        }

    def get_district_for_member(self, name):
        """Get district for a member by name lookup or page scraping."""
        name_lower = name.lower().strip()
        # Check known districts first
        for known_name, district in self.KNOWN_DISTRICTS.items():
            if known_name in name_lower or name_lower in known_name:
                return district
        return None

    async def extract_district_from_page(self):
        """Try to extract district from the current page text."""
        try:
            text = await self.page.inner_text("body")
            # Look for "District X" pattern
            district_match = re.search(r"District\s*(\d)", text, re.IGNORECASE)
            if district_match:
                return f"District {district_match.group(1)}"
        except Exception:
            pass
        return None

    async def discover_members(self):
        """Discover council members from the main council page."""
        members = []
        seen_urls = set()

        try:
            links = await self.page.query_selector_all('a[href*="/city-council/"]')

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                href_lower = href.lower()

                # Skip non-member pages
                skip_patterns = ["mailto:", "#", "agendas", "minutes", "calendar", "contact"]
                if any(skip in href_lower for skip in skip_patterns):
                    continue

                # Must be a member page (mayor- or council-member-)
                if not re.search(r'/(mayor-|council-member-)[a-z]', href_lower):
                    continue

                full_url = urljoin(self.BASE_URL, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Clean up name - remove prefixes
                name = text.strip()
                for prefix in ["Mayor Pro Tem", "Mayor", "Council Member", "Councilmember", "Dr.", "Dr"]:
                    if name.startswith(prefix):
                        name = name[len(prefix):].strip()
                    name = name.lstrip(". ")

                if len(name) < 4:
                    continue

                # Determine position from link text
                position = "Councilmember"
                text_lower = text.lower()
                if "mayor pro tem" in text_lower:
                    position = "Mayor Pro Tem"
                elif "mayor" in text_lower:
                    position = "Mayor"

                # Get district from known mapping
                district = self.get_district_for_member(name)

                members.append({
                    "name": name,
                    "position": position,
                    "district": district,
                    "url": full_url,
                })
                print(f"      Found: {name} ({position}) - {district or 'No district'}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape_city_info(self):
        """Scrape city-level info: meeting schedule, Zoom, public comment, clerk."""
        city_info = {
            "city_name": self.CITY_NAME,
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st and 3rd Tuesdays",
            "meeting_time": "5:30 PM",
            "meeting_location": {
                "name": "Council Chamber",
                "address": "303 W. Commonwealth Ave.",
                "city_state_zip": "Fullerton, CA 92832"
            },
            "zoom": {},
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Spectrum", "channel": "3"},
                {"provider": "AT&T U-verse", "channel": "99"}
            ],
            "live_stream": "https://www.cityoffullerton.com/ftv3",
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(714) 738-6350",
                "email": "cityclerksoffice@cityoffullerton.com"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": True,
                "written_email": True,
                "email": "CouncilMembers@cityoffullerton.com",
                "time_limit": "3 minutes per speaker"
            },
            "portals": {
                "granicus": self.GRANICUS_URL,
                "legistar": self.LEGISTAR_URL,
                "live_stream": "https://www.cityoffullerton.com/ftv3",
                "district_map": self.DISTRICT_MAP_URL,
            },
            "council": {
                "size": 5,
                "districts": 5,
                "at_large": 0,
                "mayor_elected": False,  # Rotates among council members
                "term_length": 4,
            },
            "elections": {
                "next_election": "2026-11-03",
                # District 3 (Charles) and District 5 (Zahra) elected 2022, up in 2026
                "seats_up": ["District 3", "District 5"],
                "election_system": "by-district",
                "term_length": 4,
            }
        }

        # Try to scrape Zoom info from participation page
        print("    Scraping meeting participation info...")
        try:
            await self.page.goto(self.PARTICIPATE_URL, timeout=60000, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(3000)
            text = await self.page.inner_text("body")
            print(f"      Got {len(text)} chars from participation page")

            # Zoom URL - try multiple patterns
            zoom_patterns = [
                r"(https?://[^\s<>\"']*zoom\.us/[jw]/\d+[^\s<>\"']*)",
                r"(https?://[^\s<>\"']*zoomgov\.com/[jw]/\d+[^\s<>\"']*)",
            ]
            for pattern in zoom_patterns:
                zoom_match = re.search(pattern, text, re.I)
                if zoom_match:
                    city_info["zoom"]["url"] = zoom_match.group(1).split("?")[0]  # Clean URL
                    print(f"      Found Zoom URL: {city_info['zoom']['url']}")
                    break

            # Zoom Meeting ID - try multiple formats
            zoom_id_patterns = [
                r"Meeting ID[:\s]*(\d{3}[\s\-]?\d{3,4}[\s\-]?\d{3,4})",
                r"Webinar ID[:\s]*(\d{3}[\s\-]?\d{3,4}[\s\-]?\d{3,4})",
                r"zoom\.us/[jw]/(\d{9,11})",
            ]
            for pattern in zoom_id_patterns:
                zoom_id_match = re.search(pattern, text, re.I)
                if zoom_id_match:
                    raw_id = zoom_id_match.group(1).replace(" ", "").replace("-", "")
                    # Format as XXX-XXXX-XXXX or XXX-XXX-XXXX
                    if len(raw_id) >= 10:
                        formatted_id = f"{raw_id[:3]}-{raw_id[3:7]}-{raw_id[7:]}"
                    else:
                        formatted_id = f"{raw_id[:3]}-{raw_id[3:6]}-{raw_id[6:]}"
                    city_info["zoom"]["meeting_id"] = formatted_id
                    print(f"      Found Zoom ID: {formatted_id}")
                    break

            # Zoom passcode
            passcode_patterns = [
                r"passcode[:\s]*[\"']?(\w+)[\"']?",
                r"password[:\s]*[\"']?(\w+)[\"']?",
            ]
            for pattern in passcode_patterns:
                passcode_match = re.search(pattern, text, re.I)
                if passcode_match:
                    city_info["zoom"]["passcode"] = passcode_match.group(1)
                    print(f"      Found passcode: {passcode_match.group(1)}")
                    break

            # Phone dial-in - multiple formats
            phone_patterns = [
                r"\(?669\)?[-.\s]?\d{3}[-.\s]?\d{4}",
                r"\(?888\)?[-.\s]?\d{3}[-.\s]?\d{4}",
                r"\(?877\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            ]
            for pattern in phone_patterns:
                phone_match = re.search(pattern, text)
                if phone_match:
                    city_info["phone_numbers"].append(phone_match.group(0))
                    print(f"      Found phone: {phone_match.group(0)}")
                    break

            # Time limit
            time_limit_match = re.search(r"(\d+)\s*minutes?\s*(?:to speak|per|each|limit)", text, re.I)
            if time_limit_match:
                city_info["public_comment"]["time_limit"] = f"{time_limit_match.group(1)} minutes per speaker"
                print(f"      Found time limit: {time_limit_match.group(1)} min")

            city_info["public_comment"]["ecomment"] = "zoom" in text.lower()

        except Exception as e:
            self.results["errors"].append(f"scrape_city_info: {str(e)}")
            print(f"      ERROR: {str(e)}")

        # If no Zoom info found, try Legistar calendar for most recent meeting
        if not city_info["zoom"].get("url"):
            print("    Checking Legistar for Zoom info...")
            try:
                await self.page.goto(self.LEGISTAR_URL, timeout=60000, wait_until="domcontentloaded")
                await self.page.wait_for_timeout(3000)

                # Find a recent meeting link
                meeting_links = await self.page.query_selector_all('a[href*="MeetingDetail"]')
                if meeting_links:
                    meeting_url = await meeting_links[0].get_attribute("href")
                    if meeting_url:
                        if not meeting_url.startswith("http"):
                            meeting_url = f"https://fullerton.legistar.com/{meeting_url}"
                        print(f"      Checking meeting: {meeting_url[:60]}...")
                        await self.page.goto(meeting_url, timeout=60000, wait_until="domcontentloaded")
                        await self.page.wait_for_timeout(2000)
                        meeting_text = await self.page.inner_text("body")

                        # Try to find Zoom info in meeting details
                        for pattern in zoom_patterns:
                            zoom_match = re.search(pattern, meeting_text, re.I)
                            if zoom_match:
                                city_info["zoom"]["url"] = zoom_match.group(1).split("?")[0]
                                print(f"      Found Zoom URL from Legistar: {city_info['zoom']['url']}")
                                break

            except Exception as e:
                print(f"      Legistar check error: {str(e)}")

        return city_info

    async def scrape_meetings(self):
        """Scrape meeting data from Granicus portal."""
        meetings = []
        seen_keys = set()

        print("    Scraping meetings from Granicus...")

        try:
            await self.page.goto(self.GRANICUS_URL, timeout=60000, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # Scroll to load all content
            for _ in range(10):
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

                    # Filter for City Council meetings (includes "City Council - Successor Agency")
                    row_upper = row_text.upper()
                    if "CITY COUNCIL" not in row_upper and "COUNCIL" not in row_upper:
                        continue

                    # Parse date - Fullerton uses YYYY-MM-DD format
                    row_text_clean = row_text.replace('\xa0', ' ')

                    # Try YYYY-MM-DD format first
                    date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", row_text_clean)
                    if date_match:
                        year_str = date_match.group(1)
                        month_num = int(date_match.group(2))
                        day_str = date_match.group(3).lstrip('0') or '1'
                        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                                      'July', 'August', 'September', 'October', 'November', 'December']
                        month_str = month_names[month_num]
                        date_str = f"{month_str} {day_str}, {year_str}"
                    else:
                        # Try Month DD, YYYY format
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

                    lines = [l.strip() for l in row_text.split('\n') if l.strip()]
                    name_text = lines[0] if lines else "City Council Meeting"
                    name_text = re.sub(r'\s+', ' ', name_text).strip()[:100]

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
                            video_url = f"https://fullerton.granicus.com/player/clip/{clip_match.group(1)}?view_id=2"

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
                        "event_id": event_id,
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
            data = await self.scrape_member_page(
                member, self.BASE_URL, self.CITY_DOMAIN, main_phones
            )
            # Fill in missing term data from KNOWN_TERMS
            if not data.get("term_start") or not data.get("term_end"):
                term_start, term_end = self.get_term_dates(data.get("name", ""))
                if term_start and not data.get("term_start"):
                    data["term_start"] = term_start
                if term_end and not data.get("term_end"):
                    data["term_end"] = term_end
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)

        # Scrape city-level info
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        # Scrape meetings from Granicus
        meetings = await self.scrape_meetings()
        self.results["meetings"] = meetings

        return self.get_results()
