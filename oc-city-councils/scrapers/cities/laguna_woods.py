"""
Laguna Woods City Council Scraper
Dynamically discovers council members from website.
"""
import re
from ..base import BaseScraper


class LagunaWoodsScraper(BaseScraper):
    """Laguna Woods - WordPress-style site with all members on main page."""

    CITY_NAME = "Laguna Woods"
    PLATFORM = "wordpress"
    CITY_DOMAIN = "cityoflagunawoods.org"
    BASE_URL = "https://www.cityoflagunawoods.org"
    COUNCIL_URL = "https://www.cityoflagunawoods.org/city-council/"
    YOUTUBE_CHANNEL = "https://www.youtube.com/@cityoflagunawoods"
    AGENDAS_URL = "https://www.cityoflagunawoods.org/current-agendas/"

    # Known term dates - Laguna Woods is at-large
    # 2 seats elected 2022 (term ends 2026)
    # 3 seats elected 2024 (term ends 2028)
    KNOWN_TERMS = {
        "annie mccary": {"term_start": 2022, "term_end": 2026},
        "pearl lee": {"term_start": 2024, "term_end": 2028},
        "cynthia conners": {"term_start": 2024, "term_end": 2028},
        "shari l. horne": {"term_start": 2024, "term_end": 2028},
        "shari horne": {"term_start": 2024, "term_end": 2028},
        "carol moore": {"term_start": 2022, "term_end": 2026},
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
            "youtube": self.YOUTUBE_CHANNEL,
            "agendas": self.AGENDAS_URL,
        }

    async def extract_photos_for_members(self, members):
        """Extract photos from main page and match to members."""
        try:
            imgs = await self.page.query_selector_all("img")

            # Skip patterns for logos/icons
            skip_patterns = ["logo", "icon", "banner", "background", "footer", "header",
                           "facebook", "instagram", "twitter", "youtube", "seal", "badge"]

            for member in members:
                name = member["name"]
                last_name = name.split()[-1].lower()
                first_name = name.split()[0].lower()

                for img in imgs:
                    src = await img.get_attribute("src") or ""
                    alt = (await img.get_attribute("alt") or "").lower()

                    # Skip icons/logos
                    if any(p in src.lower() for p in skip_patterns):
                        continue

                    # Match by name in alt or src
                    if last_name in alt or last_name in src.lower() or first_name in alt:
                        # Make absolute URL
                        if src and not src.startswith("http"):
                            src = f"{self.BASE_URL}/{src.lstrip('/')}"
                        member["photo_url"] = src
                        print(f"      Photo found: {name}")
                        break

        except Exception as e:
            self.results["errors"].append(f"extract_photos: {str(e)}")

        return members

    async def discover_members(self, main_emails):
        """
        Discover council members from the main council page.
        Laguna Woods lists all members on main page with position before name.
        """
        members = []
        seen_names = set()

        try:
            text = await self.get_page_text()

            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)

            # Laguna Woods format: "Position Name – details"
            # e.g., "Mayor Annie McCary – Elected in 2022..."
            # e.g., "Mayor Pro Tem Pearl Lee – Elected in 2024..."
            # e.g., "Councilmember Shari L. Horne – ..."
            # Name pattern handles names like "McCary" (Mc + capital + lowercase)
            # or normal names, plus optional middle initial
            name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+(?:Mc)?[A-Z][a-z]+)'

            # Match each position pattern separately to avoid conflicts
            patterns = [
                (rf'[Mm]ayor\s+[Pp]ro\s+[Tt]em\s+{name_pattern}', "Mayor Pro Tem"),
                (rf'[Cc]ouncil\s*[Mm]ember\s+{name_pattern}', "Councilmember"),
            ]

            for pattern, position in patterns:
                for match in re.finditer(pattern, text):
                    name = match.group(1).strip()

                    # Validate name structure
                    name_parts = name.split()
                    if len(name_parts) < 2:
                        continue

                    # Skip common words
                    skip_first_words = [
                        "and", "or", "the", "one", "to", "for", "in", "on", "at",
                        "city", "council", "mayor", "member", "with", "has", "was",
                        "elected", "appointed", "serves", "meeting", "contact", "pro", "tem"
                    ]
                    if name_parts[0].lower() in skip_first_words:
                        continue

                    # Skip if already seen
                    if name.lower() in seen_names:
                        continue

                    seen_names.add(name.lower())

                    # Match email from main page
                    email = self.match_email_to_name(name, main_emails, self.CITY_DOMAIN)

                    members.append({
                        "name": name,
                        "position": position,
                        "email": email,
                    })
                    print(f"      Found: {name} ({position})")

            # Now find the Mayor (making sure we don't match "Mayor Pro Tem")
            # Use negative lookahead to exclude "Mayor Pro Tem"
            mayor_pattern = rf'[Mm]ayor\s+(?![Pp]ro){name_pattern}'
            for match in re.finditer(mayor_pattern, text):
                name = match.group(1).strip()

                name_parts = name.split()
                if len(name_parts) < 2:
                    continue

                skip_first_words = ["pro", "tem", "and", "or", "the"]
                if name_parts[0].lower() in skip_first_words:
                    continue

                if name.lower() in seen_names:
                    continue

                seen_names.add(name.lower())
                email = self.match_email_to_name(name, main_emails, self.CITY_DOMAIN)

                members.append({
                    "name": name,
                    "position": "Mayor",
                    "email": email,
                })
                print(f"      Found: {name} (Mayor)")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "3rd Wednesday",
            "meeting_time": "2:00 PM",
            "meeting_location": {
                "name": "City Hall",
                "address": "24264 El Toro Road",
                "city_state_zip": "Laguna Woods, CA 92637"
            },
            "zoom": {
                "note": "Zoom available for viewing and public comment (see agenda for details)"
            },
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Local Cable", "channel": "31"}
            ],
            "live_stream": self.YOUTUBE_CHANNEL,
            "clerk": {
                "title": "City Clerk",
                "phone": "(949) 639-0500",
                "email": "cityhall@cityoflagunawoods.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": True,  # Can speak via Zoom
                "ecomment": False,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "cityhall@cityoflagunawoods.org",
                "deadline": "2:00 PM on meeting day"
            },
            "portals": {
                "agenda_center": self.AGENDAS_URL,
                "youtube": self.YOUTUBE_CHANNEL,
                "live_stream": self.YOUTUBE_CHANNEL,
            },
            "council": {
                "size": 5,
                "districts": 0,
                "at_large": 5,
                "mayor_elected": False,  # Mayor selected by council
                "expanded_date": None
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["At-Large (2 seats)"],
                "term_length": 4,
                "election_system": "at-large"
            }
        }
        return city_info

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])
        main_emails = main_result.get("emails", [])

        print("    Discovering council members...")
        members = await self.discover_members(main_emails)

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        # Extract photos from main page
        print("    Extracting photos...")
        members = await self.extract_photos_for_members(members)

        print(f"    Found {len(members)} members")

        for member in members:
            # Get term info from KNOWN_TERMS
            member_info = self.get_member_info(member["name"])
            term_start = member_info.get("term_start") if member_info else None
            term_end = member_info.get("term_end") if member_info else None

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                email=member.get("email"),
                phone=main_phones[0] if main_phones else None,
                profile_url=self.COUNCIL_URL,
                photo_url=member.get("photo_url"),
                term_start=term_start,
                term_end=term_end,
            )

        # Scrape city-level info
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        return self.get_results()
