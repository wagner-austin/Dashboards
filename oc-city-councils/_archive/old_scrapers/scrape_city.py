"""
Single City Council Scraper

Focused scraper for extracting council member data from one city at a time.
Saves detailed debug output and merges into master JSON.

Usage:
    python scrape_city.py "City Name"
    python scrape_city.py "Laguna Beach" --debug
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def load_master_data():
    """Load the master JSON file."""
    path = Path(__file__).parent / "oc_cities_master.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_master_data(data):
    """Save to master JSON file."""
    path = Path(__file__).parent / "oc_cities_master.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_emails(text):
    """Extract email addresses from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = list(set(re.findall(pattern, text.lower())))
    # Filter out common non-personal emails
    skip = ['webmaster', 'info@', 'contact@', 'noreply', 'support@', 'admin@']
    return [e for e in emails if not any(s in e for s in skip)]


def extract_phones(text):
    """Extract phone numbers from text."""
    pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    matches = re.findall(pattern, text)
    # Normalize format
    phones = []
    for m in matches:
        digits = re.sub(r'\D', '', m)
        if len(digits) == 10:
            phones.append(f"({digits[:3]}) {digits[3:6]}-{digits[6:]}")
    return list(set(phones))


def find_member_links(page, base_url):
    """Find links to individual council member pages."""
    member_links = []
    seen_urls = set()

    all_links = page.query_selector_all("a")

    for link in all_links:
        try:
            href = link.get_attribute("href") or ""
            text = link.inner_text().strip()

            # Skip empty/nav links
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue
            if not text or len(text) < 3 or len(text) > 80:
                continue

            href_lower = href.lower()
            text_lower = text.lower()

            # URL patterns for member pages
            url_patterns = [
                "/mayor", "/council-member", "/councilmember",
                "/councilwoman", "/councilman", "/district-",
                "/elected", "/official", "-mayor", "-council"
            ]

            # Skip common non-member links
            skip_patterns = [
                "meeting", "agenda", "minute", "video", "calendar",
                "contact-us", "department", "service", "news", "event",
                "form", "document", "report", "budget", "plan"
            ]

            if any(s in href_lower for s in skip_patterns):
                continue

            is_member_url = any(p in href_lower for p in url_patterns)

            # Text patterns suggesting a name
            # Names typically: First Last, or Title First Last
            words = text.split()
            looks_like_name = (
                2 <= len(words) <= 5 and
                all(w[0].isupper() for w in words if w.isalpha()) and
                not any(w.lower() in ['city', 'council', 'meeting', 'agenda', 'the', 'of', 'and'] for w in words[:2])
            )

            # Check if text contains position indicators
            has_position = any(p in text_lower for p in ['mayor', 'councilmember', 'council member', 'district'])

            if is_member_url or (looks_like_name and has_position) or (is_member_url and looks_like_name):
                full_url = urljoin(base_url, href)
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    member_links.append({
                        "text": text,
                        "url": full_url,
                        "reason": f"url:{is_member_url}, name:{looks_like_name}, pos:{has_position}"
                    })
        except Exception:
            continue

    return member_links


