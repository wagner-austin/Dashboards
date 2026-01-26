"""
Anaheim City Council Scraper
Dynamically discovers council members, scrapes meeting archives from Granicus,
and extracts city-level info (meeting schedule, public comment, clerk).
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class AnaheimScraper(BaseScraper):
    """Anaheim - CivicPlus platform with dynamic member discovery + Granicus meetings."""

    CITY_NAME = "Anaheim"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "anaheim.net"
    BASE_URL = "https://www.anaheim.net"
    COUNCIL_URL = "https://www.anaheim.net/173/City-Council"
    MEETINGS_URL = "https://www.anaheim.net/344/Public-Participation-at-a-City-Council-M"
    GRANICUS_URL = "https://anaheim.granicus.com/ViewPublisher.php?view_id=2"

    # URL corrections for CivicPlus pages with outdated slugs
    # The page IDs are correct but slugs still show old council member names
    URL_CORRECTIONS = {
        "/3522/Council-Member-Jose-Diaz": "/3522/Council-Member-Ryan-Balius",
        "/3521/Council-Member-Stephen-Faessel": "/3521/Council-Member-Kristen-Maahs",
        "/3524/Mayor-Pro-Tem-Norma-Campos-Kurtz": "/3524/Council-Member-Norma-Campos-Kurtz",
    }

    def get_urls(self):
        return {
            "council": self.COUNCIL_URL,
            "meetings": self.MEETINGS_URL,
            "granicus": self.GRANICUS_URL,
        }

    async def discover_members(self):
        """Discover council members from profile links on main page."""
        members = []
        seen_urls = set()
        seen_names = set()  # Also track names to avoid duplicates

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

                # Apply URL corrections for outdated slugs
                for old_path, new_path in self.URL_CORRECTIONS.items():
                    if old_path in url:
                        url = url.replace(old_path, new_path)
                        break

                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Skip duplicate names (same person with different link)
                name_lower = name.lower()
                if name_lower in seen_names:
                    continue
                seen_names.add(name_lower)

                members.append({"name": name, "position": position, "url": url})
                print(f"      Found: {position} {name}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape_city_info(self):
        """Scrape city-level info: meeting schedule, location, public comment, clerk."""
        city_info = {
            "city_name": self.CITY_NAME,
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st and 3rd Tuesdays",
            "meeting_time": "5:00 PM",
            "meeting_location": {
                "name": "Council Chamber",
                "address": "200 S. Anaheim Blvd",
                "city_state_zip": "Anaheim, CA 92805"
            },
            "tv_channels": [
                {"provider": "Charter Spectrum", "channel": "3"},
                {"provider": "AT&T U-verse", "channel": "99"}
            ],
            "clerk": {},
            "public_comment": {},
            "portals": {
                "granicus": self.GRANICUS_URL,
                "live_stream": "https://www.anaheim.net/councilvideos",
                "agendas": "http://local.anaheim.net/docs_agend/questys_pub/",
            },
            "council": {
                "size": 7,
                "districts": 6,
                "at_large": 1,  # Mayor
                "mayor_elected": True,
                "term_length": 4,
            },
            "elections": {
                "next_election": "2026-11-03",
                # Districts 1,2,3 up in 2026, Districts 4,5,6 up in 2028
                "seats_up": ["Mayor", "District 1", "District 2", "District 3"],
                "election_system": "by-district",
                "term_length": 4,
            }
        }

        # Scrape public comment info
        print("    Scraping public participation info...")
        try:
            await self.page.goto(self.MEETINGS_URL, timeout=30000)
            await self.page.wait_for_timeout(2000)
            text = await self.page.inner_text("body")

            # Public comment email
            if "publiccomment@anaheim.net" in text.lower():
                city_info["public_comment"]["email"] = "publiccomment@anaheim.net"

            # Time limit
            time_limit_match = re.search(r"(\d+)\s*minutes?\s*per\s*speaker", text, re.I)
            if time_limit_match:
                city_info["public_comment"]["time_limit"] = f"{time_limit_match.group(1)} minutes per speaker"

            # Deadline - check for time-based deadline
            deadline_match = re.search(r"(\d+)\s*hours?\s*prior", text, re.I)
            if deadline_match:
                city_info["public_comment"]["deadline"] = f"{deadline_match.group(1)} hours prior to meeting"
            else:
                # Check for specific time deadline like "3:00 PM"
                time_deadline = re.search(r"(?:before|prior to|by)\s*(\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?))", text, re.I)
                if time_deadline:
                    city_info["public_comment"]["deadline"] = f"by {time_deadline.group(1)} day of meeting"

            city_info["public_comment"]["in_person"] = True
            city_info["public_comment"]["remote_live"] = False  # Anaheim is in-person only
            city_info["public_comment"]["ecomment"] = False
            city_info["public_comment"]["written_email"] = True

        except Exception as e:
            self.results["errors"].append(f"scrape_public_comment: {str(e)}")

        # Set clerk info (consistent across Anaheim pages)
        city_info["clerk"] = {
            "title": "City Clerk's Office",
            "phone": "(714) 765-5166",
            "email": "cityclerk@anaheim.net"
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
                            video_url = f"https://anaheim.granicus.com/player/clip/{clip_id}?view_id=2"

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
                    return datetime.min

            meetings.sort(key=lambda m: parse_date(m["date"]), reverse=True)
            print(f"      Found {len(meetings)} City Council meetings")

        except Exception as e:
            self.results["errors"].append(f"scrape_meetings: {str(e)}")
            print(f"      ERROR scraping meetings: {e}")

        return meetings

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

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

                print(f"      Photo: {'Found' if photo_url else 'Not found'}")
                print(f"      Bio: {len(bio) if bio else 0} chars")
                print(f"      Term: {term_start}-{term_end}")
                print(f"      Email: {member_email or 'Not found'}")

                self.add_council_member(
                    name=member["name"],
                    position=member["position"],
                    email=member_email,
                    phone=member_phone,
                    profile_url=member["url"],
                    photo_url=photo_url,
                    bio=bio,
                    term_start=term_start,
                    term_end=term_end,
                )
            else:
                self.add_council_member(
                    name=member["name"],
                    position=member["position"],
                    profile_url=member["url"],
                )

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)

        # Scrape city-level info (schedule, public comment, clerk)
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        # Scrape meetings from Granicus
        meetings = await self.scrape_meetings()
        self.results["meetings"] = meetings

        return self.get_results()
