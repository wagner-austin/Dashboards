"""
Stanton City Council Scraper
Dynamically discovers council members from website.
Enhanced with external source discovery for bios, campaign sites, and social media.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class StantonScraper(BaseScraper):
    """Stanton - PHP website with individual bio pages."""

    CITY_NAME = "Stanton"
    PLATFORM = "custom"
    CITY_DOMAIN = "stantonca.gov"
    BASE_URL = "https://www.stantonca.gov"
    COUNCIL_URL = "https://www.stantonca.gov/government/city_council.php"
    AGENDAS_URL = "https://www.stantonca.gov/government/agendas___minutes/city_council.php"
    CLERK_URL = "https://www.stantonca.gov/departments/administration/city_clerk.php"

    # Known term dates - Stanton has 4 districts + at-large mayor
    # Mayor elected at-large, council members by district
    # Districts 2, 4 elected 2024 (term ends 2028)
    # Districts 1, 3 + Mayor elected 2022 (term ends 2026)
    KNOWN_TERMS = {
        "david j. shawver": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "david shawver": {"district": "At-Large", "term_start": 2022, "term_end": 2026},
        "gary taylor": {"district": "District 3", "term_start": 2022, "term_end": 2026},
        "victor barrios": {"district": "District 2", "term_start": 2024, "term_end": 2028},
        "donald torres": {"district": "District 1", "term_start": 2022, "term_end": 2026},
        "john d. warren": {"district": "District 4", "term_start": 2024, "term_end": 2028},
        "john warren": {"district": "District 4", "term_start": 2024, "term_end": 2028},
    }

    def get_member_info(self, name):
        """Get district and term info for a member."""
        name_lower = name.lower().strip()
        for known_name, info in self.KNOWN_TERMS.items():
            if known_name in name_lower or name_lower in known_name:
                return info
            # Check last name match
            known_last = known_name.split()[-1]
            if known_last in name_lower:
                return info
        return None

    def get_urls(self):
        return {
            "council": self.COUNCIL_URL,
            "agendas": self.AGENDAS_URL,
        }

    async def extract_bio_revize(self, member_name):
        """
        Extract biographical text from Revize CMS page.
        Stanton uses Revize which has a different structure than CivicPlus.
        """
        try:
            text = await self.get_page_text()
            last_name = member_name.split()[-1].lower()

            # Split into paragraphs
            paragraphs = text.split('\n')
            bio_parts = []

            for p in paragraphs:
                p = p.strip()
                # Skip short lines, navigation, headers
                if len(p) < 80 or len(p) > 2000:
                    continue

                # Skip navigation/menu items
                skip_patterns = [
                    'home', 'government', 'departments', 'services',
                    'skip to', 'search', 'menu', 'contact us', 'quick links',
                    'city hall', 'monday', 'tuesday', 'hours:', 'phone:',
                    'email:', 'fax:', 'address:'
                ]
                if any(skip.lower() in p.lower()[:50] for skip in skip_patterns):
                    continue

                # Look for biographical content
                has_bio_words = bool(re.search(
                    r'(is a|has been|was born|grew up|resident|community|'
                    r'served|experience|career|worked|years|elected|'
                    r'volunteer|member of|active in|dedicated|taught|'
                    r'graduated|degree|university|college|family|wife|husband|'
                    r'children|enjoys|interests)', p, re.I
                ))

                has_name = last_name in p.lower()

                if has_bio_words and (has_name or len(bio_parts) > 0):
                    bio_parts.append(p)
                    if len(bio_parts) >= 3:
                        break

            if bio_parts:
                bio = ' '.join(bio_parts)
                bio = re.sub(r'\s+', ' ', bio).strip()
                return bio[:1500] if len(bio) > 1500 else bio

        except Exception as e:
            self.results["errors"].append(f"extract_bio_revize: {str(e)}")

        return None

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

    async def scrape_zoom_from_agenda(self):
        """Extract Zoom info from latest agenda PDF."""
        zoom_info = {}
        phone_numbers = []

        print("    Scraping Zoom info from agenda...")
        try:
            await self.page.goto(self.AGENDAS_URL, timeout=30000)
            await self.page.wait_for_timeout(2000)

            # Find first agenda PDF link
            links = await self.page.query_selector_all('a')
            agenda_url = None
            for link in links:
                href = await link.get_attribute('href') or ''
                text = (await link.inner_text()).strip().lower()
                if '.pdf' in href.lower() and ('agd' in href.lower() or text == 'agenda'):
                    if not href.startswith('http'):
                        href = urljoin(self.BASE_URL, href)
                    agenda_url = href
                    break

            if agenda_url:
                # Download and parse PDF
                import urllib.request
                import urllib.parse
                import tempfile
                import os

                # URL-encode the path while preserving the scheme and domain
                try:
                    parsed = urllib.parse.urlparse(agenda_url)
                    encoded_path = urllib.parse.quote(parsed.path, safe='/')
                    encoded_query = urllib.parse.quote(parsed.query, safe='=&')
                    agenda_url = f"{parsed.scheme}://{parsed.netloc}{encoded_path}"
                    if encoded_query:
                        agenda_url += f"?{encoded_query}"
                except:
                    pass

                try:
                    req = urllib.request.Request(agenda_url, headers={'User-Agent': 'Mozilla/5.0'})
                    response = urllib.request.urlopen(req, timeout=30)

                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                        f.write(response.read())
                        temp_path = f.name

                    try:
                        import pdfplumber
                        with pdfplumber.open(temp_path) as pdf:
                            text = ''
                            for page in pdf.pages[:3]:
                                text += page.extract_text() or ''

                            # Extract Zoom URL
                            zoom_url_match = re.search(
                                r'(https?://[^\s]*zoom\.us/j/\d+[^\s]*)',
                                text
                            )
                            if zoom_url_match:
                                zoom_info['url'] = zoom_url_match.group(1).rstrip('.')

                            # Extract Meeting ID
                            meeting_id_match = re.search(
                                r'Meeting ID[:\s]*(\d{3}[\s-]?\d{4}[\s-]?\d{4})',
                                text, re.I
                            )
                            if meeting_id_match:
                                zoom_info['meeting_id'] = meeting_id_match.group(1).replace(' ', '-')

                            # Extract passcode
                            passcode_match = re.search(
                                r'(?:passcode|password)[:\s]*([A-Za-z0-9]+)',
                                text, re.I
                            )
                            if passcode_match:
                                zoom_info['passcode'] = passcode_match.group(1)

                            # Extract phone numbers
                            phone_match = re.search(
                                r'Dial[^+]*\+1\s*\((\d{3})\)\s*(\d{3})[-\s]?(\d{4})',
                                text, re.I
                            )
                            if phone_match:
                                phone = f"{phone_match.group(1)}-{phone_match.group(2)}-{phone_match.group(3)}"
                                phone_numbers.append(phone)

                            if zoom_info:
                                print(f"      Found Zoom: ID={zoom_info.get('meeting_id')}")

                    except ImportError:
                        print("      pdfplumber not installed, skipping PDF parsing")

                    os.unlink(temp_path)

                except Exception as e:
                    print(f"      Error downloading agenda: {e}")

        except Exception as e:
            self.results["errors"].append(f"scrape_zoom: {str(e)}")

        return zoom_info, phone_numbers

    async def scrape_city_info(self):
        """Scrape city-level info dynamically, matching Irvine's structure."""
        # First get Zoom info from agenda
        zoom_info, phone_numbers = await self.scrape_zoom_from_agenda()

        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": None,
            "meeting_time": None,
            "meeting_location": None,
            "zoom": zoom_info,
            "phone_numbers": phone_numbers,
            "tv_channels": [],
            "clerk": {},
            "public_comment": {},
            "portals": {
                "agenda_center": self.AGENDAS_URL,
            }
        }

        # Scrape meeting info from council page
        print("    Scraping meeting info...")
        try:
            await self.page.goto(self.COUNCIL_URL, timeout=30000)
            await self.page.wait_for_timeout(2000)
            text = await self.get_page_text()

            # Meeting schedule - look for patterns
            schedule_match = re.search(
                r'(second and fourth|2nd and 4th)\s+(tuesday|monday|wednesday)',
                text, re.I
            )
            if schedule_match:
                day = schedule_match.group(2).capitalize()
                city_info["meeting_schedule"] = f"2nd and 4th {day}s"
            else:
                city_info["meeting_schedule"] = "2nd and 4th Tuesdays"  # Known default

            # Meeting time
            time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:p\.?m\.?|a\.?m\.?))', text, re.I)
            if time_match:
                city_info["meeting_time"] = time_match.group(1).upper().replace(".", "")
            else:
                city_info["meeting_time"] = "6:30 PM"  # Known default

            # Location - Stanton City Hall
            city_info["meeting_location"] = {
                "name": "City Council Chambers",
                "address": "7800 Katella Avenue",
                "city_state_zip": "Stanton, CA 90680"
            }

        except Exception as e:
            self.results["errors"].append(f"scrape_meeting_info: {str(e)}")

        # Scrape clerk info
        print("    Scraping clerk info...")
        try:
            # Try city clerk page
            clerk_url = "https://www.stantonca.gov/government/city_clerk.php"
            await self.page.goto(clerk_url, timeout=30000)
            await self.page.wait_for_timeout(2000)
            text = await self.get_page_text()

            # Clerk phone
            phone_match = re.search(
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                text
            )
            if phone_match:
                city_info["clerk"]["phone"] = phone_match.group(0)

            # Clerk email
            emails = self.extract_emails(text)
            clerk_emails = [e for e in emails if "clerk" in e.lower() or self.CITY_DOMAIN in e.lower()]
            if clerk_emails:
                city_info["clerk"]["email"] = clerk_emails[0]

            city_info["clerk"]["title"] = "City Clerk"

            # Try to find clerk name
            name_match = re.search(r'City Clerk[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
            if name_match:
                city_info["clerk"]["name"] = name_match.group(1)

        except Exception as e:
            self.results["errors"].append(f"scrape_clerk_info: {str(e)}")

        # Public comment info - Stanton has Zoom and email
        city_info["public_comment"] = {
            "in_person": True,
            "remote_live": bool(city_info.get("zoom")),  # True if Zoom found
            "ecomment": False,
            "written_email": True,
            "time_limit": "3 minutes per speaker",
            "email": city_info["clerk"].get("email", "pvazquez@stantonca.gov"),
            "deadline": "5:00 PM on meeting day"
        }

        # Council structure
        city_info["council"] = {
            "size": 5,
            "districts": 4,
            "at_large": 1,
            "mayor_elected": True,
            "notes": "Mayor elected at-large; council members by district"
        }

        # Elections
        city_info["elections"] = {
            "next_election": "2026-11-03",
            "seats_up": ["Mayor (At-Large)", "District 1", "District 3"],
            "term_length": 4,
            "election_system": "mixed",
            "term_limits": "Two 4-year terms (Measure RR 2016)"
        }

        return city_info

    async def scrape_meetings(self):
        """Scrape meeting archive from agenda page."""
        meetings = {}  # Use date as key to merge agenda/minutes

        print("    Scraping meeting archive...")
        try:
            await self.page.goto(self.AGENDAS_URL, timeout=30000)
            await self.page.wait_for_timeout(3000)  # Extra wait for dynamic content

            # Get all links and filter for agenda/minutes
            all_links = await self.page.query_selector_all('a')
            links = []
            for link in all_links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip().lower()
                if ".pdf" in href.lower() or text in ["agenda", "minutes"]:
                    links.append(link)
            print(f"      Found {len(links)} potential meeting links")

            for link in links:
                try:
                    href = await link.get_attribute("href") or ""
                    text = (await link.inner_text()).strip().lower()

                    if not href:
                        continue

                    # Check if it's an agenda or minutes link
                    is_agenda = "agd" in href.lower() or text == "agenda"
                    is_minutes = "min" in href.lower() or text == "minutes"

                    if not is_agenda and not is_minutes:
                        continue

                    # Parse date from href (CC AGD 01-27-26.pdf pattern)
                    date_match = re.search(
                        r'(\d{1,2})[-_](\d{1,2})[-_](\d{2,4})',
                        href
                    )
                    if not date_match:
                        continue

                    month = date_match.group(1)
                    day = date_match.group(2)
                    year = date_match.group(3)

                    # Expand 2-digit year
                    if len(year) == 2:
                        year = f"20{year}"

                    date_str = f"{month}/{day}/{year}"

                    # Build full URL
                    full_url = urljoin(self.BASE_URL, href)

                    # Create or update meeting entry
                    if date_str not in meetings:
                        meetings[date_str] = {
                            "date": date_str,
                            "name": "City Council Meeting",
                        }

                    if is_agenda:
                        meetings[date_str]["agenda_url"] = full_url
                    if is_minutes:
                        meetings[date_str]["minutes_url"] = full_url

                except Exception:
                    continue

            # Convert to list and sort by date (newest first)
            meeting_list = list(meetings.values())

            def parse_date(date_str):
                try:
                    parts = date_str.split('/')
                    return (int(parts[2]), int(parts[0]), int(parts[1]))
                except:
                    return (0, 0, 0)

            meeting_list.sort(key=lambda m: parse_date(m["date"]), reverse=True)

            print(f"      Found {len(meeting_list)} meeting records")
            return meeting_list

        except Exception as e:
            self.results["errors"].append(f"scrape_meetings: {str(e)}")

        return []

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
            # Get district and term info from KNOWN_TERMS
            member_info = self.get_member_info(member["name"])
            district = member_info.get("district") if member_info else None
            term_start = member_info.get("term_start") if member_info else None
            term_end = member_info.get("term_end") if member_info else None

            if member.get("url"):
                data = await self.scrape_member_page(
                    member, self.BASE_URL, self.CITY_DOMAIN, main_phones
                )
                # Override with KNOWN_TERMS data
                data["district"] = district
                data["term_start"] = term_start
                data["term_end"] = term_end

                # Fix photo URL - make absolute if relative
                if data.get("photo_url") and not data["photo_url"].startswith("http"):
                    data["photo_url"] = urljoin(self.BASE_URL, data["photo_url"])

                # Use Revize-specific bio extraction if base method didn't find bio
                if not data.get("bio"):
                    bio = await self.extract_bio_revize(member["name"])
                    if bio:
                        data["bio"] = bio
                        print(f"      Bio (Revize): {len(bio)} chars")

            else:
                # No bio page, use main page data
                data = {
                    "name": member["name"],
                    "position": member["position"],
                    "district": district,
                    "email": self.match_email_to_name(
                        member["name"], main_emails, self.CITY_DOMAIN
                    ),
                    "phone": main_phones[0] if main_phones else None,
                    "profile_url": None,
                    "photo_url": None,
                    "bio": None,
                    "term_start": term_start,
                    "term_end": term_end,
                }
                print(f"    Member {member['name']} has no bio page")

            self.add_council_member(**data)

        self.match_emails_to_members(city_domain=self.CITY_DOMAIN)

        # Scrape city-level info
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        # Scrape meeting archive
        meetings = await self.scrape_meetings()
        self.results["meetings"] = meetings

        return self.get_results()