def extract_member_from_page(page, url, name_hint):
    """Extract council member data from their profile page."""
    member = {
        "name": name_hint,
        "position": None,
        "district": None,
        "email": None,
        "phone": None,
        "website": None,
        "city_profile": url,
        "instagram": None,
        "photo": None
    }

    try:
        page.goto(url, wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(1500)

        body = page.query_selector("body")
        if not body:
            return member

        text = body.inner_text()
        html = page.content()

        # Extract name from page title or headers
        title = page.title()
        h1 = page.query_selector("h1")
        h1_text = h1.inner_text() if h1 else ""

        # Determine position
        text_lower = text.lower()
        if "vice mayor" in text_lower or "mayor pro tem" in text_lower:
            member["position"] = "Vice Mayor"
        elif "mayor" in text_lower and "mayor" in (title.lower() + h1_text.lower()):
            member["position"] = "Mayor"
        else:
            member["position"] = "Councilmember"

        # Find district
        district_match = re.search(r"district\s*(\d+)", text_lower)
        if district_match:
            member["district"] = f"District {district_match.group(1)}"
        elif "at.?large" in text_lower.replace("-", "").replace(" ", ""):
            member["district"] = "At-Large"

        # Find email - look for mailto links first
        mailto_links = page.query_selector_all('a[href^="mailto:"]')
        for ml in mailto_links:
            href = ml.get_attribute("href") or ""
            email = href.replace("mailto:", "").split("?")[0].strip()
            if "@" in email and "webmaster" not in email.lower():
                member["email"] = email
                break

        # Fallback: extract from text
        if not member["email"]:
            emails = extract_emails(text)
            if emails:
                member["email"] = emails[0]

        # Find phone
        phones = extract_phones(text)
        if phones:
            member["phone"] = phones[0]

        # Find Instagram
        insta_links = page.query_selector_all('a[href*="instagram.com"]')
        for il in insta_links:
            href = il.get_attribute("href")
            if href and "instagram.com" in href:
                member["instagram"] = href
                break

        # Find personal website (non-city, non-social)
        all_links = page.query_selector_all("a")
        city_domain = urlparse(url).netloc
        for link in all_links:
            href = link.get_attribute("href") or ""
            link_text = (link.inner_text() or "").lower()
            if href.startswith("http"):
                link_domain = urlparse(href).netloc
                if (city_domain not in link_domain and
                    "instagram" not in href and
                    "facebook" not in href and
                    "twitter" not in href and
                    "linkedin" not in href and
                    ("website" in link_text or "personal" in link_text or
                     any(n.lower() in link_domain for n in name_hint.split() if len(n) > 3))):
                    member["website"] = href
                    break

        # Find photo
        images = page.query_selector_all("img")
        for img in images:
            src = img.get_attribute("src") or ""
            alt = (img.get_attribute("alt") or "").lower()
            # Look for profile-like images
            name_parts = [n.lower() for n in name_hint.split() if len(n) > 2]
            if any(n in alt or n in src.lower() for n in name_parts):
                member["photo"] = urljoin(url, src)
                break
            # Also look for images with common profile indicators
            if any(x in src.lower() for x in ["headshot", "portrait", "profile", "council", "official"]):
                member["photo"] = urljoin(url, src)
                break

    except Exception as e:
        print(f"    Error extracting from {url}: {e}")

    return member


def find_public_comment(page, base_url):
    """Find public comment submission method."""
    html = page.content().lower()
    text = page.query_selector("body").inner_text().lower() if page.query_selector("body") else ""

    # Look for eComment/Granicus systems
    if "granicus" in html:
        # Find Granicus Ideas/eComment link
        match = re.search(r'href="([^"]*granicusideas[^"]*)"', page.content(), re.I)
        if match:
            return {
                "url": match.group(1) if match.group(1).startswith("http") else urljoin(base_url, match.group(1)),
                "method": "Granicus eComment",
                "notes": "Submit written comments online"
            }
        match = re.search(r'href="([^"]*granicus[^"]*)"', page.content(), re.I)
        if match:
            return {
                "url": match.group(1) if match.group(1).startswith("http") else urljoin(base_url, match.group(1)),
                "method": "Granicus meeting portal",
                "notes": "Meeting agendas and video"
            }

    # Look for public comment links
    links = page.query_selector_all("a")
    for link in links:
        link_text = (link.inner_text() or "").lower()
        href = link.get_attribute("href") or ""

        if any(kw in link_text for kw in ["public comment", "ecomment", "speaker card", "public input"]):
            return {
                "url": urljoin(base_url, href),
                "method": link.inner_text().strip(),
                "notes": None
            }

    # Check for Zoom info
    zoom_match = re.search(r'zoom\w*\.(?:us|gov)/j/(\d+)', html)
    if zoom_match:
        return {
            "url": f"https://zoom.us/j/{zoom_match.group(1)}",
            "method": "Zoom public participation",
            "notes": "Join meeting via Zoom to provide verbal comment"
        }

    return None


def scrape_city(city_name, debug=False):
    """Scrape a single city's council data."""
    master = load_master_data()

    if city_name not in master["cities"]:
        print(f"City not found: {city_name}")
        print(f"Available: {', '.join(sorted(master['cities'].keys()))}")
        return None

    city = master["cities"][city_name]
    print(f"\n{'='*60}")
    print(f"Scraping: {city_name}")
    print(f"URL: {city['council_url']}")
    print(f"{'='*60}")

    result = {
        "scraped_at": datetime.now().isoformat(),
        "council_members": [],
        "public_comment": None,
        "status": "needs_verification",
        "notes": city.get("notes", []).copy()
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(30000)

        try:
            # Load council page
            print(f"\n[1] Loading council page...")
            response = page.goto(city["council_url"], wait_until="networkidle")

            if not response:
                result["notes"].append("Failed to load page - no response")
                result["status"] = "error"
                return result

            if response.status >= 400:
                result["notes"].append(f"HTTP {response.status} - trying alternate URLs")
                # Try some common alternates
                alternates = [
                    city["council_url"].replace("/city-council", "/citycouncil"),
                    city["council_url"].replace("www.", ""),
                    f"{city['website']}/government/city-council",
                    f"{city['website']}/city-hall/city-council",
                ]
                for alt in alternates:
                    try:
                        response = page.goto(alt, wait_until="networkidle", timeout=10000)
                        if response and response.status < 400:
                            result["notes"].append(f"Working URL: {alt}")
                            city["council_url"] = alt
                            break
                    except:
                        continue
                else:
                    result["status"] = "blocked"
                    result["notes"].append("All URLs blocked or errored")
                    browser.close()
                    return result

            print(f"    Status: {response.status}")
            page.wait_for_timeout(2000)

            # Save screenshot for debug
            if debug:
                ss_path = Path(__file__).parent / "debug" / f"{city_name.replace(' ', '_')}.png"
                ss_path.parent.mkdir(exist_ok=True)
                page.screenshot(path=str(ss_path), full_page=True)
                print(f"    Screenshot: {ss_path}")

            # Find member links
            print(f"\n[2] Finding council member links...")
            member_links = find_member_links(page, city["council_url"])
            print(f"    Found {len(member_links)} potential member links")

            if debug:
                for ml in member_links:
                    print(f"      - {ml['text'][:40]}: {ml['reason']}")

            # Visit each member page
            print(f"\n[3] Extracting member data...")
            for i, ml in enumerate(member_links[:10]):  # Limit to 10
                print(f"    [{i+1}] {ml['text'][:40]}...")
                member = extract_member_from_page(page, ml["url"], ml["text"])
                if member["email"] or member["phone"]:
                    result["council_members"].append(member)
                    print(f"        Email: {member['email']}")
                    print(f"        Phone: {member['phone']}")
                else:
                    print(f"        (no contact info found)")

            # Find public comment info
            print(f"\n[4] Finding public comment submission...")
            page.goto(city["council_url"], wait_until="networkidle")
            page.wait_for_timeout(1000)

            public_comment = find_public_comment(page, city["council_url"])
            if public_comment:
                result["public_comment"] = public_comment
                print(f"    Found: {public_comment['method']}")
            else:
                print(f"    Not found - may need manual lookup")

        except PlaywrightTimeout:
            result["notes"].append("Timeout loading page")
            result["status"] = "timeout"
        except Exception as e:
            result["notes"].append(f"Error: {str(e)}")
            result["status"] = "error"
        finally:
            browser.close()

    # Update master data
    city.update({
        "council_members": result["council_members"],
        "public_comment": result["public_comment"],
        "status": result["status"],
        "notes": result["notes"],
        "last_scraped": result["scraped_at"]
    })

    save_master_data(master)

    # Save individual city JSON
    city_file = Path(__file__).parent / "data" / f"{city_name.replace(' ', '_').lower()}.json"
    city_file.parent.mkdir(exist_ok=True)
    with open(city_file, "w", encoding="utf-8") as f:
        json.dump({
            "city": city_name,
            "website": city["website"],
            "council_url": city["council_url"],
            "scraped_at": result["scraped_at"],
            "status": result["status"],
            "council_members": result["council_members"],
            "public_comment": result["public_comment"],
            "notes": result["notes"]
        }, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {city_file}")

    # Summary
    print(f"\n{'='*60}")
    print(f"RESULTS for {city_name}")
    print(f"{'='*60}")
    print(f"Members found: {len(result['council_members'])}")
    print(f"Public comment: {'Yes' if result['public_comment'] else 'No'}")
    print(f"Status: {result['status']}")
    if result["notes"]:
        print(f"Notes: {'; '.join(result['notes'][-3:])}")

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python scrape_city.py \"City Name\" [--debug]")
        print("\nAvailable cities:")
        master = load_master_data()
        for city in sorted(master["cities"].keys()):
            status = master["cities"][city].get("status", "needs_research")
            print(f"  {city}: {status}")
        return

    city_name = sys.argv[1]
    debug = "--debug" in sys.argv

    scrape_city(city_name, debug)


if __name__ == "__main__":
    main()
