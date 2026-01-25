"""
Scrape missing council member emails using Playwright
"""
import asyncio
import json
import re
from playwright.async_api import async_playwright

# Cities needing email data
CITIES_TO_SCRAPE = {
    "Aliso Viejo": {
        "base_url": "https://avcity.org",
        "council_url": "https://avcity.org/222/City-Council",
        "member_pages": [
            "https://avcity.org/223/Mayor-Max-Duncan",
            "https://avcity.org/224/Mayor-Pro-Tem-Mike-Munzing",
            "https://avcity.org/225/Councilmember-Tiffany-Ackley",
            "https://avcity.org/226/Councilmember-Garrett-Dwyer",
            "https://avcity.org/227/Councilmember-Tim-Zandbergen"
        ]
    },
    "Anaheim": {
        "base_url": "https://www.anaheim.net",
        "council_url": "https://www.anaheim.net/2527/Agendas",
        "member_pages": [
            "https://www.anaheim.net/5174/Anaheim-Mayor-Ashleigh-Aitken",
            "https://www.anaheim.net/2314/Mayor-Pro-Tem-Carlos-A-Leon",
            "https://www.anaheim.net/3522/Council-Member-Ryan-Balius",
            "https://www.anaheim.net/3523/Council-Member-Natalie-Rubalcava",
            "https://www.anaheim.net/3524/Council-Member-Norma-Campos-Kurtz",
            "https://www.anaheim.net/3521/Council-Member-Kristen-Maahs"
        ]
    },
    "La Habra": {
        "base_url": "https://www.lahabraca.gov",
        "council_url": "https://www.lahabraca.gov/153/City-Council"
    },
    "La Palma": {
        "base_url": "https://www.lapalmaca.gov",
        "council_url": "https://www.lapalmaca.gov/66/City-Council"
    },
    "Laguna Beach": {
        "base_url": "https://www.lagunabeachcity.net",
        "council_url": "https://www.lagunabeachcity.net/government/departments/city-council/contact-city-council"
    },
    "Orange": {
        "base_url": "https://www.cityoforange.org",
        "council_url": "https://www.cityoforange.org/our-city/local-government/city-council"
    }
}

def extract_emails(text):
    """Extract email addresses from text"""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    # Filter out common non-person emails
    filtered = [e for e in emails if not any(x in e.lower() for x in ['noreply', 'webmaster', 'info@', 'support'])]
    return filtered

async def scrape_city(page, city_name, city_info):
    """Scrape email addresses from a city's council pages"""
    results = {"city": city_name, "emails": [], "raw_text": ""}

    print(f"\n{'='*50}")
    print(f"Scraping: {city_name}")
    print(f"{'='*50}")

    try:
        # First try the main council page
        print(f"  Visiting: {city_info['council_url']}")
        await page.goto(city_info['council_url'], timeout=30000, wait_until='domcontentloaded')
        await asyncio.sleep(2)

        # Get all text content
        content = await page.content()
        text = await page.inner_text('body')

        # Extract emails
        emails = extract_emails(text)
        results["emails"].extend(emails)

        # Look for mailto links
        mailto_links = await page.query_selector_all('a[href^="mailto:"]')
        for link in mailto_links:
            href = await link.get_attribute('href')
            if href:
                email = href.replace('mailto:', '').split('?')[0]
                if email and email not in results["emails"]:
                    results["emails"].append(email)

        # If there are member pages, visit those too
        if 'member_pages' in city_info:
            for member_url in city_info['member_pages']:
                try:
                    print(f"  Visiting member page: {member_url}")
                    await page.goto(member_url, timeout=30000, wait_until='domcontentloaded')
                    await asyncio.sleep(1)

                    text = await page.inner_text('body')
                    member_emails = extract_emails(text)

                    mailto_links = await page.query_selector_all('a[href^="mailto:"]')
                    for link in mailto_links:
                        href = await link.get_attribute('href')
                        if href:
                            email = href.replace('mailto:', '').split('?')[0]
                            if email and email not in member_emails:
                                member_emails.append(email)

                    for email in member_emails:
                        if email not in results["emails"]:
                            results["emails"].append(email)

                except Exception as e:
                    print(f"    Error on member page: {e}")

        print(f"  Found emails: {results['emails']}")

    except Exception as e:
        print(f"  Error: {e}")
        results["error"] = str(e)

    return results

async def main():
    results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        for city_name, city_info in CITIES_TO_SCRAPE.items():
            result = await scrape_city(page, city_name, city_info)
            results[city_name] = result

        await browser.close()

    # Save results
    with open(r'C:\Users\Test\PROJECTS\Dashboards\oc-city-councils\scraped_emails.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    for city, data in results.items():
        print(f"{city}: {len(data.get('emails', []))} emails found")
        for email in data.get('emails', []):
            print(f"  - {email}")

if __name__ == "__main__":
    asyncio.run(main())
