"""
Placentia City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class PlacentiaScraper(BaseScraper):
    """Placentia - CivicPlus with /ID/Position-Name-District-X URLs."""

    CITY_NAME = "Placentia"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "placentia.org"
    BASE_URL = "https://www.placentia.org"
    COUNCIL_URL = "https://www.placentia.org/268/Mayor-City-Council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """
        Discover council members from the main council page.
        Placentia URLs: /721/Councilmember-Thomas-Hummer-District-1
        """
        members = []
        seen_urls = set()
        seen_ids = set()

        try:
            links = await self.page.query_selector_all("a")

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()

                if not href or len(text) < 3:
                    continue

                if href.startswith(("mailto:", "javascript:", "#", "tel:")):
                    continue

                # Match URLs with council member patterns
                # /ID/Mayor-Name-District-X or /ID/Councilmember-Name-District-X
                href_lower = href.lower()
                if not re.search(r'/\d+/(mayor|councilmember)', href_lower):
                    continue

                # Skip meeting/archive pages
                if any(skip in href_lower for skip in ["archive", "meeting", "agenda"]):
                    continue

                full_url = urljoin(self.BASE_URL, href)
                # Normalize URL (ensure www. prefix)
                full_url = full_url.replace("://placentia.org", "://www.placentia.org")
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Skip main council page
                if "/268/" in full_url:
                    continue

                # Extract page ID and skip duplicates by ID
                id_match = re.search(r'/(\d+)/', full_url)
                if id_match:
                    page_id = id_match.group(1)
                    if page_id in seen_ids:
                        continue
                    seen_ids.add(page_id)

                # Extract position and name from URL
                # Pattern: /ID/Position-FirstName-MiddleInit-LastName-District-X
                match = re.search(r'/\d+/(Mayor(?:-Pro-Tem)?|Councilmember)-(.+?)(?:-District|$)', href, re.IGNORECASE)
                if not match:
                    continue

                position_raw = match.group(1).replace("-", " ").title()
                name_part = match.group(2).replace("-", " ").strip()

                # Clean up position
                if "pro tem" in position_raw.lower():
                    position = "Mayor Pro Tem"
                elif "mayor" in position_raw.lower():
                    position = "Mayor"
                else:
                    position = "Councilmember"

                # Clean name - remove trailing district info and truncated words
                name = re.sub(r'\s+distric.*$', '', name_part, flags=re.IGNORECASE).strip()
                name = re.sub(r'\s+district.*$', '', name, flags=re.IGNORECASE).strip()

                if len(name) < 3:
                    continue

                # Skip if name looks like a page title
                if name.lower() in ["city council", "mayor city council"]:
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
                    # First try city domain email
                    member_email = self.match_email_to_name(
                        member["name"], result["emails"], self.CITY_DOMAIN
                    )
                    # Fall back to any email on member's page (some use personal domains)
                    if not member_email and len(result["emails"]) == 1:
                        member_email = result["emails"][0]

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
