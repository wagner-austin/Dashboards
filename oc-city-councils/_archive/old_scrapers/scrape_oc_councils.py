"""
Orange County City Council Data Scraper

Collects verified contact information for all 34 OC city council members:
- Email
- Phone number
- Personal website
- City profile page
- Instagram
- Public comment submission method

Usage:
    python scrape_oc_councils.py              # Scrape all cities
    python scrape_oc_councils.py --city Irvine  # Scrape single city
    python scrape_oc_councils.py --verify     # Verify existing data
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# All 34 incorporated cities in Orange County with their official websites
# Verified January 2025
OC_CITIES = {
    "Aliso Viejo": {
        "website": "https://www.cityofalisoviejo.com",
        "council_url": "https://www.cityofalisoviejo.com/government/city-council",
        "state": "needs_scrape"
    },
    "Anaheim": {
        "website": "https://www.anaheim.net",
        "council_url": "https://www.anaheim.net/158/City-Council",
        "state": "needs_scrape"
    },
    "Brea": {
        "website": "https://www.ci.brea.ca.us",
        "council_url": "https://www.ci.brea.ca.us/105/City-Council",
        "state": "needs_scrape"
    },
    "Buena Park": {
        "website": "https://www.buenapark.com",
        "council_url": "https://www.buenapark.com/city-hall/city-council",
        "state": "needs_scrape"
    },
    "Costa Mesa": {
        "website": "https://www.costamesaca.gov",
        "council_url": "https://www.costamesaca.gov/city-hall/city-council",
        "state": "needs_scrape"
    },
    "Cypress": {
        "website": "https://www.cypressca.org",
        "council_url": "https://www.cypressca.org/government/city-council",
        "state": "needs_scrape"
    },
    "Dana Point": {
        "website": "https://www.danapoint.org",
        "council_url": "https://www.danapoint.org/government/city-council",
        "state": "needs_scrape"
    },
    "Fountain Valley": {
        "website": "https://www.fountainvalley.org",
        "council_url": "https://www.fountainvalley.org/148/City-Council",
        "state": "needs_scrape"
    },
    "Fullerton": {
        "website": "https://www.cityoffullerton.com",
        "council_url": "https://www.cityoffullerton.com/government/city-council",
        "state": "needs_scrape"
    },
    "Garden Grove": {
        "website": "https://ggcity.org",
        "council_url": "https://ggcity.org/city-council",
        "state": "needs_scrape"
    },
    "Huntington Beach": {
        "website": "https://www.huntingtonbeachca.gov",
        "council_url": "https://www.huntingtonbeachca.gov/government/elected_officials/city_council/",
        "state": "needs_scrape"
    },
    "Irvine": {
        "website": "https://www.cityofirvine.org",
        "council_url": "https://www.cityofirvine.org/city-council",
        "state": "done",  # Already have this data
        "notes": "Data already collected in irvine-city-council/generate.py"
    },
    "La Habra": {
        "website": "https://www.lahabracity.com",
        "council_url": "https://www.lahabracity.com/178/City-Council",
        "state": "needs_scrape"
    },
    "La Palma": {
        "website": "https://www.cityoflapalma.org",
        "council_url": "https://www.cityoflapalma.org/156/City-Council",
        "state": "needs_scrape"
    },
    "Laguna Beach": {
        "website": "https://www.lagunabeachcity.net",
        "council_url": "https://www.lagunabeachcity.net/government/city-council",
        "state": "needs_scrape"
    },
    "Laguna Hills": {
        "website": "https://www.lagunahillsca.gov",
        "council_url": "https://www.lagunahillsca.gov/city-government/city-council",
        "state": "needs_scrape"
    },
    "Laguna Niguel": {
        "website": "https://www.cityoflagunaniguel.org",
        "council_url": "https://www.cityoflagunaniguel.org/106/City-Council",
        "state": "needs_scrape"
    },
    "Laguna Woods": {
        "website": "https://www.cityoflagunawoods.org",
        "council_url": "https://www.cityoflagunawoods.org/government/city-council",
        "state": "needs_scrape"
    },
    "Lake Forest": {
        "website": "https://www.lakeforestca.gov",
        "council_url": "https://www.lakeforestca.gov/government/city-council",
        "state": "needs_scrape"
    },
    "Los Alamitos": {
        "website": "https://www.cityoflosalamitos.org",
        "council_url": "https://www.cityoflosalamitos.org/government/city-council",
        "state": "needs_scrape"
    },
    "Mission Viejo": {
        "website": "https://cityofmissionviejo.org",
        "council_url": "https://cityofmissionviejo.org/government/city-council",
        "state": "needs_scrape"
    },
    "Newport Beach": {
        "website": "https://www.newportbeachca.gov",
        "council_url": "https://www.newportbeachca.gov/government/city-council",
        "state": "needs_scrape"
    },
    "Orange": {
        "website": "https://www.cityoforange.org",
        "council_url": "https://www.cityoforange.org/120/City-Council",
        "state": "needs_scrape"
    },
    "Placentia": {
        "website": "https://www.placentia.org",
        "council_url": "https://www.placentia.org/204/City-Council",
        "state": "needs_scrape"
    },
    "Rancho Santa Margarita": {
        "website": "https://www.cityofrsm.org",
        "council_url": "https://www.cityofrsm.org/government/city-council",
        "state": "needs_scrape"
    },
    "San Clemente": {
        "website": "https://www.san-clemente.org",
        "council_url": "https://www.san-clemente.org/government/city-council",
        "state": "needs_scrape"
    },
    "San Juan Capistrano": {
        "website": "https://sanjuancapistrano.org",
        "council_url": "https://sanjuancapistrano.org/Departments/City-Manager/City-Council",
        "state": "needs_scrape"
    },
    "Santa Ana": {
        "website": "https://www.santa-ana.org",
        "council_url": "https://www.santa-ana.org/city-council/",
        "state": "needs_scrape"
    },
    "Seal Beach": {
        "website": "https://www.sealbeachca.gov",
        "council_url": "https://www.sealbeachca.gov/Government/City-Council",
        "state": "needs_scrape"
    },
    "Stanton": {
        "website": "https://www.ci.stanton.ca.us",
        "council_url": "https://www.ci.stanton.ca.us/182/City-Council",
        "state": "needs_scrape"
    },
    "Tustin": {
        "website": "https://www.tustinca.org",
        "council_url": "https://www.tustinca.org/168/City-Council",
        "state": "needs_scrape"
    },
    "Villa Park": {
        "website": "https://www.villapark.org",
        "council_url": "https://www.villapark.org/city-council",
        "state": "needs_scrape"
    },
    "Westminster": {
        "website": "https://www.westminster-ca.gov",
        "council_url": "https://www.westminster-ca.gov/government/city-council",
        "state": "needs_scrape"
    },
    "Yorba Linda": {
        "website": "https://www.yorbalindaca.gov",
        "council_url": "https://www.yorbalindaca.gov/149/City-Council",
        "state": "needs_scrape"
    },
}


def extract_emails(text):
    """Extract email addresses from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, text)))


