"""
Newport Beach City Council Scraper
Dynamically discovers council members from website.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class NewportBeachScraper(BaseScraper):
    """Newport Beach - Granicus with district-based profile pages."""

    CITY_NAME = "Newport Beach"
    PLATFORM = "granicus"
    CITY_DOMAIN = "newportbeachca.gov"
    BASE_URL = "https://www.newportbeachca.gov"
    COUNCIL_URL = "https://www.newportbeachca.gov/government/city-council"
    GRANICUS_URL = "https://newportbeach.granicus.com/ViewPublisher.php?view_id=10"

    # Known council members with correct term dates
    # Newport Beach: 7 districts, 4-year staggered terms
    KNOWN_TERMS = {
        "lauren kleiman": {"district": "District 1", "term_start": 2022, "term_end": 2026, "position": "Councilmember"},
        "noah blom": {"district": "District 2", "term_start": 2024, "term_end": 2028, "position": "Mayor Pro Tem"},
        "erik weigand": {"district": "District 3", "term_start": 2022, "term_end": 2026, "position": "Councilmember"},
        "joe stapleton": {"district": "District 4", "term_start": 2022, "term_end": 2026, "position": "Mayor"},
        "michelle barto": {"district": "District 5", "term_start": 2024, "term_end": 2028, "position": "Councilmember"},
        "robyn grant": {"district": "District 6", "term_start": 2022, "term_end": 2026, "position": "Councilmember"},
        "sara weber": {"district": "District 7", "term_start": 2024, "term_end": 2028, "position": "Councilmember"},
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

    def clean_name(self, name):
        """Clean garbage from extracted names."""
        if not name:
            return None
        # Remove year patterns like (2026), (2028*), etc.
        name = re.sub(r'\s*\(?\d{4}\*?\)?', '', name)
        # Remove "Empty heading" and similar garbage
        name = re.sub(r'\s*Empty heading.*', '', name, flags=re.IGNORECASE)
        # Remove position prefixes
        name = re.sub(r'^(Mayor Pro Tem|Pro Tem|Mayor|Council\s*Member|Councilmember)\s+', '', name, flags=re.IGNORECASE)
        # Remove special characters
        name = re.sub(r'[^\w\s\'-]', '', name)
        # Clean whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        return name if len(name) > 2 else None

    def get_urls(self):
        return {
            "council": self.COUNCIL_URL,
            "granicus": self.GRANICUS_URL,
        }

    async def discover_members(self):
        """Discover council members from district page links."""
        members = []
        seen_districts = set()

        try:
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href:
                    continue

                href_lower = href.lower()

                # Look for district profile links
                # Pattern: /find-your-council-district/district-X
                match = re.search(r'/find-your-council-district/(district-\d+)', href_lower)
                if not match:
                    continue

                district = match.group(1)
                if district in seen_districts:
                    continue
                seen_districts.add(district)

                full_url = urljoin(self.BASE_URL, href)

                # District number for reference
                district_num = re.search(r'district-(\d+)', district).group(1)

                members.append({
                    "district": f"District {district_num}",
                    "position": "Councilmember",  # Will detect Mayor/MPT on page
                    "url": full_url,
                })
                print(f"      Found: District {district_num}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        # Sort by district number
        members.sort(key=lambda m: int(re.search(r'\d+', m["district"]).group()))
        return members

    async def extract_member_name_from_page(self):
        """Extract the council member's name from their profile page."""
        try:
            # Try to find name in page title
            title = await self.page.title()
            if title:
                # Title might be like "District 1 - Joe Stapleton | Newport Beach"
                name_match = re.search(r'District\s+\d+\s*[-–]\s*([^|]+)', title)
                if name_match:
                    return name_match.group(1).strip()

            # Try to find name in h1 or h2 headers
            for selector in ["h1", "h2", ".council-member-name", ".member-name"]:
                elements = await self.page.query_selector_all(selector)
                for el in elements:
                    text = (await el.inner_text()).strip()
                    # Look for a name pattern (First Last)
                    if re.match(r'^[A-Z][a-z]+\s+[A-Z]', text) and len(text) < 50:
                        # Clean up any titles
                        name = re.sub(r'^(Mayor|Council\s*Member|Mayor Pro Tem)\s+', '', text, flags=re.IGNORECASE)
                        return name.strip()

            # Try extracting from page content
            text = await self.get_page_text()
            # Look for name pattern near the top
            first_500 = text[:500]
            name_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)\b', first_500)
            if name_match:
                return name_match.group(1)

        except Exception:
            pass
        return None

    async def detect_position_from_page(self):
        """Detect position from page content."""
        try:
            title = await self.page.title()
            if title:
                title_lower = title.lower()
                if "mayor pro tem" in title_lower:
                    return "Mayor Pro Tem"
                elif "mayor" in title_lower:
                    return "Mayor"

            text = await self.get_page_text()
            first_1000 = text[:1000].lower()

            if re.search(r'\bmayor\s+pro\s+tem\b', first_1000):
                return "Mayor Pro Tem"
            elif re.search(r'\bmayor\b', first_1000) and "pro tem" not in first_1000:
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

        print(f"    Found {len(members)} districts")

        for member in members:
            print(f"    Scraping: {member['district']}")
            result = await self.visit_page(member["url"], f"member_{member['district']}")

            if result.get("status") == "success":
                # Extract name from the district page
                raw_name = await self.extract_member_name_from_page()
                name = self.clean_name(raw_name)
                if not name:
                    print(f"      WARNING: Could not extract name for {member['district']}")
                    continue

                # Get info from KNOWN_TERMS (always use this for accuracy)
                member_info = self.get_member_info(name)
                if member_info:
                    position = member_info.get("position", "Councilmember")
                    district = member_info.get("district", member["district"])
                    term_start = member_info.get("term_start")
                    term_end = member_info.get("term_end")
                else:
                    position = await self.detect_position_from_page()
                    district = member["district"]
                    term_start, term_end = await self.extract_term_info()

                photo_url = await self.extract_photo_url(name, self.BASE_URL)
                bio = await self.extract_bio()

                member_email = None
                page_emails = result.get("emails", [])
                if page_emails:
                    member_email = self.match_email_to_name(
                        name, page_emails, self.CITY_DOMAIN
                    )
                    if not member_email and len(page_emails) == 1:
                        member_email = page_emails[0]

                result_phones = result.get("phones", [])
                member_phone = result_phones[0] if result_phones else (main_phones[0] if main_phones else None)

                print(f"      Found: {name} ({position})")

                self.add_council_member(
                    name=name,
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
            "meeting_time": "4:00 PM",
            "meeting_location": {
                "name": "City Council Chambers",
                "address": "100 Civic Center Drive",
                "city_state_zip": "Newport Beach, CA 92660"
            },
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(949) 644-3005",
                "email": "cityclerk@newportbeachca.gov"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": True,
                "written_email": True,
                "ecomment": True,
                "time_limit": "3 minutes per speaker",
                "email": "cityclerk@newportbeachca.gov",
            },
            "portals": {
                "granicus": self.GRANICUS_URL,
            },
            "council": {
                "size": 7,
                "districts": 7,
                "at_large": 0,
                "mayor_elected": False,  # Rotates among council
                "term_length": 4,
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["District 1", "District 3", "District 4", "District 6"],
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

                    # Filter for City Council meetings
                    row_upper = row_text.upper()
                    if "CITY COUNCIL" not in row_upper:
                        continue

                    # Parse date
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
                            video_url = f"https://newportbeach.granicus.com/player/clip/{clip_match.group(1)}?view_id=10"

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
