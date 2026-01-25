"""
Stealth scraper for websites with bot detection.
Uses anti-detection techniques to bypass 403 blocks.
"""
import asyncio
import random
import re
from playwright.async_api import async_playwright


class StealthScraper:
    """Stealth scraper using anti-detection techniques"""

    def __init__(self):
        self.results = {}

    async def scrape_page(self, url, page_name="page"):
        """Scrape a page using stealth techniques"""
        async with async_playwright() as p:
            # Use Firefox - much better at bypassing bot detection
            browser = await p.firefox.launch(headless=True)

            # Create context with realistic settings
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/Los_Angeles',
            )

            # Disable webdriver detection
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            page = await context.new_page()

            # Set extra headers
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            })

            try:
                # Random delay to seem more human
                await asyncio.sleep(random.uniform(1, 3))

                # Navigate to page
                response = await page.goto(url, wait_until='networkidle', timeout=30000)

                if response.status == 403:
                    print(f"  [BLOCKED] {page_name}: Still getting 403")
                    return {"status": "blocked", "url": url}

                # Wait a bit for dynamic content
                await asyncio.sleep(random.uniform(1, 2))

                # Get page content
                content = await page.content()

                # Extract emails
                emails = self._extract_emails(content)

                # Try to get mailto links
                mailto_links = await page.eval_on_selector_all(
                    'a[href^="mailto:"]',
                    'elements => elements.map(e => e.href.replace("mailto:", "").split("?")[0])'
                )

                all_emails = list(set(emails + mailto_links))

                # Extract phone numbers
                phones = self._extract_phones(content)

                print(f"  [OK] {page_name}: {len(all_emails)} emails, {len(phones)} phones")

                return {
                    "status": "success",
                    "url": url,
                    "emails": all_emails,
                    "phones": phones,
                    "http_code": response.status
                }

            except Exception as e:
                print(f"  [ERROR] {page_name}: {str(e)}")
                return {"status": "error", "url": url, "error": str(e)}

            finally:
                await browser.close()

    def _extract_emails(self, text):
        """Extract email addresses from text"""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(pattern, text)
        # Filter out common junk
        junk = ['example.com', 'domain.com', 'email.com', 'test.com', '.png', '.jpg', '.gif']
        return [e for e in emails if not any(j in e.lower() for j in junk)]

    def _extract_phones(self, text):
        """Extract phone numbers from text"""
        patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\d{3}[-.\s]\d{3}[-.\s]\d{4}'
        ]
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))


async def scrape_laguna_beach():
    """Scrape Laguna Beach city council"""
    print("\n" + "="*60)
    print("STEALTH SCRAPING: Laguna Beach")
    print("="*60)

    scraper = StealthScraper()

    urls = [
        ("https://www.lagunabeachcity.net/government/departments/city-council", "council_main"),
        ("https://www.lagunabeachcity.net/government/departments/city-council/contact-city-council", "contact"),
    ]

    all_emails = []
    all_phones = []

    for url, page_name in urls:
        result = await scraper.scrape_page(url, page_name)
        if result.get("status") == "success":
            all_emails.extend(result.get("emails", []))
            all_phones.extend(result.get("phones", []))

    print(f"\nTotal emails found: {list(set(all_emails))}")
    print(f"Total phones found: {list(set(all_phones))}")

    return {
        "city": "Laguna Beach",
        "emails": list(set(all_emails)),
        "phones": list(set(all_phones))
    }


async def scrape_orange():
    """Scrape City of Orange city council"""
    print("\n" + "="*60)
    print("STEALTH SCRAPING: City of Orange")
    print("="*60)

    scraper = StealthScraper()

    # Main council page and individual member pages
    urls = [
        ("https://www.cityoforange.org/our-city/local-government/city-council", "council_main"),
        ("https://www.cityoforange.org/our-city/local-government/city-council/mayor-dan-slater", "mayor"),
        ("https://www.cityoforange.org/our-city/local-government/city-council/mayor-pro-tem-denis-bilodeau", "mayor_pro_tem"),
        ("https://www.cityoforange.org/our-city/local-government/city-council/council-member-arianna-barrios", "district_1"),
        ("https://www.cityoforange.org/our-city/local-government/city-council/council-member-jon-dumitru", "district_2"),
        ("https://www.cityoforange.org/our-city/local-government/city-council/council-member-kathy-tavoularis", "district_3"),
        ("https://www.cityoforange.org/our-city/local-government/city-council/council-member-ana-gutierrez", "district_5"),
        ("https://www.cityoforange.org/our-city/local-government/city-council/council-member-john-gyllenhammer", "district_6"),
    ]

    members = {}
    all_emails = []

    for url, page_name in urls:
        result = await scraper.scrape_page(url, page_name)
        if result.get("status") == "success":
            all_emails.extend(result.get("emails", []))
            if page_name != "council_main":
                members[page_name] = {
                    "url": url,
                    "emails": result.get("emails", []),
                    "phones": result.get("phones", [])
                }

    print(f"\nAll emails found: {list(set(all_emails))}")
    print(f"\nBy member: {members}")

    return {
        "city": "Orange",
        "emails": list(set(all_emails)),
        "members": members
    }


async def main():
    """Run stealth scrapers"""
    results = {}

    results["Laguna Beach"] = await scrape_laguna_beach()
    results["Orange"] = await scrape_orange()

    return results


if __name__ == "__main__":
    asyncio.run(main())
