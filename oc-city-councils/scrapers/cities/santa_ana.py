"""
Santa Ana City Council Scraper
Dynamically discovers council members, scrapes meeting archives from Granicus,
and extracts city-level info (meeting schedule, Zoom, public comment, clerk).
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class SantaAnaScraper(BaseScraper):
    """Santa Ana - WordPress-style with /contacts/name-slug/ URLs + Granicus meetings."""

    CITY_NAME = "Santa Ana"
    PLATFORM = "wordpress"
    CITY_DOMAIN = "santa-ana.org"
    BASE_URL = "https://www.santa-ana.org"
    COUNCIL_URL = "https://www.santa-ana.org/city-council-members/"
    MEETINGS_URL = "https://www.santa-ana.org/city-meetings/"
    AGENDAS_URL = "https://www.santa-ana.org/agendas-and-minutes/"
    PRIMEGOV_URL = "https://santa-ana.primegov.com/Portal/Meeting"
    GRANICUS_URL = "https://santaana.granicus.com/ViewPublisher.php?view_id=2"  # Archive only (2014-2021)
    LIVE_STREAM_URL = "https://www.youtube.com/@CityofSantaAna"

    # Ward assignments and term dates
    # Mayor: 2-year terms, Councilmembers: 4-year terms
    # Wards 1,3,5 elected 2024 (end 2028), Wards 2,4,6 elected 2022 (end 2026)
    KNOWN_TERMS = {
        "valerie amezcua": {"ward": "Mayor", "term_start": 2024, "term_end": 2026},
        "thai viet phan": {"ward": "Ward 1", "term_start": 2024, "term_end": 2028},
        "benjamin vazquez": {"ward": "Ward 2", "term_start": 2022, "term_end": 2026},
        "jessie lopez": {"ward": "Ward 3", "term_start": 2024, "term_end": 2028},
        "phil bacerra": {"ward": "Ward 4", "term_start": 2022, "term_end": 2026},
        "johnathan ryan hernandez": {"ward": "Ward 5", "term_start": 2024, "term_end": 2028},
        "david penaloza": {"ward": "Ward 6", "term_start": 2022, "term_end": 2026},
    }

    def get_urls(self):
        return {
            "council": self.COUNCIL_URL,
            "meetings": self.MEETINGS_URL,
            "agendas": self.AGENDAS_URL,
            "primegov": self.PRIMEGOV_URL,
            "granicus_archive": self.GRANICUS_URL,
            "live_stream": self.LIVE_STREAM_URL,
        }

    def get_member_info(self, name):
        """Get ward and term info for a member."""
        name_lower = name.lower().strip()
        for known_name, info in self.KNOWN_TERMS.items():
            if known_name in name_lower or name_lower in known_name:
                return info
            # Check last name match
            known_parts = known_name.split()
            name_parts = name_lower.split()
            if known_parts[-1] == name_parts[-1]:
                return info
        return None

    async def discover_members(self):
        """Discover council members from /contacts/ links."""
        members = []
        seen_urls = set()

        try:
            links = await self.page.query_selector_all('a[href*="/contacts/"]')

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                # Must be a council member contact page
                if "/contacts/" not in href:
                    continue

                # Skip navigation/generic links
                if any(skip in href.lower() for skip in ["category", "page", "search"]):
                    continue

                full_url = urljoin(self.BASE_URL, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Use link text as name
                name = text.strip()

                # Skip if name looks generic
                skip_names = ["contact", "email", "phone", "more", "view"]
                if name.lower() in skip_names:
                    continue

                # Initial position guess
                position = "Councilmember"

                members.append({
                    "name": name,
                    "position": position,
                    "url": full_url,
                })
                print(f"      Found: {name}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def detect_position_from_page(self):
        """Detect position from page content."""
        try:
            title = await self.page.title()
            if title:
                title_lower = title.lower()
                if "mayor pro tem" in title_lower:
                    return "Mayor Pro Tem"
                elif "mayor" in title_lower and "pro tem" not in title_lower:
                    return "Mayor"

            text = await self.get_page_text()
            first_1000 = text[:1000].lower()
            if "mayor pro tem" in first_1000:
                return "Mayor Pro Tem"
            elif "mayor" in first_1000 and "pro tem" not in first_1000:
                return "Mayor"

        except Exception:
            pass
        return "Councilmember"

    async def scrape_city_info(self):
        """Scrape city-level info: meeting schedule, Zoom, public comment, clerk."""
        city_info = {
            "city_name": self.CITY_NAME,
            "website": self.BASE_URL,
            "council_url": "https://www.santa-ana.org/departments/city-council/",
            "meeting_schedule": "1st and 3rd Tuesdays",
            "meeting_time": "5:30 PM",
            "meeting_location": {
                "name": "City Council Chamber",
                "address": "22 Civic Center Plaza",
                "city_state_zip": "Santa Ana, CA 92701"
            },
            "zoom": {},
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Spectrum", "channel": "3", "name": "CTV3"}
            ],
            "live_stream": "https://www.youtube.com/@CityofSantaAna",
            "clerk": {
                "title": "City Clerk's Office"
            },
            "public_comment": {},
            "portals": {
                "primegov": self.PRIMEGOV_URL,
                "agendas": self.AGENDAS_URL,
                "granicus_archive": self.GRANICUS_URL,  # Archive only (2014-2021)
                "live_stream": self.LIVE_STREAM_URL,
                "youtube": self.LIVE_STREAM_URL,
            },
            "council": {
                "size": 7,
                "wards": 6,
                "at_large": 1,  # Mayor
                "mayor_elected": True,
                "mayor_term": 2,
                "councilmember_term": 4
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["Mayor", "Ward 2", "Ward 4", "Ward 6"],
                "election_system": "by-ward"
            }
        }

        print("    Scraping meeting info...")
        try:
            await self.page.goto(self.MEETINGS_URL, timeout=60000, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(5000)
            text = await self.page.inner_text("body")
            print(f"      Got {len(text)} chars from meetings page")

            # Zoom URL - try multiple patterns
            zoom_match = re.search(r"(https?://[^\s]*zoom\.us/j/\d+)", text)
            if zoom_match:
                city_info["zoom"]["url"] = zoom_match.group(1)
                print(f"      Found Zoom URL: {zoom_match.group(1)}")

            # Zoom Meeting ID - more flexible pattern
            zoom_id_match = re.search(r"Meeting ID[:\s]*(\d{3}[\s\-]?\d{3}[\s\-]?\d{3,4})", text, re.I)
            if zoom_id_match:
                city_info["zoom"]["meeting_id"] = zoom_id_match.group(1).replace(" ", "-")
                print(f"      Found Zoom ID: {zoom_id_match.group(1)}")

            # Phone dial-in - more flexible pattern
            phone_match = re.search(r"\(669\)\s*\d{3}[-\s]?\d{4}", text)
            if phone_match:
                city_info["phone_numbers"].append(phone_match.group(0))
                print(f"      Found phone: {phone_match.group(0)}")
            else:
                phone_match2 = re.search(r"669[-.\s]?\d{3}[-.\s]?\d{4}", text)
                if phone_match2:
                    city_info["phone_numbers"].append(phone_match2.group(0))
                    print(f"      Found phone: {phone_match2.group(0)}")

            # eComment email
            ecomment_match = re.search(r"(ecomment@santa-ana\.org)", text, re.I)
            if ecomment_match:
                city_info["public_comment"]["ecomment_email"] = ecomment_match.group(1)
                city_info["portals"]["ecomment"] = f"mailto:{ecomment_match.group(1)}"
                print(f"      Found eComment: {ecomment_match.group(1)}")

            # Time limit - look for "three (3) minutes" pattern too
            time_limit_match = re.search(r"(\d+)\s*(?:\(\d+\))?\s*minutes?\s*(?:to speak|per|each)", text, re.I)
            if time_limit_match:
                city_info["public_comment"]["time_limit"] = f"{time_limit_match.group(1)} minutes per speaker"
                print(f"      Found time limit: {time_limit_match.group(1)} min")
            else:
                # Try "three (3) minutes" pattern
                time_limit_match2 = re.search(r"(?:three|3)\s*\(?\d?\)?\s*minutes", text, re.I)
                if time_limit_match2:
                    city_info["public_comment"]["time_limit"] = "3 minutes per speaker"
                    print("      Found time limit: 3 min (text)")

            city_info["public_comment"]["in_person"] = True
            city_info["public_comment"]["remote_live"] = True
            city_info["public_comment"]["ecomment"] = True
            city_info["public_comment"]["written_email"] = True
            city_info["public_comment"]["email"] = "ecomment@santa-ana.org"

            # Clerk phone
            clerk_match = re.search(r"\(714\)\s*647-\d{4}", text)
            if clerk_match:
                city_info["clerk"]["phone"] = clerk_match.group(0)

            # YouTube
            if "youtube" in text.lower():
                city_info["portals"]["youtube"] = True
                print("      Found YouTube mention")

        except Exception as e:
            self.results["errors"].append(f"scrape_city_info: {str(e)}")
            print(f"      ERROR: {str(e)}")

        # Set clerk defaults if not found
        if not city_info["clerk"].get("phone"):
            city_info["clerk"]["phone"] = "(714) 647-6520"
        city_info["clerk"]["email"] = "clerk@santa-ana.org"

        return city_info

    async def scrape_primegov_meetings(self):
        """Scrape current meetings from PrimeGov API (2018+)."""
        meetings = []
        import json as json_module

        print("    Scraping current meetings from PrimeGov...")

        try:
            response = await self.page.goto(
                "https://santa-ana.primegov.com/api/meeting/list",
                timeout=30000
            )
            text = await self.page.inner_text("body")
            data = json_module.loads(text)

            # Filter for City Council meetings
            council_meetings = [
                m for m in data
                if "city council" in m.get("title", "").lower()
            ]

            print(f"      Found {len(council_meetings)} City Council meetings in PrimeGov")

            for m in council_meetings:
                meeting_id = m.get("id")
                date_str = m.get("date", "")
                time_str = m.get("time", "")
                title = m.get("title", "City Council Meeting")
                video_url = m.get("videoUrl")
                zoom_link = m.get("zoomMeetingLink")

                # Parse date to standard format
                try:
                    parsed = datetime.strptime(date_str, "%m/%d/%Y")
                    formatted_date = parsed.strftime("%B %d, %Y")
                except ValueError:
                    formatted_date = date_str

                # Get agenda template ID for URL
                agenda_url = None
                minutes_url = None
                for template in m.get("templates", []):
                    template_id = template.get("id")
                    template_title = template.get("title", "").lower()
                    if "agenda" in template_title and not agenda_url:
                        agenda_url = f"https://santa-ana.primegov.com/Portal/Meeting?meetingTemplateId={template_id}"
                    elif "minutes" in template_title and not minutes_url:
                        minutes_url = f"https://santa-ana.primegov.com/Portal/Meeting?meetingTemplateId={template_id}"

                meetings.append({
                    "name": title,
                    "date": formatted_date,
                    "time": time_str,
                    "agenda_url": agenda_url,
                    "minutes_url": minutes_url,
                    "video_url": video_url,
                    "zoom_url": zoom_link,
                    "event_id": str(meeting_id),
                    "source": "primegov"
                })

        except Exception as e:
            self.results["errors"].append(f"scrape_primegov_meetings: {str(e)}")
            print(f"      ERROR: {str(e)}")

        return meetings

    async def scrape_granicus_meetings(self):
        """Scrape archived meetings from Granicus (2014-2021 only)."""
        meetings = []
        seen_keys = set()

        print("    Scraping archived meetings from Granicus (2014-2021)...")

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
                            video_url = f"https://santaana.granicus.com/player/clip/{clip_match.group(1)}?view_id=2"

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

            def parse_date(date_str):
                try:
                    return datetime.strptime(date_str, "%B %d, %Y")
                except ValueError:
                    return datetime.min

            meetings.sort(key=lambda m: parse_date(m["date"]), reverse=True)
            print(f"      Found {len(meetings)} archived City Council meetings (2014-2021)")

        except Exception as e:
            self.results["errors"].append(f"scrape_granicus_meetings: {str(e)}")
            print(f"      ERROR scraping Granicus: {e}")

        return meetings

    async def scrape_meetings(self):
        """Scrape meetings from both PrimeGov (current) and Granicus (archive)."""
        all_meetings = []

        # Get current meetings from PrimeGov (2018+)
        primegov_meetings = await self.scrape_primegov_meetings()
        all_meetings.extend(primegov_meetings)

        # Get archived meetings from Granicus (2014-2021) - skip to save time
        # granicus_meetings = await self.scrape_granicus_meetings()
        # all_meetings.extend(granicus_meetings)

        # Sort all meetings by date (newest first)
        def parse_date(m):
            try:
                return datetime.strptime(m.get("date", ""), "%B %d, %Y")
            except ValueError:
                return datetime.min

        all_meetings.sort(key=parse_date, reverse=True)
        print(f"    Total meetings: {len(all_meetings)}")

        return all_meetings

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

                # Get ward and term info from known data - always use KNOWN_TERMS
                # since page scraping often has incorrect data
                member_info = self.get_member_info(member["name"])
                district = None
                if member_info:
                    district = member_info.get("ward")
                    # Always use KNOWN_TERMS for term dates (more reliable than page scraping)
                    term_start = member_info.get("term_start")
                    term_end = member_info.get("term_end")

                member_email = None
                if result.get("emails"):
                    member_email = self.match_email_to_name(
                        member["name"], result["emails"], self.CITY_DOMAIN
                    )

                result_phones = result.get("phones", [])
                member_phone = result_phones[0] if result_phones else (main_phones[0] if main_phones else None)

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
                self.add_council_member(
                    name=member["name"],
                    position="Councilmember",
                    profile_url=member["url"],
                )

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)

        # Scrape city-level info
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        # Scrape meetings from Granicus
        meetings = await self.scrape_meetings()
        self.results["meetings"] = meetings

        return self.get_results()
