"""
La Habra City Council Scraper
Dynamically discovers council members from website.
"""
import re
from ..base import BaseScraper


class LaHabraScraper(BaseScraper):
    """La Habra - CivicPlus platform with PDF bios (no profile pages)."""

    CITY_NAME = "La Habra"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "lahabraca.gov"
    BASE_URL = "https://www.lahabraca.gov"
    COUNCIL_URL = "https://www.lahabraca.gov/153/City-Council"
    LIVE_STREAM_URL = "https://www.lahabraca.gov/356/Archived-Council-Videos"

    # Known term dates - La Habra is at-large
    # 3 seats elected 2022 (term ends 2026)
    # 2 seats elected 2024 (term ends 2028)
    KNOWN_TERMS = {
        "jose medrano": {"term_start": 2022, "term_end": 2026},
        "james gomez": {"term_start": 2022, "term_end": 2026},
        "daren nigsarian": {"term_start": 2022, "term_end": 2026},
        "rose espinoza": {"term_start": 2024, "term_end": 2028},
        "delwin lampkin": {"term_start": 2024, "term_end": 2028},
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
            "live_stream": self.LIVE_STREAM_URL,
        }

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st and 3rd Mondays",
            "meeting_time": "6:30 PM",
            "meeting_location": {
                "name": "Council Chamber",
                "address": "100 E. La Habra Boulevard",
                "city_state_zip": "La Habra, CA 90631"
            },
            "zoom": {},  # No Zoom - live stream only
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Local Cable", "channel": "3"}
            ],
            "live_stream": self.LIVE_STREAM_URL,
            "clerk": {
                "title": "City Clerk",
                "phone": "(562) 383-4030",
                "email": "cc@lahabraca.gov"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # No Zoom, viewing + email only
                "ecomment": False,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "cc@lahabraca.gov",
                "deadline": "5:00 PM on meeting day"
            },
            "portals": {
                "agenda_center": "https://www.lahabraca.gov/AgendaCenter/City-Council-2",
                "live_stream": self.LIVE_STREAM_URL,
            },
            "council": {
                "size": 5,
                "districts": 0,
                "at_large": 5,
                "mayor_elected": False,  # Mayor rotates among council
                "expanded_date": None
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["At-Large (3 seats)"],
                "term_length": 4,
                "election_system": "at-large"
            }
        }
        return city_info

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
        La Habra lists all members on one page with photos.
        """
        members = []
        seen_names = set()

        try:
            text = await self.get_page_text()

            # Normalize whitespace (collapse multiple spaces/newlines into single space)
            # This helps match "Name,\nMayor" patterns
            text = re.sub(r'\s+', ' ', text)

            # Find council member patterns in text
            # La Habra format: "Name, Position" (comma separator)
            # Match patterns like "Jose Medrano, Mayor" or "James Gomez, Mayor Pro Tem"
            # Use strict capitalization for names (First Last) to avoid matching "COUNCIL Jose"
            # Position matching is case-insensitive via alternation
            pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*,?\s*([Mm]ayor(?:\s+[Pp]ro\s+[Tt]em)?|[Cc]ouncil\s*[Mm]ember)'

            for match in re.finditer(pattern, text):
                name = match.group(1).strip()
                position_raw = match.group(2).strip()

                # Validate name structure - must be proper name (First Last)
                name_parts = name.split()
                if len(name_parts) < 2:
                    continue

                # Skip if first word is a common word (not a name)
                skip_first_words = [
                    "and", "or", "the", "one", "to", "for", "in", "on", "at",
                    "pro", "tem", "acts", "who", "each", "another", "elected",
                    "city", "council", "mayor", "member", "with", "has", "was"
                ]
                if name_parts[0].lower() in skip_first_words:
                    continue

                # Each name part must be at least 2 characters
                if any(len(part) < 2 for part in name_parts):
                    continue

                # Name must be at least 5 characters total (e.g., "Al Li")
                if len(name) < 5:
                    continue

                # Skip if already seen
                if name.lower() in seen_names:
                    continue

                # Skip generic words that aren't names
                skip_words = ["city", "council", "meeting", "agenda", "mayor", "member"]
                if any(w in name.lower() for w in skip_words):
                    continue

                # Normalize position
                pos_lower = position_raw.lower()
                if "mayor pro tem" in pos_lower:
                    position = "Mayor Pro Tem"
                elif "mayor" in pos_lower:
                    position = "Mayor"
                else:
                    position = "Councilmember"

                seen_names.add(name.lower())

                # Match email
                email = self.match_email_to_name(name, main_emails, self.CITY_DOMAIN)

                members.append({
                    "name": name,
                    "position": position,
                    "email": email,
                })
                print(f"      Found: {name} ({position})")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

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

        # La Habra uses a shared council email - assign to all members
        shared_email = None
        for email in main_emails:
            if "citycouncil" in email.lower() or "council" in email.lower():
                shared_email = email
                break

        for member in members:
            # Get term info from KNOWN_TERMS
            member_info = self.get_member_info(member["name"])
            term_start = member_info.get("term_start") if member_info else None
            term_end = member_info.get("term_end") if member_info else None

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                email=member.get("email") or shared_email,
                phone=main_phones[0] if main_phones else None,
                profile_url=self.COUNCIL_URL,  # All on main page
                photo_url=member.get("photo_url"),
                term_start=term_start,
                term_end=term_end,
            )

        # Scrape city-level info
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        return self.get_results()
