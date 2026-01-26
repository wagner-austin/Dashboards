"""
La Palma City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class LaPalmaScraper(BaseScraper):
    """La Palma - CivicPlus platform with name/position text pattern."""

    CITY_NAME = "La Palma"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "lapalmaca.gov"
    BASE_URL = "https://www.lapalmaca.gov"
    COUNCIL_URL = "https://www.lapalmaca.gov/66/City-Council"

    # Known term dates - La Palma transitioned to by-district in 2024
    # At-Large seats elected 2022 (term ends 2026)
    # District seats elected 2024 (term ends 2028)
    KNOWN_TERMS = {
        "nitesh p. patel": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "nitesh patel": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "debbie s. baker": {"district": "District 1", "term_start": 2024, "term_end": 2028},
        "debbie baker": {"district": "District 1", "term_start": 2024, "term_end": 2028},
        "mark i. waldman": {"district": "District 5", "term_start": 2024, "term_end": 2028},
        "mark waldman": {"district": "District 5", "term_start": 2024, "term_end": 2028},
        "janet keo conklin": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "janet keo": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "vikesh p. patel": {"district": "District 3", "term_start": 2024, "term_end": 2028},
        "vikesh patel": {"district": "District 3", "term_start": 2024, "term_end": 2028},
    }

    def get_member_info(self, name):
        """Get district and term info for a member."""
        name_lower = name.lower().strip()
        # First try exact match or substring match
        for known_name, info in self.KNOWN_TERMS.items():
            if known_name == name_lower or name_lower == known_name:
                return info
            if known_name in name_lower or name_lower in known_name:
                return info
        # For Patel family, use first name to distinguish
        if "patel" in name_lower:
            if "vikesh" in name_lower:
                return self.KNOWN_TERMS.get("vikesh patel")
            if "nitesh" in name_lower:
                return self.KNOWN_TERMS.get("nitesh patel")
        return None

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st Tuesday",
            "meeting_time": "6:30 PM",
            "meeting_location": {
                "name": "La Palma Civic Center",
                "address": "7822 Walker Street",
                "city_state_zip": "La Palma, CA 90623"
            },
            "zoom": {},  # No Zoom - audio streaming only
            "phone_numbers": [],
            "tv_channels": [],  # No TV broadcast
            "live_stream": "https://www.lapalmaca.gov/72/Agendas-and-Minutes",  # Audio only
            "clerk": {
                "name": "Kimberly Kenney",
                "title": "City Clerk",
                "phone": "(714) 690-3334",
                "email": "Kimberlyk@cityoflapalma.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # No Zoom, audio only for viewing
                "ecomment": False,
                "written_email": True,
                "time_limit": "5 minutes per speaker",
                "email": "Kimberlyk@cityoflapalma.org",
                "deadline": "5:00 PM on meeting day"
            },
            "portals": {
                "agenda_center": "https://www.lapalmaca.gov/72/Agendas-and-Minutes",
                "live_stream": "https://www.lapalmaca.gov/72/Agendas-and-Minutes",
            },
            "council": {
                "size": 5,
                "districts": 3,  # Districts 1, 3, 5 (transitioned 2024)
                "at_large": 2,
                "mayor_elected": False,  # Mayor rotates among council
                "expanded_date": None
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["At-Large (2 seats)"],
                "term_length": 4,
                "election_system": "mixed"
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

    async def discover_members(self):
        """
        Discover council members from the main council page.
        La Palma lists members with name, position, and district on separate lines.
        """
        members = []
        seen_names = set()

        try:
            text = await self.get_page_text()

            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)

            # La Palma format: "Position (District) Name"
            # e.g., "Mayor (At-Large) Nitesh P. Patel"
            # e.g., "Mayor Pro Tem (District 1) Debbie S. Baker"
            # e.g., "Council Member (District 5) Mark I. Waldman"
            # Pattern matches: Position, optional district info, then name
            pattern = r'([Mm]ayor(?:\s+[Pp]ro\s+[Tt]em)?|[Cc]ouncil\s*[Mm]ember)\s+\([^)]+\)\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)'

            for match in re.finditer(pattern, text):
                position_raw = match.group(1).strip()
                name = match.group(2).strip()

                # Validate name structure
                name_parts = name.split()
                if len(name_parts) < 2:
                    continue

                # Skip common words
                skip_first_words = [
                    "and", "or", "the", "one", "to", "for", "in", "on", "at",
                    "city", "council", "mayor", "member", "with", "has", "was",
                    "elected", "appointed", "serves"
                ]
                if name_parts[0].lower() in skip_first_words:
                    continue

                # Skip if already seen
                if name.lower() in seen_names:
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

                members.append({
                    "name": name,
                    "position": position,
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
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        # Extract photos from main page
        print("    Extracting photos...")
        members = await self.extract_photos_for_members(members)

        print(f"    Found {len(members)} members")

        # La Palma uses a shared council email - find it
        shared_email = None
        for email in main_emails:
            if "citycouncil" in email.lower() or "council" in email.lower():
                shared_email = email
                break

        for member in members:
            # Try individual email first, fall back to shared
            email = self.match_email_to_name(member["name"], main_emails, self.CITY_DOMAIN)

            # Get district and term info from KNOWN_TERMS
            member_info = self.get_member_info(member["name"])
            district = member_info.get("district") if member_info else None
            term_start = member_info.get("term_start") if member_info else None
            term_end = member_info.get("term_end") if member_info else None

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                district=district,
                email=email or shared_email,
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
