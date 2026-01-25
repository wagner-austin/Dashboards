"""
Orange City Council Scraper
Dynamically discovers council members from website.
"""
import re
from urllib.parse import urljoin
from ..base import BaseScraper


class OrangeScraper(BaseScraper):
    """City of Orange - Granicus platform, members listed as text with mailto links."""

    CITY_NAME = "Orange"
    PLATFORM = "granicus"
    CITY_DOMAIN = "cityoforange.org"
    BASE_URL = "https://www.cityoforange.org"
    COUNCIL_URL = "https://www.cityoforange.org/our-city/local-government/city-council"

    def get_urls(self):
        return {"council": self.COUNCIL_URL}

    async def discover_members(self):
        """
        Discover council members from page text and mailto links.

        Orange lists members as text blocks:
        - "Mayor pro tem / Denis Bilodeau / Term: 2022-2026 / District 4"
        - "Councilmember / Arianna Barrios / Term: 2022-2026 / District 1"

        Emails are in mailto: links.
        """
        members = []
        seen_names = set()

        try:
            text = await self.get_page_text()

            # Get all mailto links for email matching
            mailto_links = await self.page.query_selector_all('a[href^="mailto:"]')
            emails = {}
            for link in mailto_links:
                href = await link.get_attribute("href") or ""
                email = href.replace("mailto:", "").split("?")[0].strip()
                if email and "@cityoforange.org" in email:
                    # Extract last name from email for matching
                    local = email.split("@")[0].lower()
                    emails[local] = email

            # Normalize whitespace
            text_normalized = re.sub(r'\s+', ' ', text)

            # Pattern for council members in text
            # Format: "Position Name Term: YYYY-YYYY District X"
            # Example: "Mayor pro tem Denis Bilodeau Term: 2022-2026 District 4"
            patterns = [
                # Mayor Pro Tem pattern
                (r'Mayor\s+pro\s+tem\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+Term:\s*(\d{4})-(\d{4})\s+District\s+(\d+)', "Mayor Pro Tem"),
                # Councilmember pattern
                (r'Councilmember\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+Term:\s*(\d{4})-(\d{4})\s+District\s+(\d+)', "Councilmember"),
            ]

            for pattern, position in patterns:
                for match in re.finditer(pattern, text_normalized):
                    name = match.group(1).strip()
                    term_start = int(match.group(2))
                    term_end = int(match.group(3))
                    district = f"District {match.group(4)}"

                    if name.lower() in seen_names:
                        continue
                    seen_names.add(name.lower())

                    # Match email by last name
                    name_parts = name.lower().split()
                    last_name = name_parts[-1]
                    first_initial = name_parts[0][0]

                    email = None
                    # Try various email patterns
                    for local, full_email in emails.items():
                        if last_name in local:
                            email = full_email
                            break
                        if f"{first_initial}{last_name}" == local:
                            email = full_email
                            break

                    members.append({
                        "name": name,
                        "position": position,
                        "district": district,
                        "email": email,
                        "term_start": term_start,
                        "term_end": term_end,
                    })
                    print(f"      Found: {name} ({position}, {district})")

            # Also find Mayor from separate pattern
            mayor_match = re.search(r'Meet Mayor\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text_normalized)
            if mayor_match:
                name = mayor_match.group(1).strip()
                if name.lower() not in seen_names:
                    seen_names.add(name.lower())

                    # Try to get term from "2024-2026 term" text
                    term_match = re.search(r'(\d{4})-(\d{4})\s+term', text_normalized)
                    term_start = int(term_match.group(1)) if term_match else None
                    term_end = int(term_match.group(2)) if term_match else None

                    # Find Mayor's profile link to get email
                    mayor_url = None
                    profile_links = await self.page.query_selector_all('a')
                    for link in profile_links:
                        href = await link.get_attribute("href") or ""
                        if "mayor-" in href.lower() and name.split()[-1].lower() in href.lower():
                            mayor_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                            break

                    members.insert(0, {  # Mayor first
                        "name": name,
                        "position": "Mayor",
                        "district": "At-Large",
                        "email": None,  # Will get from profile page
                        "term_start": term_start,
                        "term_end": term_end,
                        "profile_url": mayor_url,
                    })
                    print(f"      Found: {name} (Mayor)")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} members")

        for member in members:
            email = member.get("email")
            profile_url = member.get("profile_url") or self.COUNCIL_URL

            # If Mayor has profile page, visit it to get email
            if member["position"] == "Mayor" and member.get("profile_url"):
                print(f"    Visiting Mayor's profile for email...")
                result = await self.visit_page(member["profile_url"], "mayor_profile")
                if result.get("emails"):
                    # Take any email found (Mayor uses personal domain)
                    email = result["emails"][0]

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                district=member.get("district"),
                email=email,
                phone=main_phones[0] if main_phones else None,
                profile_url=profile_url,
                term_start=member.get("term_start"),
                term_end=member.get("term_end"),
            )

        return self.get_results()
