"""
Westminster City Council Scraper
Uses stealth mode - site blocks bots.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class WestminsterScraper(BaseScraper):
    """Westminster - Granicus platform, requires Firefox stealth mode."""

    CITY_NAME = "Westminster"
    PLATFORM = "granicus"
    CITY_DOMAIN = "westminster-ca.gov"
    BASE_URL = "https://www.westminster-ca.gov"
    COUNCIL_URL = "https://www.westminster-ca.gov/government/mayor-and-city-council-members"
    GRANICUS_URL = "https://westminster.granicus.com/ViewPublisher.php?view_id=1"

    # Known term dates - Westminster has 4 districts + at-large mayor, 4-year staggered terms
    KNOWN_TERMS = {
        "chi charlie nguyen": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "charlie nguyen": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "namquan nguyen": {"district": "District 4", "term_start": 2022, "term_end": 2026},
        "amy phan west": {"district": "District 1", "term_start": 2022, "term_end": 2026},
        "carlos manzo": {"district": "District 2", "term_start": 2024, "term_end": 2028},
        "mark nguyen": {"district": "District 3", "term_start": 2024, "term_end": 2028},
    }

    def get_member_info(self, name):
        """Get district and term info for a member."""
        name_lower = name.lower().strip()
        for known_name, info in self.KNOWN_TERMS.items():
            if known_name in name_lower or name_lower in known_name:
                return info
            # Check last name match (careful with "Nguyen" - common name)
            known_parts = known_name.split()
            name_parts = name_lower.split()
            # Match on first name for Nguyens
            if len(known_parts) > 1 and len(name_parts) > 1:
                if known_parts[0] in name_parts or name_parts[0] in known_parts:
                    if known_parts[-1] == name_parts[-1]:  # Same last name
                        return info
        return None

    def get_urls(self):
        return {
            "council": self.COUNCIL_URL,
            "granicus": self.GRANICUS_URL,
        }

    async def discover_members(self):
        """
        Discover council members from the main page.
        Westminster pattern: URLs contain mayor- or council-member- prefix.
        """
        members = []
        seen_names = set()

        try:
            links = await self.page.query_selector_all("a[href]")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text:
                    continue

                # Clean href - remove fragments and tracking params
                clean_href = href.split("#")[0].split("?")[0].rstrip("/")

                # Westminster member pages have specific patterns in URL
                href_lower = clean_href.lower()
                if not any(pattern in href_lower for pattern in
                          ["mayor-chi", "council-member-", "vice-mayor-"]):
                    continue

                # Skip non-member pages by URL pattern
                if any(skip in href_lower for skip in
                      ["code-of-ethics", "videos", "agendas", "minutes", "meetings"]):
                    continue

                # Determine position from URL (be specific to avoid false matches)
                if "/mayor-chi" in href_lower:
                    position = "Mayor"
                elif "/vice-mayor-" in href_lower:
                    position = "Vice Mayor"
                elif "/council-member-" in href_lower:
                    position = "Councilmember"
                else:
                    position = "Councilmember"

                # Extract name - clean up thoroughly
                name = text
                for prefix in ["Mayor", "Vice Mayor", "Council Member", "Councilmember"]:
                    name = re.sub(rf"^{prefix}\s*", "", name, flags=re.IGNORECASE)
                name = re.sub(r'\s*[-,]?\s*District\s*\d*', '', name, flags=re.IGNORECASE)
                name = re.sub(r',+$', '', name)  # Remove trailing commas
                name = name.strip()

                if len(name) < 3:
                    continue

                # Normalize for duplicate check
                name_key = name.lower().replace(",", "").strip()
                if name_key in seen_names:
                    continue
                seen_names.add(name_key)

                url = urljoin(self.BASE_URL, clean_href)
                members.append({"name": name, "position": position, "url": url})
                print(f"      Found: {name} ({position})")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")
        print("    NOTE: Use --stealth --browser firefox if getting blocked")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found! Try stealth mode.")
            return self.get_results()

        print(f"    Found {len(members)} members")

        for member in members:
            data = await self.scrape_member_page(
                member, self.BASE_URL, self.CITY_DOMAIN, main_phones
            )
            # Always use KNOWN_TERMS for district/term data
            member_info = self.get_member_info(data.get("name", member["name"]))
            if member_info:
                data["district"] = member_info.get("district")
                data["term_start"] = member_info.get("term_start")
                data["term_end"] = member_info.get("term_end")
            self.add_council_member(**data)

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
            "meeting_schedule": "2nd and 4th Wednesdays",
            "meeting_time": "7:00 PM",
            "meeting_location": {
                "name": "City Council Chambers",
                "address": "8200 Westminster Boulevard",
                "city_state_zip": "Westminster, CA 92683"
            },
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(714) 898-3311",
                "email": "cityclerk@westminster-ca.gov"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": True,
                "written_email": True,
                "ecomment": True,
                "time_limit": "3 minutes per speaker",
                "email": "cityclerk@westminster-ca.gov",
            },
            "portals": {
                "granicus": self.GRANICUS_URL,
            },
            "council": {
                "size": 5,
                "districts": 4,
                "at_large": 1,  # Mayor is at-large
                "mayor_elected": True,
                "term_length": 4,
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["Mayor", "District 1", "District 4"],
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
                            video_url = f"https://westminster.granicus.com/player/clip/{clip_match.group(1)}?view_id=1"

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
