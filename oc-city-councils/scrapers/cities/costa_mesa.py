"""
Costa Mesa City Council Scraper
Dynamically discovers council members from website.
Note: May return 403 to direct requests - use Firefox with Playwright.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class CostaMesaScraper(BaseScraper):
    """Costa Mesa - Granicus platform (may block - use Firefox stealth)."""

    CITY_NAME = "Costa Mesa"
    PLATFORM = "granicus"
    CITY_DOMAIN = "costamesaca.gov"
    BASE_URL = "https://www.costamesaca.gov"
    COUNCIL_URL = "https://www.costamesaca.gov/government/mayor-city-council"
    GRANICUS_URL = "https://costamesa.granicus.com/ViewPublisher.php?view_id=5"

    # Known term dates for Costa Mesa council members (at-large, 4-year staggered terms)
    # 2022 elected -> 2026, 2024 elected -> 2028
    KNOWN_TERMS = {
        "john stephens": {"district": "At-Large", "term_start": 2024, "term_end": 2028},
        "manuel chavez": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "andrea marr": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "arlis reynolds": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "jeff pettis": {"district": "At-Large", "term_start": 2024, "term_end": 2028},
        "loren gameros": {"district": "At-Large", "term_start": 2024, "term_end": 2028},
        "mike buley": {"district": "At-Large", "term_start": 2024, "term_end": 2028},
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
            "granicus": self.GRANICUS_URL,
        }

    async def discover_members(self):
        """
        Discover council members from the main council page.
        Costa Mesa/Granicus pattern: Links to individual member pages.
        """
        members = []
        seen_urls = set()

        try:
            # Find all links that look like council member pages
            links = await self.page.query_selector_all('a[href*="mayor-city-council/"]')

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                # Skip navigation/generic links
                href_lower = href.lower()
                skip_url_patterns = [
                    "mailto:", "#", "javascript:", "calendar", "agenda", "minutes",
                    "goals", "objectives", "policies", "compensation", "contact",
                    "disclosures", "notices", "past-mayors", "public-notices"
                ]
                if any(skip in href_lower for skip in skip_url_patterns):
                    continue

                # Must be a member-specific URL with name pattern (mayor-, council-member-)
                if not re.search(r'/mayor-city-council/(mayor-[a-z]|council-member-[a-z])', href_lower):
                    continue

                # Normalize URL for deduplication
                full_url = urljoin(self.BASE_URL, href)

                # Skip duplicates
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Extract name from link text
                name = text.strip()

                # Skip if name looks like a navigation element
                skip_names = ["city council", "mayor", "contact", "meeting", "agenda", "more"]
                if name.lower() in skip_names:
                    continue

                # Clean up name - remove position prefix if present
                for prefix in ["Mayor Pro Tem", "Mayor", "Council Member", "Councilmember"]:
                    if name.lower().startswith(prefix.lower()):
                        name = name[len(prefix):].strip()

                if len(name) < 4:
                    continue

                # Determine position from URL/text
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

    async def detect_position_from_page(self, name):
        """Detect position from the current member's page."""
        try:
            # Most reliable: Check the URL pattern for the actual member path
            url = self.page.url.lower()
            # Extract just the last path segment (the member-specific part)
            path_parts = url.split('/')
            last_segment = path_parts[-1] if path_parts else ""

            if last_segment.startswith("mayor-pro-tem-"):
                return "Mayor Pro Tem"
            elif last_segment.startswith("mayor-") and "pro-tem" not in last_segment:
                return "Mayor"
            elif last_segment.startswith("council-member-"):
                return "Councilmember"

            # Check page title
            title = await self.page.title()
            title_lower = title.lower() if title else ""

            if "mayor pro tem" in title_lower:
                return "Mayor Pro Tem"
            elif "mayor" in title_lower and "pro tem" not in title_lower:
                return "Mayor"

            # Check h1 heading
            h1 = await self.page.query_selector("h1")
            if h1:
                h1_text = (await h1.inner_text()).lower()
                if "mayor pro tem" in h1_text:
                    return "Mayor Pro Tem"
                elif "mayor" in h1_text and "pro tem" not in h1_text:
                    return "Mayor"

        except Exception as e:
            self.results["errors"].append(f"detect_position: {str(e)}")

        return "Councilmember"

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        # Visit main council page
        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")

        if main_result.get("status") != "success":
            print(f"    ERROR: Could not access council page - {main_result.get('error')}")
            return self.get_results()

        main_phones = main_result.get("phones", [])

        # Discover members dynamically
        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    WARNING: No council members found on main page!")
            print("    Trying alternative discovery method...")
            # Try looking for any links with name patterns
            return self.get_results()

        print(f"    Found {len(members)} members")

        # Scrape each member page
        for member in members:
            print(f"    Scraping member: {member['name']}")
            result = await self.visit_page(member["url"], f"member_{member['name']}")

            if result.get("status") == "success":
                # Detect position from individual page (more accurate)
                position = await self.detect_position_from_page(member["name"])

                # Extract rich data
                photo_url = await self.extract_photo_url(member["name"], self.BASE_URL)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                # Get email from page using name matching
                member_email = None
                if result.get("emails"):
                    member_email = self.match_email_to_name(
                        member["name"],
                        result["emails"],
                        self.CITY_DOMAIN
                    )

                # Get district from page text
                district = None
                text = await self.get_page_text()
                district_match = re.search(r'District\s+(\d+)', text, re.IGNORECASE)
                if district_match:
                    district = f"District {district_match.group(1)}"

                result_phones = result.get("phones", [])
                member_phone = result_phones[0] if result_phones else (main_phones[0] if main_phones else None)

                print(f"      Position: {position}")
                print(f"      District: {district or 'Not found'}")
                print(f"      Email: {member_email or 'Not found'}")

                # Always use KNOWN_TERMS for term/district data
                member_info = self.get_member_info(member["name"])
                if member_info:
                    district = member_info.get("district")
                    term_start = member_info.get("term_start")
                    term_end = member_info.get("term_end")

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
                # Page failed, add with basic info from KNOWN_TERMS
                member_info = self.get_member_info(member["name"])
                self.add_council_member(
                    name=member["name"],
                    position=member["position"],
                    profile_url=member["url"],
                    district=member_info.get("district") if member_info else None,
                    term_start=member_info.get("term_start") if member_info else None,
                    term_end=member_info.get("term_end") if member_info else None,
                )

        # Final email matching pass
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
            "meeting_schedule": "1st and 3rd Tuesdays",
            "meeting_time": "6:00 PM",
            "meeting_location": {
                "name": "City Hall Council Chamber",
                "address": "77 Fair Drive",
                "city_state_zip": "Costa Mesa, CA 92626"
            },
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(714) 754-5225",
                "email": "cityclerk@costamesaca.gov"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": True,
                "written_email": True,
                "ecomment": True,
                "time_limit": "3 minutes per speaker",
            },
            "portals": {
                "granicus": self.GRANICUS_URL,
            },
            "council": {
                "size": 7,
                "districts": 0,
                "at_large": 7,
                "mayor_elected": False,  # Rotates among council
                "term_length": 4,
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["3 at-large seats"],
                "election_system": "at-large",
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
                            video_url = f"https://costamesa.granicus.com/player/clip/{clip_match.group(1)}?view_id=5"

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