def extract_phones(text):
    """Extract phone numbers from text."""
    # Match various phone formats
    pattern = r'(?:\+1[-.\s]?)?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})'
    matches = re.findall(pattern, text)
    return [f"({m[0]}) {m[1]}-{m[2]}" for m in matches]


def extract_instagram(page, base_url):
    """Find Instagram links on the page."""
    links = page.query_selector_all('a[href*="instagram.com"]')
    instagrams = []
    for link in links:
        href = link.get_attribute("href")
        if href and "instagram.com" in href:
            instagrams.append(href)
    return list(set(instagrams))


def scrape_city_council(city_name, city_info, browser):
    """Scrape council member data for a single city."""
    print(f"\n{'='*60}")
    print(f"Scraping: {city_name}")
    print(f"{'='*60}")

    result = {
        "city": city_name,
        "website": city_info["website"],
        "council_url": city_info["council_url"],
        "scraped_at": datetime.now().isoformat(),
        "council_members": [],
        "public_comment": None,
        "general_contact": {},
        "notes": [],
        "errors": []
    }

    page = browser.new_page()
    page.set_default_timeout(30000)

    try:
        # First, verify the council URL works
        print(f"  Loading: {city_info['council_url']}")
        response = page.goto(city_info["council_url"], wait_until="networkidle")

        if not response or response.status >= 400:
            result["errors"].append(f"Council URL returned status {response.status if response else 'None'}")
            result["notes"].append("Need to find correct council page URL")
            return result

        result["notes"].append(f"Council page loaded successfully (status {response.status})")

        # Wait for content to load
        page.wait_for_timeout(2000)

        # Get all text content for email/phone extraction
        body = page.query_selector("body")
        page_text = body.inner_text() if body else ""
        page_html = page.content()

        # Extract general contact info
        emails = extract_emails(page_text)
        phones = extract_phones(page_text)
        instagrams = extract_instagram(page, city_info["website"])

        result["general_contact"] = {
            "emails_found": emails[:5],  # Limit to first 5
            "phones_found": phones[:5],
            "instagrams_found": instagrams
        }

        # Look for links to individual council member pages
        # Common patterns: links containing "council", "mayor", "member"
        member_links = []
        all_links = page.query_selector_all("a")

        for link in all_links:
            href = link.get_attribute("href") or ""
            text = link.inner_text().strip()

            # Skip empty or navigation links
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue
            if len(text) < 3 or len(text) > 100:
                continue

            # Look for council member profile links
            href_lower = href.lower()
            text_lower = text.lower()

            # Expanded patterns for member links
            url_patterns = ["mayor", "council-member", "councilmember", "councilwoman",
                          "councilman", "district", "elected", "official", "member"]
            name_patterns = ["mayor", "council", "district"]

            is_member_link = (
                any(x in href_lower for x in url_patterns) or
                (any(x in text_lower for x in name_patterns) and len(text.split()) <= 5)
            )

            if is_member_link:
                full_url = urljoin(city_info["council_url"], href)
                if full_url not in [m["url"] for m in member_links]:
                    member_links.append({"text": text, "url": full_url})

        # Also look for links with profile images nearby (common pattern)
        img_links = page.query_selector_all("a:has(img)")
        for link in img_links:
            href = link.get_attribute("href") or ""
            if not href or href.startswith("#"):
                continue
            # Get parent container text to find name
            parent = link.evaluate_handle("el => el.parentElement")
            if parent:
                parent_el = parent.as_element()
                if parent_el:
                    parent_text = parent_el.inner_text().strip()
                    # Check if this looks like a council member (has a name-like text)
                    if parent_text and len(parent_text) < 100:
                        words = parent_text.split()
                        if 2 <= len(words) <= 6:  # Likely a name
                            full_url = urljoin(city_info["council_url"], href)
                            if full_url not in [m["url"] for m in member_links]:
                                member_links.append({"text": parent_text.split('\n')[0], "url": full_url})

        print(f"  Found {len(member_links)} potential council member links")

        # Try to extract council member info from the main page first
        # Look for cards, list items, or sections with member info

        # Common patterns for member containers
        member_selectors = [
            ".council-member", ".councilmember", ".member-card",
            '[class*="council"]', '[class*="member"]',
            ".staff-member", ".elected-official",
            "article", ".card"
        ]

        for selector in member_selectors:
            try:
                containers = page.query_selector_all(selector)
                if containers and len(containers) >= 3:  # At least 3 members
                    print(f"  Found {len(containers)} containers with selector: {selector}")
                    result["notes"].append(f"Member containers found with: {selector}")
                    break
            except:
                continue

        # Now visit each member link to get detailed info
        for i, member_link in enumerate(member_links[:10]):  # Limit to 10 to avoid too many requests
            print(f"  Visiting member page: {member_link['text'][:40]}...")

            member_data = {
                "name": member_link["text"],
                "city_profile": member_link["url"],
                "position": None,
                "district": None,
                "email": None,
                "phone": None,
                "website": None,
                "instagram": None,
                "photo": None
            }

            try:
                page.goto(member_link["url"], wait_until="networkidle")
                page.wait_for_timeout(1500)

                member_body = page.query_selector("body")
                member_text = member_body.inner_text() if member_body else ""

                # Extract emails specific to this member
                member_emails = extract_emails(member_text)
                if member_emails:
                    # Try to find the most relevant email (matching name or city domain)
                    for email in member_emails:
                        if any(x in email.lower() for x in member_link["text"].lower().split()):
                            member_data["email"] = email
                            break
                    if not member_data["email"]:
                        member_data["email"] = member_emails[0]

                # Extract phones
                member_phones = extract_phones(member_text)
                if member_phones:
                    member_data["phone"] = member_phones[0]

                # Extract Instagram
                member_instas = extract_instagram(page, city_info["website"])
                if member_instas:
                    member_data["instagram"] = member_instas[0]

                # Try to find photo
                images = page.query_selector_all("img")
                for img in images:
                    src = img.get_attribute("src") or ""
                    alt = (img.get_attribute("alt") or "").lower()
                    # Look for images that might be the member's photo
                    if any(x in alt or x in src.lower() for x in member_link["text"].lower().split() if len(x) > 3):
                        member_data["photo"] = urljoin(member_link["url"], src)
                        break

                # Determine position (Mayor, Vice Mayor, Councilmember)
                text_lower = member_text.lower()
                if "mayor" in member_link["text"].lower() or "mayor" in text_lower[:500]:
                    if "vice" in member_link["text"].lower() or "vice mayor" in text_lower[:500]:
                        member_data["position"] = "Vice Mayor"
                    else:
                        member_data["position"] = "Mayor"
                else:
                    member_data["position"] = "Councilmember"

                # Try to find district
                district_match = re.search(r"district\s*(\d+)", text_lower)
                if district_match:
                    member_data["district"] = f"District {district_match.group(1)}"

                result["council_members"].append(member_data)
                print(f"    Email: {member_data['email']}")
                print(f"    Phone: {member_data['phone']}")

            except Exception as e:
                result["errors"].append(f"Error scraping {member_link['text']}: {str(e)}")
                result["council_members"].append(member_data)

        # Look for public comment info
        print("  Looking for public comment submission info...")

        # Go back to main council page
        page.goto(city_info["council_url"], wait_until="networkidle")
        page.wait_for_timeout(1500)

        # Search for public comment links
        comment_keywords = ["public comment", "ecomment", "speaker", "public input",
                          "comment card", "participate", "public hearing", "agenda"]

        all_links = page.query_selector_all("a")
        for link in all_links:
            href = link.get_attribute("href") or ""
            text = (link.inner_text() or "").lower()

            if any(kw in text for kw in comment_keywords):
                full_url = urljoin(city_info["council_url"], href)
                if result["public_comment"] is None:
                    result["public_comment"] = {
                        "url": full_url,
                        "description": link.inner_text().strip()
                    }
                    print(f"    Found: {result['public_comment']['description'][:50]}")
                    break

        # Also check for Granicus (common platform)
        if "granicus" in page_html.lower():
            result["notes"].append("City uses Granicus for meetings/agendas")
            granicus_match = re.search(r'href="([^"]*granicus[^"]*)"', page_html, re.I)
            if granicus_match and not result["public_comment"]:
                result["public_comment"] = {
                    "url": granicus_match.group(1),
                    "description": "Granicus meeting portal"
                }

    except PlaywrightTimeout as e:
        result["errors"].append(f"Timeout loading page: {str(e)}")
    except Exception as e:
        result["errors"].append(f"Error: {str(e)}")
    finally:
        page.close()

    print(f"  Members found: {len(result['council_members'])}")
    print(f"  Errors: {len(result['errors'])}")

    return result


