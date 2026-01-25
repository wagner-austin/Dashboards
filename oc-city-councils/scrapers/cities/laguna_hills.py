"""
Laguna Hills City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class LagunaHillsScraper(BaseScraper):
    """Laguna Hills - CivicPlus platform with URL-based member discovery."""

    CITY_NAME = "Laguna Hills"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "lagunahillsca.gov"
    BASE_URL = "https://www.lagunahillsca.gov"
    COUNCIL_URL = "https://www.lagunahillsca.gov/129/City-Council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """
        Discover council members from the main council page.
        Laguna Hills uses URLs like /527/Don-Caskey-Mayor or /475/Erica-Pezold
        """
        members = []
        seen_urls = set()

        try:
            # Find all links on the page
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href:
                    continue

                # Skip mailto, javascript, etc.
                if href.startswith(("mailto:", "javascript:", "#", "tel:")):
                    continue

                # Look for CivicPlus profile URLs: /number/Name-Pattern
                # e.g., /527/Don-Caskey-Mayor, /475/Erica-Pezold
                match = re.search(r'/(\d+)/([A-Z][a-z]+-[A-Z][a-z]+(?:-[A-Za-z-]+)?)', href)
                if not match:
                    continue

                # Extract name from URL path
                url_name_part = match.group(2)

                # Skip if it's not a person page (navigation, departments, etc.)
                skip_patterns = [
                    "city-council", "meeting", "agenda", "minutes", "contact",
                    "explore", "doing-business", "how-do-i", "community-services",
                    "public-safety", "planning", "division", "services", "department",
                    "calendar", "news", "events", "permits", "forms", "faq"
                ]
                if any(skip in url_name_part.lower() for skip in skip_patterns):
                    continue

                # Normalize URL
                full_url = urljoin(self.BASE_URL, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Extract name from URL (convert hyphens to spaces)
                # e.g., "Don-Caskey-Mayor" -> "Don Caskey Mayor"
                name_parts = url_name_part.replace("-", " ").split()

                # Determine position from URL
                position = "Councilmember"
                if "mayor-pro" in url_name_part.lower() or "pro-tempore" in url_name_part.lower():
                    position = "Mayor Pro Tem"
                    # Remove position words from name
                    name_parts = [p for p in name_parts if p.lower() not in ["mayor", "pro", "tempore", "tem"]]
                elif "mayor" in url_name_part.lower():
                    position = "Mayor"
                    name_parts = [p for p in name_parts if p.lower() != "mayor"]

                # Build name from remaining parts
                name = " ".join(name_parts)

                if len(name) < 3:
                    continue

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

                result_phones = result.get("phones", [])
                member_phone = result_phones[0] if result_phones else (main_phones[0] if main_phones else None)

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
