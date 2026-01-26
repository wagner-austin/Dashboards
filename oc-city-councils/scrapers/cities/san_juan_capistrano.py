"""
San Juan Capistrano City Council Scraper
Dynamically discovers council members from website.
"""
import re
from ..base import BaseScraper


class SanJuanCapistranoScraper(BaseScraper):
    """San Juan Capistrano - text pattern matching for council members."""

    CITY_NAME = "San Juan Capistrano"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "sanjuancapistrano.org"
    BASE_URL = "https://sanjuancapistrano.org"
    COUNCIL_URL = "https://sanjuancapistrano.org/318/City-Council"
    DIRECTORY_URL = "https://sanjuancapistrano.org/Directory.aspx?did=35"
    GRANICUS_URL = "https://sjc.granicus.com/ViewPublisher.php?view_id=3"
    AGENDAS_URL = "https://sanjuancapistrano.org/189/Public-Meetings"

    # Known term dates - SJC uses by-district elections (5 districts since 2016)
    # Districts 1, 4, 5 elected 2024 (term ends 2028)
    # Districts 2, 3 elected 2022 (term ends 2026)
    KNOWN_TERMS = {
        "john campbell": {"district": "District 3", "term_start": 2022, "term_end": 2026},
        "john taylor": {"district": "District 5", "term_start": 2024, "term_end": 2028},
        "troy a. bourne": {"district": "District 2", "term_start": 2022, "term_end": 2026},
        "troy bourne": {"district": "District 2", "term_start": 2022, "term_end": 2026},
        "sergio farias": {"district": "District 1", "term_start": 2024, "term_end": 2028},
        "howard hart": {"district": "District 4", "term_start": 2024, "term_end": 2028},
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
            "directory": self.DIRECTORY_URL,
            "granicus": self.GRANICUS_URL,
            "agendas": self.AGENDAS_URL,
        }

    async def extract_photos_from_cards(self, members):
        """Extract photos from card layout - find images in same container as member names."""
        try:
            # SJC uses card layout with ImageRepository URLs
            # Find all containers that might have member cards
            cards = await self.page.query_selector_all('.widget, .card, article, [class*="member"], [class*="council"]')

            if not cards:
                # Fallback: try to find any container with both name and image
                cards = await self.page.query_selector_all('div')

            for member in members:
                name = member["name"]
                last_name = name.split()[-1].lower()

                for card in cards:
                    try:
                        card_text = (await card.inner_text() or "").lower()

                        # Check if this card contains the member's name
                        if last_name not in card_text:
                            continue

                        # Found a card with this member's name - look for image
                        imgs = await card.query_selector_all("img")
                        for img in imgs:
                            src = await img.get_attribute("src") or ""

                            # Skip icons/logos
                            if any(p in src.lower() for p in ["logo", "icon", "seal", "badge"]):
                                continue

                            # Accept ImageRepository or portrait images
                            if "ImageRepository" in src or "portrait" in src.lower() or ".jpg" in src.lower():
                                if not src.startswith("http"):
                                    src = f"{self.BASE_URL}/{src.lstrip('/')}"
                                member["photo_url"] = src
                                print(f"      Photo found: {name}")
                                break

                        if member.get("photo_url"):
                            break  # Found photo, move to next member

                    except Exception:
                        continue

        except Exception as e:
            self.results["errors"].append(f"extract_photos: {str(e)}")

        return members

    async def discover_members(self):
        """Discover council members by matching name patterns on page.

        Format on SJC page: "Name" followed by "Position, District X"
        e.g., "John Campbell" then "Mayor, District 3"
        """
        members = []
        seen_names = set()

        try:
            text = await self.get_page_text()
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)

            # Pattern: Name followed by position/district info
            # e.g., "John Campbell Mayor, District 3" or "Sergio Farias District 1"
            name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)'

            # Find Mayor Pro Tem - "Name Mayor Pro Tem, District X"
            for match in re.finditer(rf'{name_pattern}\s+Mayor\s+Pro\s+Tem[,\s]+District\s+\d', text):
                name = match.group(1).strip()
                if name.lower() not in seen_names and len(name.split()) >= 2:
                    seen_names.add(name.lower())
                    members.append({"name": name, "position": "Mayor Pro Tem"})
                    print(f"      Found: {name} (Mayor Pro Tem)")

            # Find Mayor (not Pro Tem) - "Name Mayor, District X"
            for match in re.finditer(rf'{name_pattern}\s+Mayor[,\s]+District\s+\d', text):
                name = match.group(1).strip()
                if name.lower() not in seen_names and len(name.split()) >= 2:
                    seen_names.add(name.lower())
                    members.append({"name": name, "position": "Mayor"})
                    print(f"      Found: {name} (Mayor)")

            # Find Council Members - "Name District X" (no explicit title)
            for match in re.finditer(rf'{name_pattern}\s+District\s+\d', text):
                name = match.group(1).strip()
                if name.lower() not in seen_names and len(name.split()) >= 2:
                    seen_names.add(name.lower())
                    members.append({"name": name, "position": "Councilmember"})
                    print(f"      Found: {name} (Councilmember)")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st and 3rd Tuesdays",
            "meeting_time": "5:00 PM",
            "meeting_location": {
                "name": "City Council Chamber",
                "address": "32400 Paseo Adelanto",
                "city_state_zip": "San Juan Capistrano, CA 92675"
            },
            "zoom": {},  # No Zoom - phone-in for public comment
            "phone_numbers": [
                {"type": "Public Comment Line", "number": "(949) 493-1172"}
            ],
            "tv_channels": [],  # No cable TV broadcast
            "live_stream": self.GRANICUS_URL,
            "clerk": {
                "name": "Maria Morris",
                "title": "City Clerk",
                "phone": "(949) 443-6310",
                "email": "cityclerk@sanjuancapistrano.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": True,  # Phone-in available
                "ecomment": False,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "cityclerk@sanjuancapistrano.org",
                "phone": "(949) 493-1172",
                "notes": "Call public comment line at start of meeting to be placed in queue"
            },
            "portals": {
                "agenda_center": self.AGENDAS_URL,
                "granicus": self.GRANICUS_URL,
                "live_stream": self.GRANICUS_URL,
            },
            "council": {
                "size": 5,
                "districts": 5,
                "at_large": 0,
                "mayor_elected": False,  # Mayor selected by council
                "expanded_date": None,
                "notes": "By-district elections since 2016"
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["District 2", "District 3"],
                "term_length": 4,
                "election_system": "by-district"
            }
        }
        return city_info

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        # Extract photos from card layout
        print("    Extracting photos from cards...")
        members = await self.extract_photos_from_cards(members)

        print(f"    Found {len(members)} members")

        # Visit directory page to get emails
        print("    Getting emails from directory...")
        dir_result = await self.visit_page(self.DIRECTORY_URL, "directory")
        dir_emails = dir_result.get("emails", [])
        dir_phones = dir_result.get("phones", [])

        print(f"      Found {len(dir_emails)} emails in directory")

        # Add members with matched emails
        for member in members:
            email = self.match_email_to_name(member["name"], dir_emails, self.CITY_DOMAIN)
            phone = dir_phones[0] if dir_phones else (main_phones[0] if main_phones else None)

            # Get district and term info from KNOWN_TERMS
            member_info = self.get_member_info(member["name"])
            district = member_info.get("district") if member_info else None
            term_start = member_info.get("term_start") if member_info else None
            term_end = member_info.get("term_end") if member_info else None

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                district=district,
                email=email,
                phone=phone,
                photo_url=member.get("photo_url"),
                term_start=term_start,
                term_end=term_end,
            )

        # Scrape city-level info
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        return self.get_results()
