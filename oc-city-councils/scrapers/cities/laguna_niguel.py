"""
Laguna Niguel City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class LagunaNiguelScraper(BaseScraper):
    """Laguna Niguel - CivicPlus with individual profile pages + YouTube video archive."""

    CITY_NAME = "Laguna Niguel"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "cityoflagunaniguel.org"
    BASE_URL = "https://www.cityoflagunaniguel.org"
    COUNCIL_URL = "https://www.cityoflagunaniguel.org/396/Mayor-City-Council"
    YOUTUBE_URL = "https://www.youtube.com/cityoflagunaniguel"

    # Known term dates - Laguna Niguel has 5 at-large seats, 4-year staggered terms
    KNOWN_TERMS = {
        "gene johns": {"district": "At-Large", "term_start": 2024, "term_end": 2028},
        "kelly jennings": {"district": "At-Large", "term_start": 2024, "term_end": 2028},
        "ray gennawey": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "stephanie oddo": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "stephanie winstead": {"district": "At-Large", "term_start": 2024, "term_end": 2028},
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
            "youtube": self.YOUTUBE_URL,
        }

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st and 3rd Tuesdays",
            "meeting_time": "7:00 PM",
            "meeting_location": {
                "name": "Council Chambers",
                "address": "30111 Crown Valley Parkway",
                "city_state_zip": "Laguna Niguel, CA 92677"
            },
            "zoom": {},
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Cox", "channel": "853"},
                {"provider": "AT&T U-Verse", "channel": "99"}
            ],
            "live_stream": self.YOUTUBE_URL,
            "clerk": {
                "title": "City Clerk's Office",
                "phone": "(949) 362-4373",
                "email": "council@cityoflagunaniguel.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,
                "ecomment": False,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "council@cityoflagunaniguel.org"
            },
            "portals": {
                "granicus": None,
                "ecomment": None,
                "live_stream": self.YOUTUBE_URL,
            },
            "council": {
                "size": 5,
                "districts": 0,
                "at_large": 5,
                "mayor_elected": False,
                "expanded_date": None
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["Councilmember", "Councilmember"],
                "term_length": 4,
                "election_system": "at-large"
            }
        }
        return city_info

    async def discover_members(self):
        """Discover council members from the main council page."""
        members = []
        seen_urls = set()

        try:
            # Look for links to member profile pages
            links = await self.page.query_selector_all('a[href*="/"]')

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                href_lower = href.lower()

                # Skip non-member pages
                skip_patterns = ["mailto:", "#", "agenda", "minutes", "calendar", "meeting", "contact"]
                if any(skip in href_lower for skip in skip_patterns):
                    continue

                # Must contain member-related keywords
                if not re.search(r'(mayor|council-?member)', href_lower):
                    continue

                # Must not be the main council page
                if href_lower.endswith("/mayor-city-council") or "/396/" in href_lower:
                    continue

                full_url = urljoin(self.BASE_URL, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Extract name from link text
                name = text.strip()
                for prefix in ["Mayor Pro Tem", "Mayor", "Council Member", "Councilmember"]:
                    if name.lower().startswith(prefix.lower()):
                        name = name[len(prefix):].strip()

                if len(name) < 4:
                    continue

                # Determine position
                position = "Councilmember"
                if "mayor-pro-tem" in href_lower or "pro tem" in text.lower():
                    position = "Mayor Pro Tem"
                elif "mayor" in href_lower.split("/")[-1].split("-")[0] or text.lower().startswith("mayor"):
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

        return self.get_results()
