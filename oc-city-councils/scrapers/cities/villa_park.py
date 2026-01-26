"""
Villa Park City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class VillaParkScraper(BaseScraper):
    """Villa Park - WordPress-style site with bio pages."""

    CITY_NAME = "Villa Park"
    PLATFORM = "wordpress"
    CITY_DOMAIN = "villapark.org"
    BASE_URL = "https://villapark.org"
    COUNCIL_URL = "https://villapark.org/council-and-committees/city-council"
    AGENDAS_URL = "https://villapark.org/Council-and-Committees/Council-Agenda-and-Minutes"

    # Known term dates - Villa Park is fully at-large
    # 3 seats elected 2022 (term ends 2026)
    # 2 seats elected 2024 (term ends 2028)
    KNOWN_TERMS = {
        "jordan wu": {"term_start": 2022, "term_end": 2026},
        "robert frackelton": {"term_start": 2024, "term_end": 2028},
        "nicol jones": {"term_start": 2022, "term_end": 2026},
        "kelly mcbride": {"term_start": 2024, "term_end": 2028},
        "crystal miles": {"term_start": 2022, "term_end": 2026},
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
            "agendas": self.AGENDAS_URL,
        }

    async def extract_photos_for_members(self, members):
        """Extract photos from main council page and match to members."""
        try:
            imgs = await self.page.query_selector_all("img")

            # Skip patterns for logos/icons
            skip_patterns = ["logo", "icon", "banner", "background", "footer", "header",
                           "facebook", "instagram", "twitter", "youtube", "seal", "badge",
                           "menu", "arrow", "button", "search"]

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
                            src = urljoin(self.BASE_URL, src)
                        member["photo_url"] = src
                        print(f"      Photo found: {name}")
                        break

        except Exception as e:
            self.results["errors"].append(f"extract_photos: {str(e)}")

        return members

    async def discover_members(self):
        """
        Discover council members from the main council page.
        Villa Park pattern: URLs end in -Name-Bio format.
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

                # Villa Park member pages have -Bio at the end
                if "-Bio" not in href:
                    continue

                # Skip duplicates by URL
                if href in seen_names:
                    continue

                # Extract name from text (e.g., "Jordan Wu Bio" -> "Jordan Wu")
                name = text.replace("Bio", "").strip()

                if len(name) < 3:
                    continue

                # Try to determine position from the page context
                # We'll refine this by looking at page content
                position = "Councilmember"

                seen_names.add(href)
                url = urljoin(self.BASE_URL, href)
                members.append({"name": name, "position": position, "url": url})
                print(f"      Found: {name}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def detect_positions(self, members):
        """Detect Mayor and Mayor Pro Tem from page text."""
        try:
            text = await self.get_page_text()
            text_lower = text.lower()

            for member in members:
                name = member["name"]
                name_lower = name.lower()

                # Strategy: Find all occurrences of the name and check context
                # Look for patterns like "Name\nMayor" or "Mayor\nName"

                # Check for Mayor Pro Tem first (more specific)
                pro_tem_patterns = [
                    rf'{re.escape(name_lower)}\s*[\n,\-]?\s*mayor\s+pro\s+tem',
                    rf'mayor\s+pro\s+tem\s*[\n,\-]?\s*{re.escape(name_lower)}',
                ]
                found_pro_tem = any(re.search(p, text_lower) for p in pro_tem_patterns)

                if found_pro_tem:
                    member["position"] = "Mayor Pro Tem"
                    continue

                # Check for Mayor (use negative lookahead, avoid lookbehind)
                # Pattern: "Name Mayor" where Mayor is NOT followed by "pro"
                # Or: "Mayor Name" where "pro tem" doesn't appear before Mayor
                mayor_pattern_after = rf'{re.escape(name_lower)}\s*[\n,\-]?\s*mayor(?!\s+pro)'
                mayor_match = re.search(mayor_pattern_after, text_lower)

                if mayor_match:
                    member["position"] = "Mayor"
                    continue

                # Also check "Mayor Name" but verify it's not "Mayor Pro Tem Name"
                mayor_before_pattern = rf'mayor\s+{re.escape(name_lower)}'
                pro_tem_before = rf'mayor\s+pro\s+tem\s+{re.escape(name_lower)}'
                if re.search(mayor_before_pattern, text_lower) and not re.search(pro_tem_before, text_lower):
                    member["position"] = "Mayor"

        except Exception as e:
            self.results["errors"].append(f"detect_positions: {str(e)}")

        return members

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "4th Tuesday",
            "meeting_time": "6:30 PM",
            "meeting_location": {
                "name": "Council Chambers",
                "address": "17855 Santiago Boulevard",
                "city_state_zip": "Villa Park, CA 92861"
            },
            "zoom": {},  # No Zoom - email public comment only
            "phone_numbers": [
                {"type": "City Hall", "number": "(714) 998-1500"}
            ],
            "tv_channels": [],  # No cable TV broadcast
            "live_stream": None,  # No live stream
            "clerk": {
                "title": "City Clerk",
                "phone": "(714) 998-1500",
                "email": "info@villapark.org"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # No remote live participation
                "ecomment": False,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "info@villapark.org",
                "deadline": "3:00 PM on meeting day"
            },
            "portals": {
                "agenda_center": self.AGENDAS_URL,
            },
            "council": {
                "size": 5,
                "districts": 0,
                "at_large": 5,  # All at-large
                "mayor_elected": False,  # Mayor selected by council
                "expanded_date": None,
                "notes": "All members elected at-large"
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["At-Large (3 seats)"],
                "term_length": 4,
                "election_system": "at-large",
                "term_limits": "Two full terms"
            }
        }
        return city_info

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        # Visit main council page with extra long timeout (site is slow)
        main_result = await self.visit_page(self.COUNCIL_URL, "council_main", timeout=90000)
        main_phones = main_result.get("phones", [])
        main_emails = main_result.get("emails", [])

        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        # Detect positions from page text
        members = await self.detect_positions(members)

        # Extract photos from main page (before visiting individual pages)
        print("    Extracting photos from main page...")
        members = await self.extract_photos_for_members(members)

        print(f"    Found {len(members)} members")
        for m in members:
            print(f"      - {m['name']} ({m['position']})")

        # Scrape each member page
        for member in members:
            data = await self.scrape_member_page(
                member, self.BASE_URL, self.CITY_DOMAIN, main_phones
            )

            # If no email found on member page, try main page emails
            if not data.get("email") and main_emails:
                data["email"] = self.match_email_to_name(
                    member["name"], main_emails, self.CITY_DOMAIN
                )

            # Use photo from main page if member page didn't find one
            if not data.get("photo_url") and member.get("photo_url"):
                data["photo_url"] = member["photo_url"]

            # Get term info from KNOWN_TERMS
            member_info = self.get_member_info(member["name"])
            if member_info:
                data["term_start"] = member_info.get("term_start")
                data["term_end"] = member_info.get("term_end")

            self.add_council_member(**data)

        # Final pass to match any remaining emails
        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)

        # Scrape city-level info
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        return self.get_results()
