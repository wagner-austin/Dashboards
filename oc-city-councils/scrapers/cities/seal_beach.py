"""
Seal Beach City Council Scraper
Dynamically discovers council members, meeting info, clerk, portals, and elections.
CivicPlus platform - all members displayed on single page with table layout.
"""
import re
from datetime import datetime
from urllib.parse import urljoin
from ..base import BaseScraper


class SealBeachScraper(BaseScraper):
    """Seal Beach - CivicPlus platform with table-based council display."""

    CITY_NAME = "Seal Beach"
    PLATFORM = "civicplus"
    CITY_DOMAIN = "sealbeachca.gov"
    BASE_URL = "https://www.sealbeachca.gov"
    COUNCIL_URL = "https://www.sealbeachca.gov/Government/City-Council"
    CLERK_URL = "https://www.sealbeachca.gov/Departments/City-Clerk"
    AGENDAS_URL = "https://www.sealbeachca.gov/Government/Agendas-Notices-Meeting-Videos"
    MEETINGS_URL = "https://www.sealbeachca.gov/Government/Agendas-Notices-Meeting-Videos/Council-Commission-Meetings"
    SBTV_URL = "https://www.sealbeachca.gov/About-Us/SBTV-Cable"
    E_RECORDS_URL = "http://pubrec.sealbeachca.gov/WebLink8/"
    PUBLIC_RECORDS_URL = "https://cityofsealbeach.nextrequest.com"

    # District mapping for name lookups
    DISTRICT_NAMES = {
        "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
        "1": "1", "2": "2", "3": "3", "4": "4", "5": "5"
    }

    def get_urls(self):
        return {
            "council": self.COUNCIL_URL,
            "clerk": self.CLERK_URL,
            "agendas": self.AGENDAS_URL,
            "meetings": self.MEETINGS_URL,
            "sbtv": self.SBTV_URL,
        }

    async def discover_members(self, main_emails):
        """
        Discover council members from the main council page.
        Seal Beach displays all members in a table with photos, terms, and contact info.
        """
        members = []
        current_year = datetime.now().year

        try:
            text = await self.get_page_text()

            # Extract photos from the page - CivicPlus uses portals path
            photo_map = {}
            imgs = await self.page.query_selector_all("img")
            for img in imgs:
                src = await img.get_attribute("src") or ""
                alt = (await img.get_attribute("alt") or "").lower()

                # Skip non-portrait images
                if any(x in src.lower() for x in ["logo", "icon", "banner", "seal", "facebook", "twitter"]):
                    continue

                if "/portals/" in src.lower() or "/images/" in src.lower():
                    # Make absolute URL
                    if src.startswith("/"):
                        src = urljoin(self.BASE_URL, src)
                    # Try to match to a name from alt text
                    if alt:
                        photo_map[alt] = src

            # Parse member data from page text
            # Seal Beach format: Name, Position info, District, Term info, Email, Phones
            for email in main_emails:
                local_part = email.split("@")[0].lower()

                # Match email to name patterns
                name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-zA-Z]+)'
                name_matches = re.findall(name_pattern, text)

                matched_name = None
                for name in name_matches:
                    name_clean = name.strip()
                    name_parts = name_clean.lower().split()
                    if len(name_parts) < 2:
                        continue

                    first_name = name_parts[0]
                    last_name = name_parts[-1]

                    # Check if email matches this name
                    if (local_part == f"{first_name[0]}{last_name}" or
                        local_part == f"{first_name}{last_name}" or
                        local_part == last_name):
                        matched_name = name_clean
                        break

                if not matched_name:
                    continue

                # Avoid duplicates
                if any(m["name"].lower() == matched_name.lower() for m in members):
                    continue

                # Get text context around the name for parsing
                # Use larger window to capture term info which may be further down
                name_idx = text.find(matched_name)
                if name_idx < 0:
                    name_idx = text.lower().find(matched_name.lower())
                context = text[max(0, name_idx - 100):name_idx + 1500] if name_idx >= 0 else ""

                # Determine position based on year designations
                position = "Councilmember"
                current_year_str = str(current_year)

                # Mayor (not Pro Tem) for current year
                if re.search(rf'{current_year_str}\s*(?:&|,)?\s*Mayor(?!\s+Pro)', context, re.I):
                    position = "Mayor"
                elif re.search(rf'Mayor(?!\s+Pro).*?{current_year_str}', context, re.I):
                    position = "Mayor"
                # Mayor Pro Tem for current year
                elif re.search(rf'{current_year_str}\s*Mayor\s+Pro\s+Tem', context, re.I):
                    position = "Mayor Pro Tem"
                elif re.search(rf'Mayor\s+Pro\s+Tem.*?{current_year_str}', context, re.I):
                    position = "Mayor Pro Tem"

                # Extract district
                district = None
                district_match = re.search(
                    r'District\s+(One|Two|Three|Four|Five|\d+)',
                    context, re.IGNORECASE
                )
                if district_match:
                    district_text = district_match.group(1).lower()
                    district_num = self.DISTRICT_NAMES.get(district_text, district_text)
                    district = f"District {district_num}"

                # Extract term end year
                # Seal Beach format: table row with District, then Term Expires
                # Look for the year that appears immediately after the district text
                term_end = None

                if district:
                    # Find text after district designation
                    district_text_pattern = district.replace("District ", "")  # e.g., "1", "2", etc.
                    # Look for patterns like "District One" or just the number followed by a year
                    post_district = re.search(
                        rf'District\s+(?:One|Two|Three|Four|Five|{district_text_pattern})\s*.*?\b(202[4-9])\b',
                        context, re.I | re.DOTALL
                    )
                    if post_district:
                        term_end = int(post_district.group(1))

                # Fallback: look for year near email if district approach didn't work
                if not term_end:
                    email_idx = text.find(email)
                    if email_idx >= 0:
                        # Very narrow window around email
                        email_context = text[max(0, email_idx - 100):email_idx + 100]
                        years = re.findall(r'\b(202[6-9])\b', email_context)  # Only look for future years
                        if years:
                            term_end = int(years[0])  # Take first one found


                # Extract phones - look for extension patterns
                phone = None
                phone_alt = None
                phone_matches = re.findall(
                    r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?:\s*(?:x|ext\.?)\s*\d+)?',
                    context, re.I
                )
                if phone_matches:
                    phone = phone_matches[0]
                    if len(phone_matches) > 1:
                        phone_alt = phone_matches[1]

                # Find photo URL
                photo_url = None
                name_lower = matched_name.lower()
                last_name_lower = matched_name.split()[-1].lower()
                for alt_text, url in photo_map.items():
                    if last_name_lower in alt_text or name_lower in alt_text:
                        photo_url = url
                        break

                members.append({
                    "name": matched_name,
                    "position": position,
                    "district": district,
                    "email": email,
                    "phone": phone,
                    "phone_alt": phone_alt,
                    "photo_url": photo_url,
                    "term_end": term_end,
                })
                print(f"      Found: {matched_name} ({position}) - District {district}")

        except Exception as e:
            self.results["errors"].append(f"discover_members: {str(e)}")

        return members

    async def scrape_city_info(self):
        """Scrape city-level info: meeting schedule, location, clerk, public comment."""
        city_info = {
            "city_name": self.CITY_NAME,
            "website": self.BASE_URL,
            "council_url": self.COUNCIL_URL,
            "meeting_schedule": None,
            "meeting_time": None,
            "meeting_location": None,
            "clerk": {},
            "public_comment": {},
            "broadcast": {},
            "portals": {
                "agendas_minutes": self.AGENDAS_URL,
                "e_records": self.E_RECORDS_URL,
                "public_records": self.PUBLIC_RECORDS_URL,
            }
        }

        # Scrape clerk info
        print("    Scraping clerk info...")
        try:
            await self.page.goto(self.CLERK_URL, timeout=30000)
            await self.page.wait_for_timeout(2000)
            text = await self.get_page_text()

            # Clerk phone with extension
            phone_match = re.search(
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?:\s*(?:x|ext\.?|extension)\s*\d+)?',
                text, re.I
            )
            if phone_match:
                city_info["clerk"]["phone"] = phone_match.group(0)

            # Hours
            hours_match = re.search(
                r'(\d{1,2}:\d{2}\s*(?:a\.?m\.?|p\.?m\.?).*?(?:to|-).*?\d{1,2}:\d{2}\s*(?:a\.?m\.?|p\.?m\.?))',
                text, re.I
            )
            if hours_match:
                city_info["clerk"]["hours"] = hours_match.group(0)

            city_info["clerk"]["title"] = "City Clerk's Office"
            city_info["clerk"]["address"] = "211 Eighth Street, Seal Beach, CA 90740"

        except Exception as e:
            self.results["errors"].append(f"scrape_clerk: {str(e)}")

        # Scrape meeting info from council page
        print("    Scraping meeting schedule...")
        try:
            await self.page.goto(self.COUNCIL_URL, timeout=30000)
            await self.page.wait_for_timeout(2000)
            text = await self.get_page_text()

            # Meeting schedule pattern
            schedule_match = re.search(
                r'(second and fourth|2nd and 4th)\s+(monday|tuesday|wednesday)',
                text, re.I
            )
            if schedule_match:
                day = schedule_match.group(2).capitalize()
                city_info["meeting_schedule"] = f"2nd and 4th {day}s"

            # Meeting time
            time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:p\.?m\.?|a\.?m\.?))', text, re.I)
            if time_match:
                city_info["meeting_time"] = time_match.group(1).upper().replace(".", "")

            # Location
            if "211 Eighth Street" in text or "Council Chambers" in text:
                city_info["meeting_location"] = {
                    "name": "City Council Chambers",
                    "address": "211 Eighth Street",
                    "city_state_zip": "Seal Beach, CA 90740"
                }

            # Public comment time limit
            limit_match = re.search(r'(\d+)[\s-]*minute', text, re.I)
            if limit_match:
                city_info["public_comment"]["time_limit"] = f"{limit_match.group(1)} minutes per speaker"

            city_info["public_comment"]["in_person"] = True

        except Exception as e:
            self.results["errors"].append(f"scrape_meetings: {str(e)}")

        # Scrape broadcast info
        print("    Scraping broadcast info...")
        try:
            await self.page.goto(self.SBTV_URL, timeout=30000)
            await self.page.wait_for_timeout(2000)
            text = await self.get_page_text()

            # Store in format expected by update_all_data.py
            city_info["tv_channels"] = [{
                "provider": "SBTV",
                "channel": "3"
            }]

            # SBTV contact info stored in broadcast sub-object
            city_info["broadcast"] = {}
            phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
            if phone_match:
                city_info["broadcast"]["sbtv_phone"] = phone_match.group(0)

            email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', text)
            if email_match:
                city_info["broadcast"]["sbtv_email"] = email_match.group(0)

        except Exception as e:
            self.results["errors"].append(f"scrape_broadcast: {str(e)}")

        return city_info

    async def scrape_elections(self):
        """Determine election info from term data."""
        current_year = datetime.now().year

        # Seal Beach elections are in even years (November)
        next_election_year = current_year if current_year % 2 == 0 else current_year + 1

        elections = {
            "next_election": f"{next_election_year}-11-03",
            "seats_up": [],  # Will be populated based on term_end dates
            "term_length": 4,
            "election_system": "district",
        }

        return elections

    async def discover_external_sources(self, member_name):
        """
        Search for external sources for a council member:
        - Campaign websites
        - Instagram profiles
        - News articles with bios
        Returns dict with discovered URLs.
        """
        sources = {
            "website": None,
            "instagram": None,
            "bio_sources": []
        }

        first_name = member_name.split()[0].lower()
        last_name = member_name.split()[-1].lower()

        # Common campaign site patterns for Seal Beach
        campaign_patterns = [
            f"https://{first_name}forsealbeach.com",
            f"https://www.{first_name}forsealbeach.com",
            f"https://{last_name}forsealbeach.com",
            f"https://www.{last_name}forsealbeach.com",
            f"https://sealbeach{first_name}.com",
            f"https://www.sealbeach{first_name}.com",
            f"https://{first_name}{last_name}.com",
            f"https://www.{first_name}{last_name}.com",
        ]

        # Try campaign site patterns
        for url in campaign_patterns:
            try:
                response = await self.page.goto(url, timeout=10000, wait_until='domcontentloaded')
                if response and response.status == 200:
                    sources["website"] = url
                    sources["bio_sources"].append(url)
                    print(f"        Found campaign site: {url}")
                    break
            except:
                continue

        # Search page for Instagram links
        try:
            await self.page.goto(self.COUNCIL_URL, timeout=30000)
            await self.page.wait_for_timeout(1000)

            # Look for Instagram links on the council page
            links = await self.page.query_selector_all('a[href*="instagram.com"]')
            for link in links:
                href = await link.get_attribute("href") or ""
                if "instagram.com" in href:
                    # Check if this link is near the member's name
                    parent_text = await link.evaluate("el => el.closest('tr, div, section')?.innerText || ''")
                    if last_name.lower() in parent_text.lower():
                        sources["instagram"] = href
                        print(f"        Found Instagram: {href}")
                        break
        except Exception as e:
            pass

        # If no Instagram found on page, try common handle patterns
        if not sources["instagram"]:
            instagram_patterns = [
                f"https://www.instagram.com/{first_name}4sealbeach",
                f"https://www.instagram.com/{first_name}forsealbeach",
                f"https://www.instagram.com/{first_name}_{last_name}",
                f"https://www.instagram.com/{first_name}{last_name}",
                f"https://www.instagram.com/councilmember{first_name}",
            ]
            for ig_url in instagram_patterns:
                try:
                    response = await self.page.goto(ig_url, timeout=10000)
                    if response and response.status == 200:
                        text = await self.get_page_text()
                        # Verify it's a real profile (not 404 page)
                        if "Page Not Found" not in text and len(text) > 1000:
                            sources["instagram"] = ig_url
                            print(f"        Found Instagram: {ig_url}")
                            break
                except:
                    continue

        return sources

    async def scrape_campaign_site(self, url, member_name):
        """Scrape a campaign website for bio information."""
        bio = None
        first_name = member_name.split()[0]
        last_name = member_name.split()[-1]

        # Junk patterns - be very aggressive
        junk_patterns = [
            'donate', 'contribution', 'payment', 'cookie', 'maximum per person',
            'privacy policy', 'terms of', 'copyright', 'contact me directly',
            'subscribe', 'newsletter', 'sign up', '\$', 'credit card',
            'paypal', 'checkout', 'cart', 'purchase', 'venmo'
        ]

        try:
            await self.page.goto(url, timeout=30000)
            await self.page.wait_for_timeout(2000)

            # Try multiple pages on the campaign site
            pages_to_try = [
                url,
                url.rstrip('/') + '/about',
                url.rstrip('/') + '/about-me',
                url.rstrip('/') + '/meet-' + first_name.lower(),
                url.rstrip('/') + '/bio',
            ]

            for page_url in pages_to_try:
                try:
                    if page_url != url:
                        response = await self.page.goto(page_url, timeout=10000)
                        if not response or response.status != 200:
                            continue
                        await self.page.wait_for_timeout(1000)

                    # Try to find main content area first
                    content_selectors = [
                        'main', 'article', '.content', '#content',
                        '.about', '#about', '.bio', '#bio',
                        '.entry-content', '.post-content', '.page-content'
                    ]

                    text = ""
                    for selector in content_selectors:
                        try:
                            el = await self.page.query_selector(selector)
                            if el:
                                text = await el.inner_text()
                                if len(text) > 200:
                                    break
                        except:
                            continue

                    # Fallback to body
                    if len(text) < 200:
                        text = await self.get_page_text()

                    # Look for substantial paragraphs that seem like bio content
                    paragraphs = text.split('\n')
                    bio_parts = []

                    for p in paragraphs:
                        p = p.strip()
                        if len(p) < 80 or len(p) > 1500:
                            continue

                        # Skip if it looks like junk
                        if any(junk.lower() in p.lower() for junk in junk_patterns):
                            continue

                        # Must mention the person or Seal Beach and look biographical
                        has_name = (first_name.lower() in p.lower() or last_name.lower() in p.lower())
                        has_location = 'seal beach' in p.lower()
                        has_bio_words = bool(re.search(
                            r'(is a|has been|was born|grew up|resident|community|'
                            r'served|experience|career|worked|years|elected|'
                            r'volunteer|member of|active in|dedicated)', p, re.I))

                        if (has_name or has_location) and has_bio_words:
                            bio_parts.append(p)
                            if len(bio_parts) >= 2:
                                break

                    if bio_parts:
                        bio = ' '.join(bio_parts)
                        bio = re.sub(r'\s+', ' ', bio).strip()
                        if len(bio) > 100:
                            bio = bio[:1500]
                            break  # Found good bio, stop trying pages

                except Exception:
                    continue

        except Exception as e:
            self.results["errors"].append(f"scrape_campaign_site {url}: {str(e)}")

        return bio

    async def scrape_ocregister_bio(self, member_name):
        """Search OC Register for candidate questionnaire/bio."""
        bio = None
        first_name = member_name.split()[0]
        last_name = member_name.split()[-1]

        # Junk patterns to filter out
        junk_patterns = [
            'sign up', 'subscribe', 'newsletter', 'facebook', 'twitter',
            'reddit', 'print', 'newsroom', 'contact us', 'report an error',
            'around the web', 'bread clip', 'salt down', 'side hustles',
            'sponsored', 'advertisement', 'terms of use', 'privacy policy'
        ]

        try:
            # Navigate to OC Register search
            search_url = f"https://www.ocregister.com/?s={last_name.lower()}+seal+beach+city+council+candidate+questionnaire"
            await self.page.goto(search_url, timeout=30000)
            await self.page.wait_for_timeout(2000)

            # Look for questionnaire article links
            links = await self.page.query_selector_all('a[href*="questionnaire"], a[href*="candidate"]')
            for link in links:
                href = await link.get_attribute("href") or ""
                link_text = await link.inner_text()

                if last_name.lower() in link_text.lower() and "seal beach" in link_text.lower():
                    # Found a questionnaire article
                    try:
                        await self.page.goto(href, timeout=30000)
                        await self.page.wait_for_timeout(2000)

                        # Get article content specifically
                        article_el = await self.page.query_selector('article, .article-content, .entry-content')
                        if article_el:
                            text = await article_el.inner_text()
                        else:
                            text = await self.get_page_text()

                        # Look for the candidate's info section
                        # OC Register questionnaire format usually has: Name, Age, Occupation, then answers
                        paragraphs = text.split('\n')
                        bio_parts = []

                        for i, p in enumerate(paragraphs):
                            p = p.strip()
                            if len(p) < 30:
                                continue

                            # Skip junk
                            if any(junk.lower() in p.lower() for junk in junk_patterns):
                                continue

                            # Look for biographical info patterns
                            if (last_name.lower() in p.lower() and
                                re.search(r'(is a|has been|served|experience|background|years|career)', p, re.I)):
                                bio_parts.append(p)
                                if len(bio_parts) >= 2:
                                    break

                        if bio_parts:
                            bio = ' '.join(bio_parts)
                            bio = re.sub(r'\s+', ' ', bio).strip()
                            if len(bio) > 100:
                                bio = bio[:1500]
                                print(f"        Found OC Register bio")
                                break
                            else:
                                bio = None
                    except:
                        continue
        except Exception as e:
            self.results["errors"].append(f"scrape_ocregister: {str(e)}")

        return bio

    async def enrich_member_data(self, member):
        """
        Enrich a single member's data with external sources.
        Scrapes campaign sites, Instagram, news sources for bios.
        """
        name = member.get("name", "")
        print(f"    Enriching {name}...")

        # Discover external sources
        sources = await self.discover_external_sources(name)

        # Update member with discovered URLs
        if sources["website"]:
            member["website"] = sources["website"]
        if sources["instagram"]:
            member["instagram"] = sources["instagram"]

        # Try to get bio from campaign site first
        bio = None
        if sources["website"]:
            bio = await self.scrape_campaign_site(sources["website"], name)
            if bio:
                print(f"        Got bio from campaign site ({len(bio)} chars)")

        # If no bio from campaign site, try OC Register
        if not bio:
            bio = await self.scrape_ocregister_bio(name)

        # If still no bio, try Ballotpedia
        if not bio:
            bio = await self.scrape_ballotpedia_bio(name)

        if bio:
            member["bio"] = bio

        return member

    async def scrape_ballotpedia_bio(self, member_name):
        """Search Ballotpedia for candidate bio."""
        bio = None
        first_name = member_name.split()[0]
        last_name = member_name.split()[-1]

        try:
            url = f"https://ballotpedia.org/{first_name}_{last_name}"
            await self.page.goto(url, timeout=30000)
            await self.page.wait_for_timeout(2000)

            # Check if we got a disambiguation page
            text = await self.get_page_text()
            if "may refer to" in text.lower() or "did not match" in text.lower():
                # Try with location qualifier
                url = f"https://ballotpedia.org/{first_name}_{last_name}_(California)"
                await self.page.goto(url, timeout=30000)
                await self.page.wait_for_timeout(2000)

            # Try to get content from the main content div only
            content_el = await self.page.query_selector('#mw-content-text .mw-parser-output')
            if not content_el:
                content_el = await self.page.query_selector('#mw-content-text')
            if content_el:
                text = await content_el.inner_text()
            else:
                return None  # No content found

            # Skip if we got a "page does not exist" result
            if "does not have an article" in text.lower():
                return None

            # Very aggressive junk filtering
            junk_markers = [
                'Ballotpedia', 'Media inquiries', 'Data sales', '501(c)3',
                'SITE NAVIGATION', 'Daily Brew', 'ADDITIONAL ANALYSIS',
                'Volunteer', 'Ad Policy', 'Contact us', 'charitable nonprofit',
                'tax deductible', 'provide voters', 'Sign up', 'Terms of Use',
                'Privacy Policy', 'Newsletter', 'Subscribe'
            ]

            # Find the first real paragraph that mentions the person
            paragraphs = text.split('\n')
            bio_paragraphs = []

            for p in paragraphs:
                p = p.strip()
                if len(p) < 80 or len(p) > 1000:
                    continue

                # Skip junk
                if any(marker.lower() in p.lower() for marker in junk_markers):
                    continue

                # Skip very short or list-like content
                if p.startswith('•') or p.startswith('-') or p.startswith('*') or p.startswith('['):
                    continue

                # Must mention the person's name and look like a bio sentence
                if (last_name.lower() in p.lower() and
                    re.search(r'(is|was|has|serves?|elected|born|graduated|worked|career)', p, re.I)):
                    bio_paragraphs.append(p)
                    if len(bio_paragraphs) >= 2:
                        break  # Stop after 2 good paragraphs

            if bio_paragraphs:
                bio = ' '.join(bio_paragraphs)
                bio = re.sub(r'\s+', ' ', bio).strip()
                if len(bio) > 100:
                    bio = bio[:1500]
                    print(f"        Found Ballotpedia bio")
                else:
                    bio = None

        except Exception as e:
            pass

        return bio

    async def scrape(self):
        print(f"\n  Scraping {self.CITY_NAME}")

        # Scrape main council page
        main_result = await self.visit_page(self.COUNCIL_URL, "council_main")
        main_phones = main_result.get("phones", [])
        main_emails = [e for e in main_result.get("emails", [])
                       if self.CITY_DOMAIN.lower() in e.lower()]

        print("    Discovering council members...")
        members = await self.discover_members(main_emails)

        if not members:
            print("    ERROR: No council members found!")
            return self.get_results()

        print(f"    Found {len(members)} members")

        # Enrich each member with external sources (bios, social media, websites)
        print("    Enriching member data from external sources...")
        for i, member in enumerate(members):
            members[i] = await self.enrich_member_data(member)

        # Determine seats up for election based on term_end
        current_year = datetime.now().year
        next_election_year = current_year if current_year % 2 == 0 else current_year + 1
        seats_up = []

        for member in members:
            # Calculate term_start from term_end (4-year terms)
            term_end = member.get("term_end")
            term_start = term_end - 4 if term_end else None

            # Check if seat is up in next election
            if term_end and term_end == next_election_year:
                if member.get("district"):
                    seats_up.append(member["district"])

            self.add_council_member(
                name=member["name"],
                position=member["position"],
                district=member.get("district"),
                email=member.get("email"),
                phone=member.get("phone") or (main_phones[0] if main_phones else None),
                photo_url=member.get("photo_url"),
                bio=member.get("bio"),
                term_start=term_start,
                term_end=term_end,
                website=member.get("website"),
                instagram=member.get("instagram"),
            )

            # Store phone_alt in results for YAML generation
            if member.get("phone_alt"):
                for cm in self.results["council_members"]:
                    if cm["name"] == member["name"]:
                        cm["phone_alt"] = member["phone_alt"]

        # Scrape city-level info
        city_info = await self.scrape_city_info()

        # Add election info to city_info (expected by update_all_data.py)
        elections = await self.scrape_elections()
        elections["seats_up"] = seats_up
        city_info["elections"] = elections

        # Add council structure info
        city_info["council"] = {
            "size": 5,
            "districts": 5,
            "at_large": 0,
            "mayor_elected": False,
            "mayor_rotation": "Selected by council annually"
        }

        self.results["city_info"] = city_info

        return self.get_results()