def scrape_all_cities(cities_to_scrape=None):
    """Scrape data for all (or specified) cities."""

    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for city_name, city_info in OC_CITIES.items():
            if cities_to_scrape and city_name not in cities_to_scrape:
                continue

            if city_info.get("state") == "done":
                print(f"\nSkipping {city_name} (already done)")
                continue

            try:
                result = scrape_city_council(city_name, city_info, browser)
                results[city_name] = result

                # Save after each city in case of crash
                save_results(results)

                # Be nice to servers
                time.sleep(2)

            except Exception as e:
                print(f"ERROR scraping {city_name}: {e}")
                results[city_name] = {
                    "city": city_name,
                    "error": str(e),
                    "scraped_at": datetime.now().isoformat()
                }

        browser.close()

    return results


def save_results(results):
    """Save results to JSON file."""
    output_path = Path(__file__).parent / "oc_council_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")


def main():
    print("=" * 60)
    print("Orange County City Council Data Scraper")
    print("=" * 60)
    print(f"Total cities to scrape: {len([c for c in OC_CITIES.values() if c.get('state') != 'done'])}")
    print(f"Already completed: {len([c for c in OC_CITIES.values() if c.get('state') == 'done'])}")

    # Check for command line args
    if len(sys.argv) > 1:
        if sys.argv[1] == "--city" and len(sys.argv) > 2:
            city_name = " ".join(sys.argv[2:])
            if city_name in OC_CITIES:
                results = scrape_all_cities([city_name])
            else:
                print(f"City not found: {city_name}")
                print(f"Available cities: {', '.join(sorted(OC_CITIES.keys()))}")
                return
        elif sys.argv[1] == "--list":
            print("\nAll Orange County cities:")
            for city in sorted(OC_CITIES.keys()):
                status = OC_CITIES[city].get("state", "needs_scrape")
                print(f"  {city}: {status}")
            return
        elif sys.argv[1] == "--verify":
            print("\nVerification mode - checking existing data...")
            # TODO: Implement verification
            return
    else:
        results = scrape_all_cities()

    save_results(results)

    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)

    # Summary
    total_members = sum(len(r.get("council_members", [])) for r in results.values())
    total_errors = sum(len(r.get("errors", [])) for r in results.values())
    print(f"Cities scraped: {len(results)}")
    print(f"Council members found: {total_members}")
    print(f"Total errors: {total_errors}")


if __name__ == "__main__":
    main()
