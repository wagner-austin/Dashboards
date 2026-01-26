"""
Irvine City Council Scraper
Dynamically discovers council members, scrapes meeting archives from Granicus,
and extracts city-level info (meeting schedule, Zoom, public comment, clerk).
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class IrvineScraper(BaseScraper):
    """Irvine - Custom CMS with individual profile pages + Granicus meetings."""

    CITY_NAME = "Irvine"
    PLATFORM = "custom"
    CITY_DOMAIN = "cityofirvine.org"
    BASE_URL = "https://www.cityofirvine.org"
    COUNCIL_URL = "https://www.cityofirvine.org/city-council"
    MEETINGS_URL = "https://www.cityofirvine.org/city-council/city-council-meetings"
    CONTACT_URL = "https://www.cityofirvine.org/city-council/contact-council"
    GRANICUS_URL = "https://irvine.granicus.com/ViewPublisher.php?view_id=68"
    ECOMMENT_URL = "https://irvine.granicusideas.com/meetings"
    LIVE_STREAM_URL = "https://legacy.cityofirvine.org/cityhall/citymanager/pio/ictv/default.asp"

    # Known term dates - expanded district system in 2024
    KNOWN_TERMS = {
        "larry agran": {"district": "At-Large", "term_start": 2024, "term_end": 2026},
        "james mai": {"district": "District 3", "term_start": 2022, "term_end": 2026},
        "mike carroll": {"district": "District 4", "term_start": 2024, "term_end": 2028},
        "william go": {"district": "District 2", "term_start": 2024, "term_end": 2028},
        "melinda liu": {"district": "District 1", "term_start": 2024, "term_end": 2026},
        "betty martinez franco": {"district": "District 5", "term_start": 2024, "term_end": 2026},
        "kathleen treseder": {"district": "At-Large", "term_start": 2024, "term_end": 2026},
    }

    def get_member_info(self, name):
        """Get district and term info for a member."""
        name_lower = name.lower().strip()
        for known_name, info in self.KNOWN_TERMS.items():
            if known_name in name_lower or name_lower in known_name:
                return info
        return None

    def get_urls(self):
        return {
            "council": self.COUNCIL_URL,
            "meetings": self.MEETINGS_URL,
            "contact": self.CONTACT_URL,
            "granicus": self.GRANICUS_URL,
            "ecomment": self.ECOMMENT_URL,
            "live_stream": self.LIVE_STREAM_URL,
        }

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
                if href_lower.endswith("/city-council") or href_lower.endswith("/city-council/"):
                    continue
                skip_patterns = ["mailto:", "#", "agenda", "minutes", "calendar", "meeting", "contact"]
                if any(skip in href_lower for skip in skip_patterns):
                    continue

                # Must be a member page (mayor, vice-mayor, councilmember)
                if not re.search(r'/city-council/(mayor|vice-mayor|councilmember)', href_lower):
                    continue

                full_url = urljoin(self.BASE_URL, href)
                # Normalize URL (ensure www. prefix for deduplication)
                normalized_url = full_url.replace("://cityofirvine.org", "://www.cityofirvine.org")
                if normalized_url in seen_urls:
                    continue
                seen_urls.add(normalized_url)
                full_url = normalized_url

                # Extract name - clean up prefixes
                name = text.strip()
                for prefix in ["Vice Mayor", "Mayor", "Council Member", "Councilmember"]:
                    if name.lower().startswith(prefix.lower()):
                        name = name[len(prefix):].strip()

                if len(name) < 4:
                    continue

                # Determine position from URL/text
                position = "Councilmember"
                if "vice-mayor" in href_lower or "vice mayor" in text.lower():
                    position = "Vice Mayor"
                elif "mayor" in href_lower.split("/")[-1].split("-")[0] or text.lower().startswith("mayor"):
                    position = "Mayor"

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
        """Scrape city-level info: meeting schedule, location, Zoom, clerk, public comment."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": None,
            "meeting_time": None,
            "meeting_location": None,
            "zoom": {},
            "phone_numbers": [],
            "tv_channels": [],
            "clerk": {},
            "public_comment": {},
            "portals": {
                "granicus": self.GRANICUS_URL,
                "ecomment": self.ECOMMENT_URL,
                "live_stream": self.LIVE_STREAM_URL,
            }
        }

        # Scrape meeting info page
        print("    Scraping meeting info...")
        try:
            await self.page.goto(self.MEETINGS_URL, timeout=30000)
            await self.page.wait_for_timeout(2000)
            text = await self.page.inner_text("body")

            # Meeting schedule
            schedule_match = re.search(r"(second and fourth|2nd and 4th)\s+(tuesday|monday|wednesday)", text, re.I)
            if schedule_match:
                city_info["meeting_schedule"] = "2nd and 4th Tuesdays"

            # Meeting time
            time_match = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?))", text, re.I)
            if time_match:
                city_info["meeting_time"] = time_match.group(1).replace(".", "").upper()

            # Location
            if "1 Civic Center Plaza" in text:
                city_info["meeting_location"] = {
                    "name": "City Council Chamber",
                    "address": "1 Civic Center Plaza",
                    "city_state_zip": "Irvine, CA 92606"
                }

            # TV channel
            channel_match = re.search(r"channel\s*(\d+)", text, re.I)
            if channel_match:
                city_info["tv_channels"].append({
                    "provider": "Cox",
                    "channel": channel_match.group(1)
                })

        except Exception as e:
            self.results["errors"].append(f"scrape_meeting_info: {str(e)}")

        # Scrape Zoom info from latest agenda
        print("    Scraping Zoom info from agenda...")
        try:
            await self.page.goto(self.GRANICUS_URL, timeout=60000, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # Find first agenda link (upcoming meeting)
            agenda_link = await self.page.query_selector('a[href*="AgendaViewer"][href*="event_id"]')
            if agenda_link:
                agenda_url = await agenda_link.get_attribute("href")
                if agenda_url:
                    if agenda_url.startswith("//"):
                        agenda_url = "https:" + agenda_url
                    await self.page.goto(agenda_url, timeout=30000)
                    await self.page.wait_for_timeout(2000)
                    agenda_text = await self.page.inner_text("body")

                    # Zoom meeting ID
                    zoom_id_match = re.search(r"(?:Meeting ID|ID)[:\s]*(\d{3}[-\s]?\d{3}[-\s]?\d{4})", agenda_text)
                    if zoom_id_match:
                        city_info["zoom"]["meeting_id"] = zoom_id_match.group(1).replace(" ", "-")

                    # Zoom passcode
                    passcode_match = re.search(r"passcode[:\s]*(\d{4,8})", agenda_text, re.I)
                    if passcode_match:
                        city_info["zoom"]["passcode"] = passcode_match.group(1)

                    # Zoom URL
                    if "zoom.us" in agenda_text or "zoomgov.com" in agenda_text:
                        zoom_url_match = re.search(r"(https?://[^\s]*zoom(?:gov)?\.(?:us|com)[^\s]*)", agenda_text)
                        if zoom_url_match:
                            city_info["zoom"]["url"] = zoom_url_match.group(1)
                        elif city_info["zoom"].get("meeting_id"):
                            # Construct URL from meeting ID
                            clean_id = city_info["zoom"]["meeting_id"].replace("-", "")
                            city_info["zoom"]["url"] = f"https://www.zoomgov.com/j/{clean_id}"

                    # Phone numbers (for Zoom dial-in)
                    phone_matches = re.findall(r"(\d{3}[-\s]?\d{3}[-\s]?\d{4})", agenda_text)
                    for phone in phone_matches:
                        clean_phone = phone.replace(" ", "-")
                        # Filter out meeting IDs, duplicates, and invalid numbers
                        if clean_phone in city_info["phone_numbers"]:
                            continue
                        if clean_phone == city_info["zoom"].get("meeting_id", ""):
                            continue
                        if clean_phone.startswith("160") or clean_phone.startswith("0"):
                            continue  # Skip meeting IDs and invalid prefixes
                        if clean_phone.startswith("669") or clean_phone.startswith("833"):
                            city_info["phone_numbers"].append(clean_phone)

        except Exception as e:
            self.results["errors"].append(f"scrape_zoom_info: {str(e)}")

        # Scrape clerk/contact info
        print("    Scraping contact info...")
        try:
            await self.page.goto(self.CONTACT_URL, timeout=30000)
            await self.page.wait_for_timeout(2000)
            text = await self.page.inner_text("body")

            # Clerk info
            city_info["clerk"]["title"] = "City Clerk's Office"

            # Clerk phone
            phone_match = re.search(r"(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})", text)
            if phone_match:
                city_info["clerk"]["phone"] = phone_match.group(1)

            # Clerk/council email
            emails = self.extract_emails(text)
            council_emails = [e for e in emails if "council" in e.lower() or "clerk" in e.lower()]
            if council_emails:
                city_info["clerk"]["email"] = council_emails[0]
            else:
                city_info["clerk"]["email"] = "irvinecitycouncil@cityofirvine.org"

        except Exception as e:
            self.results["errors"].append(f"scrape_contact_info: {str(e)}")

        # Public comment info
        city_info["public_comment"] = {
            "in_person": True,
            "remote_live": True,
            "ecomment": True,
            "written_email": True,
            "time_limit": "3 minutes per speaker",
            "email": "irvinecitycouncil@cityofirvine.org"
        }

        return city_info

    async def scrape_meetings(self, granicus_url=None):
        """Scrape meeting data from Granicus portal."""
        meetings = []
        seen_keys = set()
        url = granicus_url or self.GRANICUS_URL

        print(f"    Scraping meetings from Granicus...")

        try:
            await self.page.goto(url, timeout=60000, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # Scroll to load all content (Granicus lazy loads)
            for _ in range(10):
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.page.wait_for_timeout(500)

            # Get all links that have AgendaViewer - these are meeting rows
            agenda_links = await self.page.query_selector_all('a[href*="AgendaViewer"]')
            print(f"      Found {len(agenda_links)} agenda links")

            for link in agenda_links:
                try:
                    # Get the parent row
                    row = await link.evaluate_handle("el => el.closest('tr')")
                    if not row:
                        continue

                    row_el = row.as_element()
                    if not row_el:
                        continue

                    # Get all text in row to find meeting info
                    row_text = await row_el.inner_text()

                    # Skip non-council meetings
                    if "CITY COUNCIL" not in row_text.upper():
                        continue

                    # Parse date from row text
                    row_text_clean = row_text.replace('\xa0', ' ')
                    date_match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", row_text_clean)
                    if not date_match:
                        continue

                    month_str = date_match.group(1)
                    day_str = date_match.group(2)
                    year_str = date_match.group(3)

                    # Convert abbreviated month to full name
                    month_map = {
                        'Jan': 'January', 'Feb': 'February', 'Mar': 'March',
                        'Apr': 'April', 'May': 'May', 'Jun': 'June',
                        'Jul': 'July', 'Aug': 'August', 'Sep': 'September',
                        'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
                    }
                    if month_str in month_map:
                        month_str = month_map[month_str]

                    date_str = f"{month_str} {day_str}, {year_str}"

                    # Get meeting name (first line)
                    lines = [l.strip() for l in row_text.split('\n') if l.strip()]
                    name_text = lines[0] if lines else "City Council Meeting"
                    name_text = re.sub(r'\s+', ' ', name_text).strip()
                    if len(name_text) > 100:
                        name_text = name_text[:100]

                    # Get agenda URL
                    agenda_url = await link.get_attribute("href")
                    if agenda_url and agenda_url.startswith("//"):
                        agenda_url = "https:" + agenda_url

                    # Get minutes link from same row
                    minutes_link = await row_el.query_selector('a[href*="MinutesViewer"]')
                    minutes_url = None
                    if minutes_link:
                        minutes_url = await minutes_link.get_attribute("href")
                        if minutes_url and minutes_url.startswith("//"):
                            minutes_url = "https:" + minutes_url

                    # Get video player URL (not MP4 download)
                    video_url = None
                    if agenda_url:
                        clip_match = re.search(r"clip_id=(\d+)", agenda_url)
                        if clip_match:
                            clip_id = clip_match.group(1)
                            # Extract base domain from granicus URL
                            domain_match = re.search(r"https?://([^/]+)", url)
                            domain = domain_match.group(1) if domain_match else "irvine.granicus.com"
                            video_url = f"https://{domain}/player/clip/{clip_id}?view_id=68"

                    # Get event_id
                    event_id = None
                    if agenda_url:
                        event_match = re.search(r"event_id=(\d+)", agenda_url)
                        if event_match:
                            event_id = event_match.group(1)

                    # Deduplicate
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

            # Sort by date (newest first)
            def parse_date(date_str):
                try:
                    return datetime.strptime(date_str, "%B %d, %Y")
                except ValueError:
                    try:
                        return datetime.strptime(date_str, "%B  %d, %Y")
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

        # Scrape council members
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
            # Always use KNOWN_TERMS for term/district data (page may show historical info)
            member_info = self.get_member_info(data.get("name", ""))
            if member_info:
                data["district"] = member_info.get("district")
                data["term_start"] = member_info.get("term_start")
                data["term_end"] = member_info.get("term_end")
            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)

        # Scrape city-level info (schedule, Zoom, clerk, public comment)
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        # Scrape meetings from Granicus
        meetings = await self.scrape_meetings()
        self.results["meetings"] = meetings

        return self.get_results()
