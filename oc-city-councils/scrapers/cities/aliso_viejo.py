"""
Aliso Viejo City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class AlisoViejoScraper(BaseScraper):
    """Aliso Viejo - CivicPlus platform with dynamic member discovery."""

    CITY_NAME = "Aliso Viejo"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "avcity.org"
    BASE_URL = "https://avcity.org"
    COUNCIL_URL = "https://avcity.org/222/City-Council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """Discover council members from profile links on main page."""
        members = []
        seen_urls = set()

        try:
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or not text or len(text) < 3:
                    continue

                text_lower = text.lower()

                # Look for position keywords in link text
                position = None
                if "mayor pro tem" in text_lower:
                    position = "Mayor Pro Tem"
                elif "mayor" in text_lower and "pro tem" not in text_lower:
                    position = "Mayor"
                elif "councilmember" in text_lower or "council member" in text_lower:
                    position = "Councilmember"

                if not position:
                    continue

                # Extract name (remove position prefix)
                name = text
                for prefix in ["Mayor Pro Tem", "Mayor", "Councilmember", "Council Member"]:
                    name = re.sub(rf"^{prefix}\s*", "", name, flags=re.IGNORECASE).strip()

                # Skip bad parses
                if len(name) < 3 or any(kw in name.lower() for kw in ["mayor", "council", "contact"]):
                    continue

                url = urljoin(self.BASE_URL, href)
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                members.append({"name": name, "position": position, "url": url})
                print(f"      Found: {position} {name}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} council members")

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

                member_phone = result.get("phones", [None])[0] or (main_phones[0] if main_phones else None)

                print(f"      Photo: {'Found' if photo_url else 'Not found'}")
                print(f"      Bio: {len(bio) if bio else 0} chars")
                print(f"      Term: {term_start}-{term_end}")
                print(f"      Email: {member_email or 'Not found'}")

                self.add_council_member(
                    name=member["name"],
                    position=member["position"],
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
