"""
Orange City Council Scraper
Dynamically discovers council members from website.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class OrangeScraper(BaseScraper):
    """City of Orange - Granicus platform, members listed as text with mailto links."""

    CITY_NAME = "Orange"
    PLATFORM = "granicus"
    CITY_DOMAIN = "cityoforange.org"
    BASE_URL = "https://www.cityoforange.org"
    COUNCIL_URL = "https://www.cityoforange.org/our-city/local-government/city-council"
    GRANICUS_URL = "https://cityoforange.granicus.com/ViewPublisher.php?view_id=2"

    def get_urls(self):
        return {
            "council": self.COUNCIL_URL,
            "granicus": self.GRANICUS_URL,
        }

    async def discover_members(self):
        """
        Discover council members from page text and mailto links.

        Orange lists members as text blocks:
        - "Mayor pro tem / Denis Bilodeau / Term: 2022-2026 / District 4"
        - "Councilmember / Arianna Barrios / Term: 2022-2026 / District 1"

        Emails are in mailto: links.
        """
        members = []
        seen_names = set()

        try:
            text = await self.get_page_text()

            # Get all mailto links for email matching
            mailto_links = await self.page.query_selector_all('a[href^="mailto:"]')
            emails = {}
            for link in mailto_links:
                href = await link.get_attribute("href") or ""
                email = href.replace("mailto:", "").split("?")[0].strip()
                if email and "@cityoforange.org" in email:
                    # Extract last name from email for matching
                    local = email.split("@")[0].lower()
                    emails[local] = email

            # Normalize whitespace
            text_normalized = re.sub(r'\s+', ' ', text)

            # Pattern for council members in text
            # Format: "Position Name Term: YYYY-YYYY District X"
            # Example: "Mayor pro tem Denis Bilodeau Term: 2022-2026 District 4"
            patterns = [
                # Mayor Pro Tem pattern
                (r'Mayor\s+pro\s+tem\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+Term:\s*(\d{4})-(\d{4})\s+District\s+(\d+)', "Mayor Pro Tem"),
                # Councilmember pattern
                (r'Councilmember\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+Term:\s*(\d{4})-(\d{4})\s+District\s+(\d+)', "Councilmember"),
            ]

            for pattern, position in patterns:
                for match in re.finditer(pattern, text_normalized):
                    name = match.group(1).strip()
                    term_start = int(match.group(2))
                    term_end = int(match.group(3))
                    district = f"District {match.group(4)}"

                    if name.lower() in seen_names:
                        continue
                    seen_names.add(name.lower())

                    # Match email by last name
                    name_parts = name.lower().split()
                    last_name = name_parts[-1]
                    first_initial = name_parts[0][0]

                    email = None
                    # Try various email patterns
                    for local, full_email in emails.items():
                        if last_name in local:
                            email = full_email
                            break
                        if f"{first_initial}{last_name}" == local:
                            email = full_email
                            break

                    members.append({
                        "name": name,
                        "position": position,
                        "district": district,
                        "email": email,
                        "term_start": term_start,
                        "term_end": term_end,
                    })
                    print(f"      Found: {name} ({position}, {district})")

            # Also find Mayor from separate pattern
            mayor_match = re.search(r'Meet Mayor\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text_normalized)
            if mayor_match:
                name = mayor_match.group(1).strip()
                if name.lower() not in seen_names:
                    seen_names.add(name.lower())

                    # Try to get term from "2024-2026 term" text
                    term_match = re.search(r'(\d{4})-(\d{4})\s+term', text_normalized)
                    term_start = int(term_match.group(1)) if term_match else None
                    term_end = int(term_match.group(2)) if term_match else None

                    # Find Mayor's profile link to get email
                    mayor_url = None
                    profile_links = await self.page.query_selector_all('a')
                    for link in profile_links:
                        href = await link.get_attribute("href") or ""
                        if "mayor-" in href.lower() and name.split()[-1].lower() in href.lower():
                            mayor_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                            break

                    members.insert(0, {  # Mayor first
                        "name": name,
                        "position": "Mayor",
                        "district": "At-Large",
                        "email": None,  # Will get from profile page
                        "term_start": term_start,
                        "term_end": term_end,
                        "profile_url": mayor_url,
                    })
                    print(f"      Found: {name} (Mayor)")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def extract_photos(self):
        """Extract photos for council members from the page."""
        photos = {}
        try:
            # Look for images in council member sections
            imgs = await self.page.query_selector_all('img')
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

                # Try to match to a council member by alt text or filename
                src_lower = src.lower()
                # Check for common name patterns in src or alt
                for name_part in ["slater", "bilodeau", "gutierrez", "barrios",
                                  "gyllenhammer", "dumitru", "tavoularis"]:
                    if name_part in src_lower or name_part in alt:
                        photos[name_part] = src
                        break

        except Exception as e:
            print(f"      Photo extraction error: {e}")
        return photos

    def find_photo_for_member(self, name, photos):
        """Find photo URL for a member."""
        name_lower = name.lower()
        for part in name_lower.split():
            if part in photos:
                return photos[part]
        return None

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

        # Extract photos from the main page
        photos = await self.extract_photos()
        print(f"    Found {len(photos)} photos")

        for member in members:
            email = member.get("email")
            profile_url = member.get("profile_url") or self.COUNCIL_URL
            photo_url = self.find_photo_for_member(member["name"], photos)

            # If Mayor has profile page, visit it to get email
            if member["position"] == "Mayor" and member.get("profile_url"):
                print(f"    Visiting Mayor's profile for email...")
                result = await self.visit_page(member["profile_url"], "mayor_profile")
                if result.get("emails"):
                    email = result["emails"][0]
                # Try to get photo from mayor's profile
                if not photo_url:
                    photo_url = await self.extract_photo_url(member["name"], self.BASE_URL)

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                district=member.get("district"),
                email=email,
                phone=main_phones[0] if main_phones else None,
                profile_url=profile_url,
                photo_url=photo_url,
                term_start=member.get("term_start"),
                term_end=member.get("term_end"),
            )

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
            "meeting_time": "7:00 PM",
            "meeting_location": {
                "name": "City Council Chamber",
                "address": "300 E. Chapman Avenue",
                "city_state_zip": "Orange, CA 92866"
            },
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(714) 744-5500",
                "email": "cityclerk@cityoforange.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": True,
                "written_email": True,
                "ecomment": True,
                "time_limit": "3 minutes per speaker",
                "email": "cityclerk@cityoforange.org",
            },
            "portals": {
                "granicus": self.GRANICUS_URL,
            },
            "council": {
                "size": 7,
                "districts": 6,
                "at_large": 1,  # Mayor is at-large
                "mayor_elected": True,  # Directly elected
                "term_length": 4,
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["Mayor", "District 1", "District 4", "District 5"],
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
                            video_url = f"https://cityoforange.granicus.com/player/clip/{clip_match.group(1)}?view_id=2"

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
