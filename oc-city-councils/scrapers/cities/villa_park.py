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

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

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

            self.add_council_member(**data)

        # Final pass to match any remaining emails
        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)
        return self.get_results()
