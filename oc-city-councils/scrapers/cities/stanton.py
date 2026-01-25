"""
Stanton City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class StantonScraper(BaseScraper):
    """Stanton - PHP website with individual bio pages."""

    CITY_NAME = "Stanton"
    PLATFORM = "custom"
    CITY_DOMAIN = "stantonca.gov"
    BASE_URL = "https://www.stantonca.gov"
    COUNCIL_URL = "https://www.stantonca.gov/government/city_council.php"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """
        Discover council members from the main page.
        Stanton has position labels followed by names in the text.
        """
        members = []
        seen_names = set()

        try:
            # Get the full page text
            text = await self.get_page_text()

            # Find council members using pattern matching on position labels
            # Pattern: "Mayor: Name", "Mayor Pro Tem: Name", "Council Member: Name"
            patterns = [
                (r'Mayor:\s*([A-Z][a-zA-Z\.\s]+?)(?:\s+At-Large|\s+District|\n)', "Mayor"),
                (r'Mayor Pro Tem:\s*([A-Z][a-zA-Z\.\s]+?)(?:\s+District|\n)', "Mayor Pro Tem"),
                (r'Council Member:\s*([A-Z][a-zA-Z\.\s]+?)(?:\s+District|\n)', "Councilmember"),
            ]

            for pattern, position in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    name = match.group(1).strip()
                    # Clean up name
                    name = re.sub(r'\s+', ' ', name).strip()

                    if len(name) < 3 or name in seen_names:
                        continue

                    seen_names.add(name)
                    members.append({"name": name, "position": position, "url": None})
                    print(f"      Found: {name} ({position})")

            # Now find bio links and match them to members
            links = await self.page.query_selector_all("a[href*='bio']")
            for link in links:
                href = await link.get_attribute("href") or ""
                if "bio" not in href.lower():
                    continue

                url = urljoin(self.BASE_URL, href)

                # Try to match bio URL to a member by name in URL
                href_lower = href.lower()
                for member in members:
                    if member["url"]:
                        continue  # Already matched

                    # Check if last name is in URL
                    name_parts = member["name"].lower().split()
                    last_name = name_parts[-1] if name_parts else ""

                    if last_name and last_name in href_lower:
                        member["url"] = url
                        print(f"        Bio URL for {member['name']}: {url}")
                        break

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

        print(f"    Found {len(members)} members")

        for member in members:
            if member.get("url"):
                data = await self.scrape_member_page(
                    member, self.BASE_URL, self.CITY_DOMAIN, main_phones
                )
            else:
                # No bio page yet, just use main page data
                data = {
                    "name": member["name"],
                    "position": member["position"],
                    "district": member.get("district"),
                    "email": self.match_email_to_name(
                        member["name"], main_emails, self.CITY_DOMAIN
                    ),
                    "phone": main_phones[0] if main_phones else None,
                    "profile_url": None,
                    "photo_url": None,
                    "bio": None,
                    "term_start": None,
                    "term_end": None,
                }
                print(f"    Member {member['name']} has no bio page")

            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()
