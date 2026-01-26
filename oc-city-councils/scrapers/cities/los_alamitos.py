"""
Los Alamitos City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class LosAlamitosScraper(BaseScraper):
    """Los Alamitos - CivicPlus platform with /ID/Name-Format URLs."""

    CITY_NAME = "Los Alamitos"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cityoflosalamitos.org"
    BASE_URL = "https://cityoflosalamitos.org"
    COUNCIL_URL = "https://cityoflosalamitos.org/165/City-Council"
    YOUTUBE_CHANNEL = "https://www.youtube.com/@cityoflosal"
    TV_URL = "https://cityoflosalamitos.org/629/Watch-Los-Al-TV-3"
    AGENDAS_URL = "https://cityoflosalamitos.org/129/Agendas-Minutes"

    # Known term dates - Los Alamitos uses by-district elections
    # Districts 1, 2, 3 elected 2024 (term ends 2028)
    # Districts 4, 5 elected 2022 (term ends 2026)
    KNOWN_TERMS = {
        "tanya doby": {"district": "District 1", "term_start": 2024, "term_end": 2028},
        "jordan nefulda": {"district": "District 3", "term_start": 2024, "term_end": 2028},
        "gary loe": {"district": "District 2", "term_start": 2024, "term_end": 2028},
        "shelley hasselbrink": {"district": "District 4", "term_start": 2022, "term_end": 2026},
        "emily hibard": {"district": "District 5", "term_start": 2022, "term_end": 2026},
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
            "youtube": self.YOUTUBE_CHANNEL,
            "tv": self.TV_URL,
            "agendas": self.AGENDAS_URL,
        }

    async def discover_members(self):
        """
        Discover council members from the main council page.
        Los Alamitos URLs: /321/Tanya-Doby, /323/Jordan-Nefulda
        """
        members = []
        seen_urls = set()

        try:
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                # Skip non-member links
                if href.startswith(("mailto:", "javascript:", "#", "tel:")):
                    continue

                # Match URLs like /321/Tanya-Doby (numeric ID + First-Last name pattern)
                # Must be exactly First-Last or First-Middle-Last (2-3 parts, all capitalized)
                match = re.search(r'/(\d+)/([A-Z][a-z]+-[A-Z][a-z]+(?:-[A-Z][a-z]+)?)\b', href)
                if not match:
                    continue

                # Extract name from URL
                url_name = match.group(2)
                name_parts = url_name.split("-")

                # Must be 2-3 name parts (First Last or First Middle Last)
                if len(name_parts) < 2 or len(name_parts) > 3:
                    continue

                # Skip if any part is a common non-name word
                skip_words = [
                    "city", "council", "meeting", "agenda", "agendas", "minutes",
                    "contact", "district", "services", "department", "committee",
                    "management", "resources", "human", "development", "recreation",
                    "community", "standing", "disclosure", "statements", "fair",
                    "connected", "stay", "your", "news", "events", "calendar"
                ]
                if any(part.lower() in skip_words for part in name_parts):
                    continue

                # Normalize URL
                full_url = urljoin(self.BASE_URL, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Convert URL name to proper format
                name = url_name.replace("-", " ")

                # Determine initial position from link text
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

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "3rd Monday",
            "meeting_time": "6:00 PM",
            "meeting_location": {
                "name": "Council Chamber, City Hall",
                "address": "3191 Katella Avenue",
                "city_state_zip": "Los Alamitos, CA 90720"
            },
            "zoom": {},  # No Zoom - TV and YouTube streaming only
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Local Cable", "channel": "3"}
            ],
            "live_stream": self.YOUTUBE_CHANNEL,
            "clerk": {
                "name": "Windmera Quintanar, MMC",
                "title": "City Clerk",
                "phone": "(562) 431-3538 ext. 220",
                "email": "cityclerk@cityoflosalamitos.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # No Zoom participation
                "ecomment": False,
                "written_email": True,
                "time_limit": "5 minutes per speaker",
                "email": "cityclerk@cityoflosalamitos.org",
                "deadline": "3:00 PM on meeting day",
                "subject_line": "COUNCIL PUBLIC COMMENT"
            },
            "portals": {
                "agenda_center": self.AGENDAS_URL,
                "youtube": self.YOUTUBE_CHANNEL,
                "tv": self.TV_URL,
                "live_stream": self.YOUTUBE_CHANNEL,
            },
            "council": {
                "size": 5,
                "districts": 5,
                "at_large": 0,
                "mayor_elected": False,  # Mayor selected by council annually
                "expanded_date": None
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["District 4", "District 5"],
                "term_length": 4,
                "election_system": "by-district"
            }
        }
        return city_info

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")

        if main_result.get("status") != "success":
            print(f"    ERROR: Could not access council page")
            return self.get_results()

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
                photo_url = await self.extract_photo_url(member["name"], self.BASE_URL)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                member_email = None
                if result.get("emails"):
                    member_email = self.match_email_to_name(
                        member["name"], result["emails"], self.CITY_DOMAIN
                    )

                # Detect position from page
                text = await self.get_page_text()
                first_500 = text[:500].lower()
                position = member["position"]
                if "mayor pro tem" in first_500:
                    position = "Mayor Pro Tem"
                elif "mayor" in first_500 and "pro tem" not in first_500:
                    position = "Mayor"

                # Get district and term info from KNOWN_TERMS
                member_info = self.get_member_info(member["name"])
                if member_info:
                    district = member_info.get("district")
                    term_start = member_info.get("term_start") or term_start
                    term_end = member_info.get("term_end") or term_end
                else:
                    district = None

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

        return self.get_results()
