"""
Cypress City Council Scraper
Dynamically discovers council members from website.
Scrapes meeting archives from Destiny Hosted portal.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class CypressScraper(BaseScraper):
    """Cypress - CivicPlus/Granicus with individual profile pages + Destiny meetings."""

    CITY_NAME = "Cypress"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cypressca.org"
    BASE_URL = "https://www.cypressca.org"
    COUNCIL_URL = "https://www.cypressca.org/government/city-council"
    DESTINY_URL = "https://public.destinyhosted.com/agenda_publish.cfm?id=29773"
    STREAMING_URL = "https://www.cypressca.org/government/watch-cypress-channel-36"

    # Known term dates - Cypress transitioned to by-district in 2024
    # Districts 3, 4 elected 2024 (term ends 2028)
    # At-large seats elected 2022 (term ends 2026)
    # Rachel Strong Carnahan appointed Nov 2025 to fill vacancy (District 5, term ends 2026)
    KNOWN_TERMS = {
        "leo medrano": {"district": "District 4", "term_start": 2024, "term_end": 2028},
        "kyle chang": {"district": "District 3", "term_start": 2024, "term_end": 2028},
        "bonnie peat": {"district": "District 1", "term_start": 2022, "term_end": 2026},
        "david burke": {"district": "District 2", "term_start": 2022, "term_end": 2026},
        "rachel strong carnahan": {"district": "District 5", "term_start": 2025, "term_end": 2026},
        "rachel strong": {"district": "District 5", "term_start": 2025, "term_end": 2026},
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
            "destiny": self.DESTINY_URL,
            "streaming": self.STREAMING_URL,
        }

    async def discover_members(self):
        """
        Discover council members from the main council page.
        Cypress pattern: Links to council-member-{name} or mayor-pro-tem-{name} pages.
        """
        members = []
        seen_urls = set()

        try:
            # Find all links that look like council member pages
            links = await self.page.query_selector_all('a[href*="/city-council/"]')

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                href_lower = href.lower()

                # Skip navigation/generic links
                skip_patterns = [
                    "mailto:", "#", "javascript:", "calendar", "agenda",
                    "minutes", "policies", "contact", "commission"
                ]
                if any(skip in href_lower for skip in skip_patterns):
                    continue

                # Must be a member-specific URL
                if not re.search(r'/city-council/(council-member-|mayor-pro-tem-|mayor-)[a-z]', href_lower):
                    continue

                # Normalize URL for deduplication
                full_url = urljoin(self.BASE_URL, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Extract name from link text (remove position prefix)
                name = text.strip()
                for prefix in ["Mayor Pro Tem", "Mayor", "Council Member", "Councilmember"]:
                    if name.lower().startswith(prefix.lower()):
                        name = name[len(prefix):].strip()

                if len(name) < 4:
                    continue

                # Initial position guess from text (will verify from individual page)
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

    async def detect_position_from_page(self, initial_position="Councilmember"):
        """
        Detect position from the current member's page.
        NOTE: Cypress doesn't update URLs when positions change (Mayor rotates yearly),
        so we TRUST the initial position from the main page which is current.
        URLs may have outdated positions from when the page was created.
        """
        # Trust the main page's position detection - it reflects the CURRENT position
        # Individual page URLs may have old positions (e.g., someone who WAS Mayor Pro Tem
        # but is now a Councilmember still has mayor-pro-tem in their URL)
        return initial_position

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "2nd and 4th Mondays",
            "meeting_time": "6:00 PM",
            "meeting_location": {
                "name": "Council Chambers",
                "address": "5275 Orange Avenue",
                "city_state_zip": "Cypress, CA 90630"
            },
            "zoom": {},  # No Zoom - streaming only
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Spectrum", "channel": "36"}
            ],
            "live_stream": self.STREAMING_URL,
            "clerk": {
                "title": "City Clerk",
                "phone": "(714) 229-6685",
                "email": "cityclerk@cypressca.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # No Zoom public comment
                "ecomment": False,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "cityclerk@cypressca.org",
                "deadline": "3:00 PM on meeting day"
            },
            "portals": {
                "destiny": self.DESTINY_URL,
                "live_stream": self.STREAMING_URL,
            },
            "council": {
                "size": 5,
                "districts": 5,  # Transitioned to by-district in 2024
                "at_large": 0,
                "mayor_elected": False,  # Mayor rotates among council
                "expanded_date": None
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["District 1", "District 2", "District 5"],
                "term_length": 4,
                "election_system": "by-district"
            }
        }
        return city_info

    async def scrape_meetings(self):
        """Scrape meeting data from Destiny Hosted portal."""
        meetings = []
        seen_keys = set()

        print(f"    Scraping meetings from Destiny portal...")

        try:
            await self.page.goto(self.DESTINY_URL, timeout=60000, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # Destiny shows meetings in a table format
            # Look for rows with City Council meetings
            rows = await self.page.query_selector_all('tr')

            for row in rows:
                try:
                    text = await row.inner_text()
                    if "city council" not in text.lower():
                        continue

                    # Extract date - pattern like "January 12, 2026" or "January 12"
                    date_match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})?", text)
                    if not date_match:
                        continue

                    month_str, day_str, year_str = date_match.groups()
                    if not year_str:
                        year_str = "2026"  # Default to current year
                    date_str = f"{month_str} {day_str}, {year_str}"

                    # Determine meeting type
                    if "special" in text.lower():
                        name = "City Council Special Meeting"
                    else:
                        name = "City Council Regular Meeting"

                    # Look for video link
                    video_link = await row.query_selector('a[href*="video"], a:has-text("Video")')
                    video_url = None
                    if video_link:
                        video_url = await video_link.get_attribute("href")

                    # Look for agenda link
                    agenda_link = await row.query_selector('a[href*="agenda"], a:has-text("Agenda")')
                    agenda_url = None
                    if agenda_link:
                        agenda_url = await agenda_link.get_attribute("href")

                    key = f"{date_str}|{name}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    meetings.append({
                        "name": name,
                        "date": date_str,
                        "video_url": video_url,
                        "agenda_url": agenda_url,
                        "minutes_url": None
                    })
                except Exception:
                    continue

            def parse_date(d):
                try:
                    return datetime.strptime(d, "%B %d, %Y")
                except ValueError:
                    return datetime.min
            meetings.sort(key=lambda m: parse_date(m["date"]), reverse=True)
            print(f"      Found {len(meetings)} City Council meetings")

        except Exception as e:
            self.results["errors"].append(f"scrape_meetings: {str(e)}")

        return meetings

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        # Visit main council page
        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")

        if main_result.get("status") != "success":
            print(f"    ERROR: Could not access council page")
            return self.get_results()

        main_phones = main_result.get("phones", [])

        # Discover members dynamically
        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} members")

        # Scrape each member page
        for member in members:
            print(f"    Scraping member: {member['name']}")
            result = await self.visit_page(member["url"], f"member_{member['name']}")

            if result.get("status") == "success":
                position = await self.detect_position_from_page(member["position"])

                photo_url = await self.extract_photo_url(member["name"], self.BASE_URL)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                # Get email
                member_email = None
                if result.get("emails"):
                    member_email = self.match_email_to_name(
                        member["name"],
                        result["emails"],
                        self.CITY_DOMAIN
                    )

                # Get district from page or KNOWN_TERMS
                district = None
                text = await self.get_page_text()
                district_match = re.search(r'District\s+(\d+)', text, re.IGNORECASE)
                if district_match:
                    district = f"District {district_match.group(1)}"

                # Use KNOWN_TERMS for reliable district/term data
                member_info = self.get_member_info(member["name"])
                if member_info:
                    district = member_info.get("district") or district
                    term_start = member_info.get("term_start") or term_start
                    term_end = member_info.get("term_end") or term_end

                result_phones = result.get("phones", [])
                member_phone = result_phones[0] if result_phones else (main_phones[0] if main_phones else None)

                print(f"      Position: {position}")
                print(f"      District: {district or 'Not found'}")
                print(f"      Email: {member_email or 'Not found'}")

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
                # Get term info even if page visit failed
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

        # Scrape meetings from Destiny portal
        meetings = await self.scrape_meetings()
        self.results["meetings"] = meetings

        return self.get_results()
