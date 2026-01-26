"""
Buena Park City Council Scraper
Dynamically discovers council members from website.
Scrapes meeting archives from Cablecast video portal.
"""
import re
from datetime import datetime
from ..base import BaseScraper


class BuenaParkScraper(BaseScraper):
    """Buena Park - PHP site with all info on main council page + Cablecast meetings."""

    CITY_NAME = "Buena Park"
    PLATFORM = "custom"
    CITY_DOMAIN = "buenapark.com"
    BASE_URL = "https://www.buenapark.com"
    COUNCIL_URL = "https://www.buenapark.com/city_departments/city_council/council_members.php"
    CABLECAST_URL = "https://buenapark.cablecast.tv/"
    AGENDALINK_URL = "https://horizon.agendalink.app/engage/buenaparkca/agendas"

    # Known term dates - Buena Park uses by-district elections
    # Districts 1, 5 elected 2022 (term ends 2026)
    # Districts 2 elected 2024 special election (term ends 2026)
    # Districts 3, 4 elected 2024 (term ends 2028)
    KNOWN_TERMS = {
        "connor traut": {"district": "District 5", "term_start": 2022, "term_end": 2026},
        "joyce ahn": {"district": "District 1", "term_start": 2022, "term_end": 2026},
        "susan sonne": {"district": "District 3", "term_start": 2024, "term_end": 2028},
        "carlos franco": {"district": "District 2", "term_start": 2024, "term_end": 2026},  # Special election
        "lamiya hoque": {"district": "District 4", "term_start": 2024, "term_end": 2028},
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
            "cablecast": self.CABLECAST_URL,
            "agendalink": self.AGENDALINK_URL,
        }

    async def discover_members(self):
        """
        Discover council members from the main council page.
        Buena Park pattern: All members on one page with photos and info.
        Look for patterns like "Mayor Connor Traut" or "Council Member Joyce Ahn"
        """
        members = []

        try:
            text = await self.get_page_text()
            text_lines = text.split('\n')

            # Pattern to match member lines
            # Examples: "Mayor Connor Traut", "Vice Mayor Lamiya Hoque", "Council Member Carlos Franco"
            # Name must start with capital letter and be a proper name (not words like "and", "to", "serve")
            member_pattern = re.compile(
                r'(Mayor|Vice Mayor|Council\s*Member)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                re.IGNORECASE
            )

            # Skip words that indicate descriptive text, not names
            skip_first_words = ["and", "to", "the", "one", "each", "another", "who", "elected"]

            seen_names = set()

            for line in text_lines:
                match = member_pattern.search(line)
                if match:
                    position_raw = match.group(1).strip()
                    name = match.group(2).strip()

                    # Skip if name starts with descriptive words (not a real name)
                    first_word = name.split()[0].lower() if name.split() else ""
                    if first_word in skip_first_words:
                        continue

                    # Skip very short names or names that look like text fragments
                    if len(name) < 5 or len(name.split()) < 2:
                        continue

                    # Normalize position
                    pos_lower = position_raw.lower()
                    if "vice mayor" in pos_lower:
                        position = "Vice Mayor"
                    elif "mayor" in pos_lower:
                        position = "Mayor"
                    else:
                        position = "Councilmember"

                    # Skip duplicates
                    if name.lower() in seen_names:
                        continue
                    seen_names.add(name.lower())

                    # Try to find district from nearby text
                    district = None
                    district_match = re.search(rf'{re.escape(name)}.*?District\s*(\d+)', text, re.IGNORECASE | re.DOTALL)
                    if district_match:
                        district = f"District {district_match.group(1)}"

                    members.append({
                        "name": name,
                        "position": position,
                        "district": district,
                        "url": None  # No individual profile pages
                    })
                    print(f"      Found: {name} ({position}) - {district or 'No district'}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def extract_emails_for_members(self, members):
        """Match emails to member names from page."""
        try:
            text = await self.get_page_text()
            emails = self.extract_emails(text)

            # Also get mailto links
            mailto_emails = await self.get_mailto_links()
            all_emails = list(set(emails + mailto_emails))

            for member in members:
                matched_email = self.match_email_to_name(
                    member["name"],
                    all_emails,
                    self.CITY_DOMAIN
                )
                if matched_email:
                    member["email"] = matched_email
                    print(f"      Email matched: {member['name']} -> {matched_email}")

        except Exception as e:
            self.results["errors"].append(f"extract_emails: {str(e)}")

        return members

    async def extract_photos_and_bios(self, members):
        """Extract photos and bio PDF links for each member."""
        print("    Extracting photos and bios...")

        try:
            # Get all images and links upfront
            imgs = await self.page.query_selector_all('img')
            all_links = await self.page.query_selector_all('a')

            # Build list of bio PDF links
            bio_pdfs = []
            for link in all_links:
                try:
                    href = await link.get_attribute('href') or ''
                    text = (await link.inner_text() or '').lower().strip()
                    if '.pdf' in href.lower() and ('bio' in text or 'bio' in href.lower()):
                        bio_pdfs.append(href)
                except:
                    continue

            for member in members:
                name = member["name"]
                last_name = name.split()[-1].lower()
                first_name = name.split()[0].lower()

                # Find photo - look for img with name in src or alt
                for img in imgs:
                    src = await img.get_attribute('src') or ''
                    alt = (await img.get_attribute('alt') or '').lower()

                    # Check if this image matches the member
                    if last_name in src.lower() or last_name in alt or first_name in src.lower():
                        # Make absolute URL
                        if src and not src.startswith('http'):
                            src = f"{self.BASE_URL}/{src.lstrip('/')}"
                        member["photo_url"] = src
                        print(f"      Photo found: {name}")
                        break

                # Find bio PDF
                for href in bio_pdfs:
                    href_lower = href.lower()
                    if last_name in href_lower or first_name in href_lower:
                        if not href.startswith('http'):
                            href = f"{self.BASE_URL}/{href.lstrip('/')}"
                        member["bio_url"] = href
                        print(f"      Bio PDF found: {name}")
                        break

        except Exception as e:
            self.results["errors"].append(f"extract_photos_bios: {str(e)}")

        return members

    async def scrape_bio_from_pdf(self, pdf_url, member_name):
        """Extract bio text from a PDF."""
        import urllib.request
        import urllib.parse
        import tempfile
        import os

        try:
            # URL encode
            parsed = urllib.parse.urlparse(pdf_url)
            encoded_path = urllib.parse.quote(parsed.path, safe='/')
            pdf_url = f"{parsed.scheme}://{parsed.netloc}{encoded_path}"

            req = urllib.request.Request(pdf_url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=30)

            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                f.write(response.read())
                temp_path = f.name

            try:
                import pdfplumber
                with pdfplumber.open(temp_path) as pdf:
                    text = ''
                    for page in pdf.pages[:2]:  # First 2 pages
                        text += page.extract_text() or ''

                    if text:
                        # Clean up and extract relevant bio content
                        lines = text.split('\n')
                        bio_parts = []
                        last_name = member_name.split()[-1].lower()

                        for line in lines:
                            line = line.strip()
                            if len(line) < 50 or len(line) > 1500:
                                continue

                            # Skip headers/footers
                            skip_patterns = ['city of buena park', 'page', 'district', 'contact']
                            if any(skip.lower() in line.lower()[:30] for skip in skip_patterns):
                                continue

                            # Look for biographical content
                            has_bio_words = bool(re.search(
                                r'(is a|has been|was born|grew up|resident|community|'
                                r'served|experience|career|worked|years|elected|'
                                r'volunteer|member of|active in|dedicated|family|'
                                r'graduated|degree|university|college)', line, re.I
                            ))

                            if has_bio_words:
                                bio_parts.append(line)
                                if len(bio_parts) >= 3:
                                    break

                        if bio_parts:
                            bio = ' '.join(bio_parts)
                            bio = re.sub(r'\s+', ' ', bio).strip()
                            return bio[:1500] if len(bio) > 1500 else bio

            except ImportError:
                pass  # pdfplumber not installed

            os.unlink(temp_path)

        except Exception as e:
            self.results["errors"].append(f"scrape_bio_pdf: {str(e)}")

        return None

    async def scrape_city_info(self):
        """Scrape city-level info matching Irvine's structure."""
        city_info = {
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": "2nd and 4th Tuesdays",
            "meeting_time": "5:00 PM",
            "meeting_location": {
                "name": "City Hall Council Chambers",
                "address": "6650 Beach Boulevard",
                "city_state_zip": "Buena Park, CA 90621"
            },
            "zoom": {
                # Zoom available but Meeting ID changes per meeting (on agenda)
                "note": "Meeting ID changes per meeting - check agenda"
            },
            "phone_numbers": [],
            "tv_channels": [
                {"provider": "Spectrum", "channel": "3"},
                {"provider": "AT&T U-Verse", "channel": "99"}
            ],
            "live_stream": self.CABLECAST_URL,
            "clerk": {
                "name": "Adria M. Vicuna",
                "title": "Director of Government & Community Relations/City Clerk",
                "phone": "(714) 562-3754",
                "email": "cityclerk@buenapark.com"
            },
            "public_comment": {
                "in_person": True,
                "remote_live": False,  # Zoom is for viewing only, no remote public comment
                "ecomment": False,
                "written_email": True,
                "time_limit": "3 minutes per speaker",
                "email": "cityclerk@buenapark.com"
            },
            "portals": {
                "cablecast": self.CABLECAST_URL,
                "agendalink": self.AGENDALINK_URL,
                "live_stream": f"{self.CABLECAST_URL}watch-now?site=1",
            },
            "council": {
                "size": 5,
                "districts": 5,
                "at_large": 0,
                "mayor_elected": False,  # Mayor rotates among council
                "expanded_date": None
            },
            "elections": {
                "next_election": "2026-11-03",
                "seats_up": ["District 1", "District 2", "District 5"],
                "term_length": 4,
                "election_system": "by-district"
            }
        }
        return city_info

    async def scrape_meetings(self):
        """Scrape meeting data from Cablecast portal."""
        meetings = []
        seen_keys = set()

        print(f"    Scraping meetings from Cablecast...")

        try:
            await self.page.goto(self.CABLECAST_URL, timeout=60000, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # Cablecast shows meetings as video thumbnails with titles
            # Look for city council meeting entries
            meeting_links = await self.page.query_selector_all('a[href*="show"]')

            for link in meeting_links:
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute("href") or ""

                    # Filter for city council meetings
                    if "council" not in text.lower():
                        continue

                    # Extract date from text - patterns like "January 13, 2026" or "01/13/2026"
                    date_match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", text)
                    if not date_match:
                        date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
                        if date_match:
                            month, day, year = date_match.groups()
                            month_names = ["January", "February", "March", "April", "May", "June",
                                          "July", "August", "September", "October", "November", "December"]
                            month_str = month_names[int(month) - 1]
                            date_str = f"{month_str} {day}, {year}"
                        else:
                            continue
                    else:
                        month_str, day_str, year_str = date_match.groups()
                        date_str = f"{month_str} {day_str}, {year_str}"

                    video_url = href if href.startswith("http") else f"{self.CABLECAST_URL.rstrip('/')}{href}"

                    key = f"{date_str}|{video_url}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    meetings.append({
                        "name": "City Council Meeting",
                        "date": date_str,
                        "video_url": video_url,
                        "agenda_url": None,  # Agendas are on AgendaLink
                        "minutes_url": None
                    })
                except Exception:
                    continue

            def parse_date(d):
                try:
                    return datetime.strptime(d, "%B %d, %Y")
                except ValueError:
                    return datetime.min
            meetings.sort(key=lambda m: parse_date(m["date"]), reverse=True)
            print(f"      Found {len(meetings)} City Council meetings")

        except Exception as e:
            self.results["errors"].append(f"scrape_meetings: {str(e)}")

        return meetings

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        # Visit main council page
        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])

        # Discover members dynamically
        print("    Discovering council members...")
        members = await self.discover_members()

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        # Match emails to members
        print("    Matching emails to members...")
        members = await self.extract_emails_for_members(members)

        # Extract photos and bio PDF links
        members = await self.extract_photos_and_bios(members)

        # Extract bios from PDFs
        print("    Extracting bios from PDFs...")
        for member in members:
            if member.get("bio_url"):
                bio = await self.scrape_bio_from_pdf(member["bio_url"], member["name"])
                if bio:
                    member["bio"] = bio
                    print(f"      Bio extracted: {member['name']} ({len(bio)} chars)")

        print(f"    Found {len(members)} members")

        # Add all members with term info from KNOWN_TERMS
        for member in members:
            member_info = self.get_member_info(member["name"])
            if member_info:
                district = member_info.get("district")
                term_start = member_info.get("term_start")
                term_end = member_info.get("term_end")
            else:
                district = member.get("district")
                term_start = None
                term_end = None

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                district=district,
                email=member.get("email"),
                phone=main_phones[0] if main_phones else None,
                profile_url=self.COUNCIL_URL,  # All on main page
                photo_url=member.get("photo_url"),
                bio=member.get("bio"),
                term_start=term_start,
                term_end=term_end,
            )

        # Scrape city-level info
        city_info = await self.scrape_city_info()
        self.results["city_info"] = city_info

        # Scrape meetings from Cablecast
        meetings = await self.scrape_meetings()
        self.results["meetings"] = meetings

        return self.get_results()
