"""
Lake Forest City Council Scraper
Names are ALL CAPS on page: "MAYOR ROBERT PEQUEÑO", "COUNCIL MEMBER MARK TETTEMER"
"""
import re
import unicodedata
from urllib.parse import urljoin
from ..base import BaseScraper


class LakeForestScraper(BaseScraper):
    """Lake Forest - Custom PHP site with ALL CAPS names."""

    CITY_NAME = "Lake Forest"
    PLATFORM = "custom"
    CITY_DOMAIN = "lakeforestca.gov"
    BASE_URL = "https://www.lakeforestca.gov"
    COUNCIL_URL = "https://www.lakeforestca.gov/city_government/city_council/index.php"
    YOUTUBE_CHANNEL = "https://www.youtube.com/@CityofLakeForestCA1991"
    FACEBOOK_PAGE = "https://www.facebook.com/lakeforestca"
    AGENDAS_URL = "https://www.lakeforestca.gov/city_government/agendas_and_minutes/index.php"

    KNOWN_TERMS = {
        "robert pequeño": {"district": "District 5", "term_start": 2024, "term_end": 2028},
        "robert pequeno": {"district": "District 5", "term_start": 2024, "term_end": 2028},
        "doug cirbo": {"district": "District 1", "term_start": 2024, "term_end": 2028},
        "mark tettemer": {"district": "District 4", "term_start": 2022, "term_end": 2026},
        "scott voigts": {"district": "District 3", "term_start": 2022, "term_end": 2026},
        "benjamin yu": {"district": "District 2", "term_start": 2022, "term_end": 2026},
    }

    def get_member_info(self, name):
        name_lower = self._normalize(name)
        for known_name, info in self.KNOWN_TERMS.items():
            if self._normalize(known_name) in name_lower or name_lower in self._normalize(known_name):
                return info
        return None

    def get_urls(self):
        return {
            "council": self.COUNCIL_URL,
            "youtube": self.YOUTUBE_CHANNEL,
            "facebook": self.FACEBOOK_PAGE,
            "agendas": self.AGENDAS_URL,
        }

    def _normalize(self, text):
        """Remove accents and normalize."""
        normalized = unicodedata.normalize('NFKD', text)
        return ''.join(c for c in normalized if not unicodedata.combining(c)).lower()

    async def discover_members(self):
        """Discover members from page text patterns."""
        members = []
        text = await self.get_page_text()

        # Pattern: "MAYOR/MAYOR PRO TEM/COUNCIL MEMBER FIRSTNAME LASTNAME"
        # Names are ALL CAPS, last name must be 3+ chars
        patterns = [
            (r'MAYOR\s+PRO\s+TEM\s+([A-Z]{2,})\s+([A-Z]{3,})', "Mayor Pro Tem"),
            (r'(?<!PRO\s)(?<!TEM\s)MAYOR\s+([A-Z]{2,})\s+([A-Z\u00D1]{3,})', "Mayor"),
            (r'COUNCIL\s+MEMBER\s+([A-Z]{2,})\s+([A-Z]{2,})', "Councilmember"),
        ]

        seen = set()
        for pattern, position in patterns:
            for match in re.finditer(pattern, text):
                first = match.group(1).strip().title()
                last = match.group(2).strip().title()

                # Skip if looks like position text
                if first.lower() in ["pro", "tem", "member", "council"]:
                    continue
                if last.lower() in ["pro", "tem", "member", "council"]:
                    continue

                name = f"{first} {last}"

                # Normalize for dedup
                name_key = self._normalize(name)
                if name_key in seen:
                    continue
                seen.add(name_key)

                # Find email for this member
                last_lower = self._normalize(last)
                email = None
                email_match = re.search(rf'[a-z]{last_lower}@{self.CITY_DOMAIN}', text, re.I)
                if email_match:
                    email = email_match.group(0)

                members.append({
                    "name": name,
                    "position": position,
                    "email": email,
                })
                print(f"      Found: {name} ({position})")

        return members

    async def extract_photos(self, members):
        """Extract photos from page - check both img tags and CSS background-images."""
        try:
            # First try regular img tags
            imgs = await self.page.query_selector_all("img")
            skip = ["logo", "icon", "seal", "badge", "footer", "header", "menu", "arrow"]

            for member in members:
                last_name = self._normalize(member["name"].split()[-1])

                for img in imgs:
                    src = await img.get_attribute("src") or ""
                    alt = (await img.get_attribute("alt") or "").lower()

                    if any(s in src.lower() for s in skip):
                        continue

                    if last_name in alt or last_name in self._normalize(src):
                        if not src.startswith("http"):
                            src = urljoin(self.BASE_URL, src)
                        member["photo_url"] = src
                        print(f"      Photo (img): {member['name']}")
                        break

            # If no photos found via img tags, try CSS background-images
            members_without_photos = [m for m in members if not m.get("photo_url")]
            if members_without_photos:
                print("      Checking CSS background-images...")
                # Use JavaScript to find all elements with background-image CSS
                bg_images = await self.page.evaluate("""
                    () => {
                        const results = [];
                        const elements = document.querySelectorAll('*');
                        for (const el of elements) {
                            const style = window.getComputedStyle(el);
                            const bg = style.backgroundImage;
                            if (bg && bg !== 'none' && bg.includes('url(')) {
                                // Extract URL from background-image
                                const match = bg.match(/url\\(["']?([^"')]+)["']?\\)/);
                                if (match) {
                                    // Get nearby text for matching
                                    const text = el.textContent || '';
                                    const parent = el.parentElement;
                                    const parentText = parent ? (parent.textContent || '') : '';
                                    results.push({
                                        url: match[1],
                                        text: text.substring(0, 200),
                                        parentText: parentText.substring(0, 500)
                                    });
                                }
                            }
                        }
                        return results;
                    }
                """)

                # Filter to only council photo URLs
                council_photos = [
                    bg for bg in bg_images
                    if "bus-directory" in bg.get("url", "").lower() and "council" in bg.get("url", "").lower()
                ]

                for bg in council_photos:
                    url = bg.get("url", "")
                    url_lower = self._normalize(url)
                    text = bg.get("text", "").lower()
                    parent_text = bg.get("parentText", "").lower()

                    for member in members_without_photos:
                        if member.get("photo_url"):
                            continue
                        last_name = self._normalize(member["name"].split()[-1])
                        first_name = self._normalize(member["name"].split()[0])

                        # Check URL, text, and parent text for name match
                        if (last_name in url_lower or first_name in url_lower or
                            last_name in text or last_name in parent_text or
                            first_name in text or first_name in parent_text):
                            if not url.startswith("http"):
                                url = urljoin(self.BASE_URL, url)
                            member["photo_url"] = url
                            print(f"      Photo: {member['name']}")
                            break

        except Exception as e:
            self.results["errors"].append(f"extract_photos: {str(e)}")

        return members

    async def scrape_city_info(self):
        return {
            "city_name": "Lake Forest",
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "1st and 3rd Tuesdays",
            "meeting_time": "6:30 PM",
            "meeting_location": {
                "name": "City Council Chambers",
                "address": "100 Civic Center Drive",
                "city_state_zip": "Lake Forest, CA 92630"
            },
            "zoom": {},
            "phone_numbers": [],
            "tv_channels": [],
            "live_stream": self.YOUTUBE_CHANNEL,
            "clerk": {
                "name": "Lisa Berglund",
                "title": "City Clerk",
                "phone": "(949) 461-3400",
                "email": "council@lakeforestca.gov"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,
                "ecomment": False,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "council@lakeforestca.gov",
                "deadline": "5:00 PM on meeting day",
            },
            "portals": {
                "agenda_center": self.AGENDAS_URL,
                "youtube": self.YOUTUBE_CHANNEL,
                "facebook": self.FACEBOOK_PAGE,
                "live_stream": self.YOUTUBE_CHANNEL,
            },
            "council": {
                "size": 5,
                "districts": 5,
                "at_large": 0,
                "mayor_elected": False,
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["District 2", "District 3", "District 4"],
                "term_length": 4,
                "election_system": "by-district"
            }
        }

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print("    Extracting photos...")
        members = await self.extract_photos(members)

        print(f"    Found {len(members)} members")

        for member in members:
            member_info = self.get_member_info(member["name"])
            district = member_info.get("district") if member_info else None
            term_start = member_info.get("term_start") if member_info else None
            term_end = member_info.get("term_end") if member_info else None

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                district=district,
                email=member.get("email"),
                phone=main_phones[0] if main_phones else None,
                profile_url=self.COUNCIL_URL,
                photo_url=member.get("photo_url"),
                term_start=term_start,
                term_end=term_end,
            )

        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        return self.get_results()
