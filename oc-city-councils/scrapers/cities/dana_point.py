"""
Dana Point City Council Scraper
Dynamically discovers council members from website.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class DanaPointScraper(BaseScraper):
    """Dana Point - Granicus platform with YouTube video archives."""

    CITY_NAME = "Dana Point"
    PLATFORM = "granicus"
    CITY_DOMAIN = "danapoint.org"
    BASE_URL = "https://www.danapoint.org"
    COUNCIL_URL = "https://www.danapoint.org/department/city-council"
    YOUTUBE_CHANNEL = "https://www.youtube.com/channel/UCdNW_5KL2Q7lC-DFHUyFr7A"
    AGENDAS_URL = "https://www.danapoint.org/department/city-council/meetings-agendas-minutes"

    # Known term dates - Dana Point uses by-district elections
    # Districts 1, 2, 3 appointed 2022 (term ends 2026)
    # Districts 4, 5 elected 2020, re-elected 2024 (term ends 2028)
    KNOWN_TERMS = {
        "john gabbard": {"district": "District 1", "term_start": 2022, "term_end": 2026},
        "matthew pagano": {"district": "District 2", "term_start": 2022, "term_end": 2026},
        "jamey m. federico": {"district": "District 3", "term_start": 2022, "term_end": 2026},
        "jamey federico": {"district": "District 3", "term_start": 2022, "term_end": 2026},
        "mike frost": {"district": "District 4", "term_start": 2024, "term_end": 2028},
        "michael villar": {"district": "District 5", "term_start": 2024, "term_end": 2028},
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
            "agendas": self.AGENDAS_URL,
        }

    async def discover_members(self):
        """
        Discover council members from the main council page.
        Dana Point/Granicus pattern: Links to /City-Government/City-Council/Member-Name
        """
        members = []
        seen_urls = set()

        try:
            # Find all links that look like council member pages
            links = await self.page.query_selector_all('a[href*="City-Council/"]')

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                href_lower = href.lower()

                # Skip navigation/generic links
                skip_patterns = [
                    "mailto:", "#", "javascript:", "calendar", "agenda",
                    "minutes", "contact", "meeting", "archive"
                ]
                if any(skip in href_lower for skip in skip_patterns):
                    continue

                # Must be a member-specific URL (has name after City-Council/)
                if not re.search(r'/city-council/[a-z]+-[a-z]+', href_lower):
                    continue

                # Normalize URL
                full_url = urljoin(self.BASE_URL, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Extract name from link text
                name = text.strip()

                # Clean up name - remove position prefix
                for prefix in ["Mayor Pro Tem", "Mayor", "Council Member", "Councilmember"]:
                    if name.lower().startswith(prefix.lower()):
                        name = name[len(prefix):].strip()

                if len(name) < 4:
                    continue

                # Determine position from text
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
            "meeting_schedule": "1st and 3rd Tuesdays",
            "meeting_time": "6:00 PM",
            "meeting_location": {
                "name": "Council Chamber, City Hall",
                "address": "33282 Golden Lantern, Suite 210",
                "city_state_zip": "Dana Point, CA 92629"
            },
            "zoom": {},  # No Zoom - YouTube/TV only
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Cox", "channel": "855"}
            ],
            "live_stream": self.YOUTUBE_CHANNEL,
            "clerk": {
                "name": "Shayna Sharke",
                "title": "City Clerk",
                "phone": "(949) 248-3506",
                "email": "comment@danapoint.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # No Zoom public comment
                "ecomment": False,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "comment@danapoint.org",
                "deadline": "4:00 PM on meeting day"
            },
            "portals": {
                "youtube": self.YOUTUBE_CHANNEL,
                "agendas": self.AGENDAS_URL,
                "live_stream": self.YOUTUBE_CHANNEL,
            },
            "council": {
                "size": 5,
                "districts": 5,
                "at_large": 0,
                "mayor_elected": False,  # Mayor rotates among council
                "expanded_date": None
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["District 1", "District 2", "District 3"],
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

                # Get email
                member_email = None
                if result.get("emails"):
                    member_email = self.match_email_to_name(
                        member["name"],
                        result["emails"],
                        self.CITY_DOMAIN
                    )

                # Get district and position from page text
                district = None
                position = member["position"]
                text = await self.get_page_text()
                text_lower = text.lower()

                district_match = re.search(r'District\s+(\d+)', text, re.IGNORECASE)
                if district_match:
                    district = f"District {district_match.group(1)}"

                # Use KNOWN_TERMS for reliable district/term data
                member_info = self.get_member_info(member["name"])
                if member_info:
                    district = member_info.get("district") or district
                    term_start = member_info.get("term_start") or term_start
                    term_end = member_info.get("term_end") or term_end

                # Detect position from page content (first 1000 chars)
                first_part = text_lower[:1000]
                if "mayor pro tem" in first_part:
                    position = "Mayor Pro Tem"
                elif "mayor" in first_part and "pro tem" not in first_part:
                    position = "Mayor"

                # Also check page title
                title = await self.page.title()
                if title:
                    title_lower = title.lower()
                    if "mayor pro tem" in title_lower:
                        position = "Mayor Pro Tem"
                    elif "mayor" in title_lower and "pro tem" not in title_lower:
                        position = "Mayor"

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

        return self.get_results()
