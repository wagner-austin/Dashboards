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

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

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

                result_phones = result.get("phones", [])
                member_phone = result_phones[0] if result_phones else (main_phones[0] if main_phones else None)

                self.add_council_member(
                    name=member["name"],
                    position=position,
                    email=member_email,
                    phone=member_phone,
                    profile_url=member["url"],
                    photo_url=photo_url,
                    bio=bio,
                    term_start=term_start,
                    term_end=term_end,
                )
            else:
                self.add_council_member(
                    name=member["name"],
                    position=member["position"],
                    profile_url=member["url"],
                )

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()
