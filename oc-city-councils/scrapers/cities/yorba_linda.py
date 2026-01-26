"""
Yorba Linda City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class YorbaLindaScraper(BaseScraper):
    """Yorba Linda - CivicPlus platform with dynamic member discovery."""

    CITY_NAME = "Yorba Linda"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "yorbalindaca.gov"
    BASE_URL = "https://www.yorbalindaca.gov"
    COUNCIL_URL = "https://www.yorbalindaca.gov/190/City-Council"
    GRANICUS_URL = "https://yorbalinda.granicus.com/ViewPublisher.php?view_id=7"
    AGENDAS_URL = "https://www.yorbalindaca.gov/197/Council-Meeting-Agendas-Minutes"

    # Known term dates - Yorba Linda is fully at-large
    # 3 seats elected 2024 (term ends 2028): Campbell, Huang, Singh
    # 2 seats elected 2022 (term ends 2026): Rodriguez, Lim
    KNOWN_TERMS = {
        "carlos rodriguez": {"term_start": 2022, "term_end": 2026},
        "peggy huang": {"term_start": 2024, "term_end": 2028},
        "tara campbell": {"term_start": 2024, "term_end": 2028},
        "janice lim": {"term_start": 2022, "term_end": 2026},
        "shivinder singh": {"term_start": 2024, "term_end": 2028},
    }

    def get_member_info(self, name):
        """Get term info for a member."""
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
            "granicus": self.GRANICUS_URL,
            "agendas": self.AGENDAS_URL,
        }

    async def discover_members(self):
        """
        Discover council members from the main council page.
        CivicPlus pattern: links contain /XXX/Name-Title format
        """
        members = []
        seen_urls = set()

        try:
            links = await self.page.query_selector_all("a[href]")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                # Skip empty, mailto, or already seen
                if not href or href.startswith("mailto:") or href in seen_urls:
                    continue

                # CivicPlus member pages have numeric ID pattern: /123/Name
                if not re.search(r'/\d+/', href):
                    continue

                text_lower = text.lower()

                # Must contain a position keyword
                if not any(kw in text_lower for kw in ["mayor", "council"]):
                    continue

                # Skip generic links
                if any(skip in text_lower for skip in ["email all", "contact", "agendas", "meetings"]):
                    continue

                # Determine position
                if "mayor pro tem" in text_lower:
                    position = "Mayor Pro Tem"
                elif "mayor" in text_lower:
                    position = "Mayor"
                else:
                    position = "Councilmember"

                # Extract clean name - remove position prefixes
                name = text
                for prefix in ["Mayor Pro Tem", "Mayor Pro Tempore", "Vice Mayor",
                               "Mayor", "Councilmember", "Council Member"]:
                    name = re.sub(rf"^{prefix}\s*", "", name, flags=re.IGNORECASE)
                name = name.strip()

                # Remove trailing position (e.g., "John Smith, Mayor" -> "John Smith")
                name = re.sub(r',\s*(Mayor|Council\s*member|Vice\s*Mayor).*$', '', name, flags=re.IGNORECASE)
                name = name.strip()

                # Skip if name too short or looks wrong
                if len(name) < 4 or name.lower() in ["city council"]:
                    continue

                url = urljoin(self.BASE_URL, href)
                seen_urls.add(href)

                # Avoid duplicate names
                if not any(m["name"].lower() == name.lower() for m in members):
                    members.append({"name": name, "position": position, "url": url})
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
            "meeting_time": "6:30 PM",
            "meeting_location": {
                "name": "City Council Chambers",
                "address": "4845 Casa Loma Avenue",
                "city_state_zip": "Yorba Linda, CA 92886"
            },
            "zoom": {},  # No Zoom - email public comment only
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Local Cable", "channel": "3"},
                {"provider": "AT&T U-Verse", "channel": "99"}
            ],
            "live_stream": self.GRANICUS_URL,
            "clerk": {
                "title": "City Clerk",
                "phone": "(714) 961-7100",
                "email": "cityclerk@yorbalindaca.gov"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # No remote live participation
                "ecomment": False,
                "written_email": True,
                "time_limit": "5 minutes per speaker",
                "email": "cityclerk@yorbalindaca.gov",
                "notes": "Include full name, city of residence, phone number, and agenda item"
            },
            "portals": {
                "agenda_center": self.AGENDAS_URL,
                "granicus": self.GRANICUS_URL,
                "live_stream": self.GRANICUS_URL,
            },
            "council": {
                "size": 5,
                "districts": 0,
                "at_large": 5,  # All at-large
                "mayor_elected": False,  # Mayor selected by council annually
                "expanded_date": None,
                "notes": "All members elected at-large"
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["At-Large (2 seats)"],
                "term_length": 4,
                "election_system": "at-large",
                "term_limits": "Three consecutive 4-year terms"
            }
        }
        return city_info

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        # Visit main council page
        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        # Discover members dynamically
        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} members")

        # Scrape each member
        for member in members:
            data = await self.scrape_member_page(
                member, self.BASE_URL, self.CITY_DOMAIN, main_phones
            )

            # Get term info from KNOWN_TERMS
            member_info = self.get_member_info(member["name"])
            if member_info:
                data["term_start"] = member_info.get("term_start")
                data["term_end"] = member_info.get("term_end")

            self.add_council_member(**data)

        # Final email matching pass
        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)

        # Scrape city-level info
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        return self.get_results()
