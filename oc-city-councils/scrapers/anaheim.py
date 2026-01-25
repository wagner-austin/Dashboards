"""
Anaheim-specific scraper.
Anaheim's site has a broken main council page but individual member pages work.
"""
from .base import BaseScraper


class AnaheimScraper(BaseScraper):
    """
    Anaheim scraper - special case.

    Main council page is broken, but individual member pages have contact info.
    Each member page has their email in a mailto: link.
    """

    CITY_NAME = "Anaheim"
    PLATFORM = "civicplus_custom"

    MEMBERS = [
        {
            "name": "Ashleigh Aitken",
            "position": "Mayor",
            "district": "At-Large",
            "url": "https://www.anaheim.net/5174/Anaheim-Mayor-Ashleigh-Aitken"
        },
        {
            "name": "Carlos A. Leon",
            "position": "Mayor Pro Tem",
            "district": "District 3",
            "url": "https://www.anaheim.net/2314/Mayor-Pro-Tem-Carlos-A-Leon"
        },
        {
            "name": "Ryan Balius",
            "position": "Councilmember",
            "district": "District 1",
            "url": "https://www.anaheim.net/3522/Council-Member-Ryan-Balius"
        },
        {
            "name": "Natalie Rubalcava",
            "position": "Councilmember",
            "district": "District 4",
            "url": "https://www.anaheim.net/3523/Council-Member-Natalie-Rubalcava"
        },
        {
            "name": "Norma Campos Kurtz",
            "position": "Councilmember",
            "district": "District 5",
            "url": "https://www.anaheim.net/3524/Council-Member-Norma-Campos-Kurtz"
        },
        {
            "name": "Kristen Maahs",
            "position": "Councilmember",
            "district": "District 6",
            "url": "https://www.anaheim.net/3521/Council-Member-Kristen-Maahs"
        }
    ]

    def get_urls(self):
        return {m["name"]: m["url"] for m in self.MEMBERS}

    async def scrape(self):
        print(f"\n  [{self.PLATFORM}] Scraping {self.CITY_NAME}")

        for member in self.MEMBERS:
            result = await self.visit_page(member["url"], f"member_{member['name']}")

            # Find this member's email from the scraped page
            member_email = None
            member_phone = None

            # Look for email matching pattern (first initial + lastname)
            name_parts = member["name"].lower().split()
            if len(name_parts) >= 2:
                # Try patterns like aaitken, cleon, etc.
                first_initial = name_parts[0][0]
                last_name = name_parts[-1]

                for email in result.get("emails", []):
                    email_lower = email.lower()
                    if f"{first_initial}{last_name}" in email_lower or last_name in email_lower:
                        if "@anaheim.net" in email_lower:
                            member_email = email.strip()
                            break

            # Get first phone if available
            if result.get("phones"):
                member_phone = result["phones"][0]

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                email=member_email,
                phone=member_phone,
                district=member["district"],
                profile_url=member["url"]
            )

        # Fallback: match any remaining members from all collected emails
        self.match_emails_to_members(city_domain="anaheim.net")

        return self.get_results()
