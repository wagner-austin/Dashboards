"""
Garden Grove City Council Scraper
Dynamically discovers council members from website.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class GardenGroveScraper(BaseScraper):
    """Garden Grove - Custom CMS with /city-council/name pattern."""

    CITY_NAME = "Garden Grove"
    PLATFORM = "custom"
    CITY_DOMAIN = "ggcity.org"
    BASE_URL = "https://ggcity.org"
    COUNCIL_URL = "https://ggcity.org/city-council"
    GRANICUS_URL = "https://gardengrove.granicus.com/ViewPublisher.php?view_id=1"

    # Known term dates - Garden Grove has 6 districts + at-large mayor, 4-year staggered terms
    KNOWN_TERMS = {
        "stephanie klopfenstein": {"district": "Citywide", "term_start": 2024, "term_end": 2028},
        "george s. brietigam iii": {"district": "District 1", "term_start": 2022, "term_end": 2026},
        "george brietigam": {"district": "District 1", "term_start": 2022, "term_end": 2026},
        "brietigam": {"district": "District 1", "term_start": 2022, "term_end": 2026},
        "phillip nguyen": {"district": "District 2", "term_start": 2024, "term_end": 2028},
        "cindy ngoc tran": {"district": "District 3", "term_start": 2022, "term_end": 2026},
        "cindy tran": {"district": "District 3", "term_start": 2022, "term_end": 2026},
        "joe dovinh": {"district": "District 4", "term_start": 2022, "term_end": 2026},
        "yesenia muñeton": {"district": "District 5", "term_start": 2024, "term_end": 2028},
        "yesenia muneton": {"district": "District 5", "term_start": 2024, "term_end": 2028},
        "ariana arestegui": {"district": "District 6", "term_start": 2024, "term_end": 2028},
    }

    def get_member_info(self, name):
        """Get district and term info for a member."""
        name_lower = name.lower().strip()
        # Remove special characters for matching
        name_normalized = re.sub(r'[^\w\s]', '', name_lower)
        for known_name, info in self.KNOWN_TERMS.items():
            known_normalized = re.sub(r'[^\w\s]', '', known_name)
            if known_name in name_lower or name_lower in known_name:
                return info
            if known_normalized in name_normalized or name_normalized in known_normalized:
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
                skip_patterns = ["mailto:", "#", "agenda", "minutes", "calendar", "meeting"]
                if any(skip in href_lower for skip in skip_patterns):
                    continue

                # Must have a name slug after /city-council/
                if not re.search(r'/city-council/[a-z]+-[a-z]+', href_lower):
                    continue

                full_url = urljoin(self.BASE_URL, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Extract name - clean up prefixes
                name = text.strip()
                for prefix in ["Mayor Pro Tem", "Mayor", "Council Member", "Councilmember"]:
                    if name.lower().startswith(prefix.lower()):
                        name = name[len(prefix):].strip()
                name = name.lstrip("- ").strip()

                if len(name) < 4:
                    continue

                # Determine position
                position = "Councilmember"
                text_lower = text.lower()
                if "mayor pro tem" in text_lower:
                    position = "Mayor Pro Tem"
                elif "mayor" in text_lower and "pro tem" not in text_lower:
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

    async def detect_position_from_page(self):
        """Detect position from current member page."""
        try:
            text = await self.get_page_text()
            first_part = text[:1000].lower()

            if "mayor pro tem" in first_part:
                return "Mayor Pro Tem"
            elif "mayor" in first_part and "pro tem" not in first_part:
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
                # Detect position from individual page
                position = await self.detect_position_from_page()

                photo_url = await self.extract_photo_url(member["name"], self.BASE_URL)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                member_email = None
                if result.get("emails"):
                    member_email = self.match_email_to_name(
                        member["name"], result["emails"], self.CITY_DOMAIN
                    )

                result_phones = result.get("phones", [])
                member_phone = result_phones[0] if result_phones else (main_phones[0] if main_phones else None)

                print(f"      Position: {position}")
                print(f"      Email: {member_email or 'Not found'}")

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
                    position="Councilmember",
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

    async def scrape_city_info(self):
        """Scrape city-level info."""
        city_info = {
            "city_name": self.CITY_NAME,
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "2nd and 4th Tuesdays",
            "meeting_time": "5:30 PM",
            "meeting_location": {
                "name": "City Council Chamber",
                "address": "11300 Stanford Avenue",
                "city_state_zip": "Garden Grove, CA 92840"
            },
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(714) 741-5040",
                "email": "cityclerk@ggcity.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": True,
                "written_email": True,
                "ecomment": True,
                "time_limit": "3 minutes per speaker",
                "email": "cityclerk@ggcity.org",
            },
            "portals": {
                "granicus": self.GRANICUS_URL,
            },
            "council": {
                "size": 7,
                "districts": 6,
                "at_large": 1,  # Mayor is at-large
                "mayor_elected": True,
                "term_length": 4,
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["District 1", "District 3", "District 4"],
                "election_system": "by-district",
                "term_length": 4,
            }
        }
        return city_info

    async def scrape_meetings(self):
        """Scrape meeting data from Granicus portal."""
        meetings = []
        seen_keys = set()

        print("    Scraping meetings from Granicus...")

        try:
            await self.page.goto(self.GRANICUS_URL, timeout=60000, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

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
                    row_upper = row_text.upper()
                    if "CITY COUNCIL" not in row_upper:
                        continue

                    row_text_clean = row_text.replace('\xa0', ' ')
                    date_match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", row_text_clean)
                    if not date_match:
                        continue

                    date_str = f"{date_match.group(1)} {date_match.group(2)}, {date_match.group(3)}"

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
                            video_url = f"https://gardengrove.granicus.com/player/clip/{clip_match.group(1)}?view_id=1"

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
