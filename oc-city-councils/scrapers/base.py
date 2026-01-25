"""
Base scraper class with common functionality for all city scrapers.
"""
import re
from datetime import datetime
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Base class for city council scrapers"""

    CITY_NAME = "Unknown"
    PLATFORM = "unknown"  # civicplus, granicus, wordpress, custom

    def __init__(self, page):
        self.page = page
        self.results = {
            "city": self.CITY_NAME,
            "platform": self.PLATFORM,
            "scrape_time": datetime.now().isoformat(),
            "pages_visited": [],
            "council_members": [],
            "emails_found": [],
            "phones_found": [],
            "errors": [],
            "status": "pending"
        }

    @abstractmethod
    async def scrape(self):
        """Main scrape method - implement in subclass"""
        pass

    @abstractmethod
    def get_urls(self):
        """Return dict of URLs to scrape - implement in subclass"""
        pass

    # === SHARED UTILITIES ===

    def extract_emails(self, text):
        """Extract email addresses from text"""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(pattern, text)
        # Filter junk
        filtered = []
        skip_words = ['noreply', 'webmaster', 'donotreply', 'example.com', 'sentry.io']
        for e in emails:
            if not any(x in e.lower() for x in skip_words):
                filtered.append(e.strip())
        return list(set(filtered))

    def extract_phones(self, text):
        """Extract phone numbers from text"""
        patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?:\s*(?:x|ext\.?)\s*\d+)?',
        ]
        phones = []
        for pattern in patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            phones.extend(found)
        # Clean up
        cleaned = []
        for p in phones:
            p = re.sub(r'[^\d\-()x. ]', '', p).strip()
            if len(re.sub(r'\D', '', p)) >= 10:  # At least 10 digits
                cleaned.append(p)
        return list(set(cleaned))

    async def get_mailto_links(self):
        """Extract emails from mailto: links"""
        emails = []
        try:
            links = await self.page.query_selector_all('a[href^="mailto:"]')
            for link in links:
                href = await link.get_attribute('href')
                if href:
                    email = href.replace('mailto:', '').split('?')[0].strip()
                    if email:
                        emails.append(email)
        except Exception as e:
            self.results["errors"].append(f"mailto extraction: {str(e)}")
        return list(set(emails))

    async def get_page_text(self):
        """Get all text from page body"""
        try:
            return await self.page.inner_text('body')
        except:
            return ""

    async def visit_page(self, url, page_type="unknown", timeout=60000):
        """Visit a page and log the result.

        Args:
            url: URL to visit
            page_type: Type label for logging
            timeout: Page load timeout in ms (default 60000 = 60s)
        """
        result = {
            "url": url,
            "type": page_type,
            "status": "pending",
            "http_code": None,
            "emails": [],
            "phones": [],
            "error": None,
            "timestamp": datetime.now().isoformat()
        }

        try:
            print(f"    Visiting [{page_type}]: {url}")
            response = await self.page.goto(url, timeout=timeout, wait_until='domcontentloaded')

            if response:
                result["http_code"] = response.status
                if response.status >= 400:
                    result["status"] = "http_error"
                    result["error"] = f"HTTP {response.status}"
                    self.results["pages_visited"].append(result)
                    return result

            await self.page.wait_for_timeout(2000)  # Let JS render

            # Extract data
            text = await self.get_page_text()
            result["emails"] = self.extract_emails(text)
            result["phones"] = self.extract_phones(text)

            # Also get mailto links
            mailto_emails = await self.get_mailto_links()
            for e in mailto_emails:
                if e not in result["emails"]:
                    result["emails"].append(e)

            result["status"] = "success"
            print(f"      Found: {len(result['emails'])} emails, {len(result['phones'])} phones")

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)[:200]
            print(f"      ERROR: {str(e)[:100]}")

        self.results["pages_visited"].append(result)

        # Aggregate to main results
        for e in result["emails"]:
            if e not in self.results["emails_found"]:
                self.results["emails_found"].append(e)
        for p in result["phones"]:
            if p not in self.results["phones_found"]:
                self.results["phones_found"].append(p)

        return result

    def add_council_member(self, name, position, email=None, phone=None, district=None,
                           profile_url=None, photo_url=None, bio=None,
                           term_start=None, term_end=None, website=None, instagram=None):
        """Add a council member to results with full standardized schema"""
        member = {
            "name": name,
            "position": position,
            "district": district,
            "email": email,
            "phone": phone,
            "city_profile": profile_url,
            "photo_url": photo_url,
            "bio": bio,
            "term_start": term_start,
            "term_end": term_end,
            "website": website,
            "instagram": instagram,
        }
        self.results["council_members"].append(member)

    def match_email_to_name(self, name, emails, city_domain=None):
        """
        Try to match an email to a person's name.

        Patterns checked:
        - firstlast@domain (e.g., danslater@)
        - first.last@domain (e.g., dan.slater@)
        - flast@domain (e.g., dslater@)
        - firstl@domain (e.g., dans@)
        - last@domain (e.g., slater@)
        - first@domain (e.g., dan@)
        - For 3+ part names:
          - firstmiddlelast (e.g., amyphanwest)
          - first initial + second initial + last (e.g., ccnguyen for Chi Charlie Nguyen)

        Returns the matched email or None.
        """
        if not name or not emails:
            return None

        name_parts = name.lower().strip().split()
        if len(name_parts) < 2:
            return None

        first_name = name_parts[0]
        last_name = name_parts[-1]
        first_initial = first_name[0]
        last_initial = last_name[0]

        # Generate patterns to match (in order of specificity)
        patterns = [
            f"{first_name}{last_name}",      # danslater
            f"{first_name}.{last_name}",     # dan.slater
            f"{first_initial}{last_name}",   # dslater
            f"{first_name}{last_initial}",   # dans
            f"{last_name}",                  # slater
            f"{first_name}",                 # dan
        ]

        # Handle 3+ part names (middle names, compound names)
        if len(name_parts) >= 3:
            middle_name = name_parts[1]
            middle_initial = middle_name[0]

            # Insert more specific compound patterns at the front
            compound_patterns = [
                f"{first_name}{middle_name}{last_name}",  # amyphanwest
                f"{first_initial}{middle_initial}{last_name}",  # ccnguyen (Chi Charlie Nguyen)
                f"{first_initial}{middle_name}{last_name}",  # aphanwest
                f"{first_name}{middle_initial}{last_name}",  # amypwest
            ]
            patterns = compound_patterns + patterns

        for email in emails:
            email_lower = email.lower()
            local_part = email_lower.split('@')[0]

            # If city_domain specified, only match those emails
            if city_domain and city_domain.lower() not in email_lower:
                continue

            # Check each pattern
            for pattern in patterns:
                if pattern == local_part or local_part.startswith(pattern):
                    return email

        return None

    def match_emails_to_members(self, city_domain=None):
        """
        After scraping, try to match collected emails to council members
        who don't have emails yet. Updates self.results["council_members"] in place.
        """
        all_emails = self.results.get("emails_found", [])

        for member in self.results.get("council_members", []):
            if member.get("email"):
                continue  # Already has email

            matched = self.match_email_to_name(
                member.get("name", ""),
                all_emails,
                city_domain
            )

            if matched:
                member["email"] = matched
                print(f"      Matched: {member['name']} -> {matched}")

    async def extract_photo_url(self, member_name, base_url=None):
        """
        Extract council member's photo URL from current page.
        Uses name matching and content area detection.
        """
        try:
            imgs = await self.page.query_selector_all("img")
            name_parts = member_name.lower().split()
            last_name = name_parts[-1] if name_parts else ""

            # Skip patterns for logos/icons
            skip_patterns = ["logo", "icon", "banner", "background", "footer", "header",
                           "facebook", "instagram", "twitter", "youtube", "nextdoor",
                           "search", "menu", "arrow", "button", "seal", "badge"]

            # First pass: match alt/title with last name
            for img in imgs:
                alt = (await img.get_attribute("alt") or "").lower()
                title = (await img.get_attribute("title") or "").lower()
                src = await img.get_attribute("src") or ""

                if any(p in src.lower() for p in skip_patterns):
                    continue

                if last_name and (last_name in alt or last_name in title):
                    if base_url and src.startswith("/"):
                        from urllib.parse import urljoin
                        src = urljoin(base_url, src)
                    return src

            # Second pass: look for portrait/headshot in alt
            for img in imgs:
                alt = (await img.get_attribute("alt") or "").lower()
                title = (await img.get_attribute("title") or "").lower()
                src = await img.get_attribute("src") or ""

                if any(p in src.lower() for p in skip_patterns):
                    continue

                if "portrait" in alt or "portrait" in title or "headshot" in alt:
                    if base_url and src.startswith("/"):
                        from urllib.parse import urljoin
                        src = urljoin(base_url, src)
                    return src

            # Third pass: first content image
            content_selectors = [".fr-view img", "article img", ".widgetContent img", "main img"]
            for selector in content_selectors:
                try:
                    content_imgs = await self.page.query_selector_all(selector)
                    for img in content_imgs:
                        src = await img.get_attribute("src") or ""
                        if any(p in src.lower() for p in skip_patterns):
                            continue
                        if "ImageRepository" in src or "uploads" in src or ".jpg" in src.lower() or ".png" in src.lower():
                            if base_url and src.startswith("/"):
                                from urllib.parse import urljoin
                                src = urljoin(base_url, src)
                            return src
                except:
                    pass

        except Exception as e:
            self.results["errors"].append(f"photo extraction: {str(e)}")

        return None

    async def extract_bio(self):
        """Extract biographical text from current page."""
        try:
            selectors = [".fr-view", "article", ".widgetContent", ".bio", ".biography", "main p"]
            for selector in selectors:
                containers = await self.page.query_selector_all(selector)
                for container in containers:
                    text = await container.inner_text()
                    if text and len(text) > 100:
                        lines = text.strip().split("\n")
                        bio_lines = [l.strip() for l in lines if len(l.strip()) > 50]
                        if bio_lines:
                            return " ".join(bio_lines[:3])
        except Exception as e:
            self.results["errors"].append(f"bio extraction: {str(e)}")
        return None

    async def extract_term_info(self):
        """Extract term start/end dates from current page."""
        try:
            text = await self.page.inner_text("body")
            term_start = None
            term_end = None

            # Elected patterns
            elected_match = re.search(r'elected.*?(\d{4})', text, re.IGNORECASE)
            if elected_match:
                term_start = int(elected_match.group(1))

            # Term end patterns
            expires_match = re.search(r'(?:term expires?|expires?|through|until).*?(\d{4})', text, re.IGNORECASE)
            if expires_match:
                term_end = int(expires_match.group(1))

            # If we found start but not end, estimate 4-year term
            if term_start and not term_end:
                term_end = term_start + 4

            return term_start, term_end
        except:
            return None, None

    async def scrape_member_page(self, member, base_url, city_domain, main_phones=None):
        """
        Scrape a single member's page and return structured data.

        This is the standard method for scraping individual council member pages.
        All city scrapers should use this for consistency.

        Args:
            member: dict with 'name', 'position', 'url', optionally 'district'
            base_url: base URL for the city website (for making absolute URLs)
            city_domain: domain for matching emails (e.g., "cityoforange.org")
            main_phones: fallback phone list from main council page

        Returns:
            dict with standardized member data
        """
        member_url = member.get("url")
        photo_url = None
        bio = None
        term_start = None
        term_end = None
        member_email = None
        member_phone = main_phones[0] if main_phones else None

        if member_url:
            print(f"    Scraping member: {member['name']}")
            result = await self.visit_page(member_url, f"member_{member['name']}")

            if result.get("status") == "success":
                # Extract rich data
                photo_url = await self.extract_photo_url(member["name"], base_url)
                bio = await self.extract_bio()
                term_start, term_end = await self.extract_term_info()

                # Get email from page - use name matching only (no blind fallback)
                if result.get("emails"):
                    member_email = self.match_email_to_name(
                        member["name"],
                        result["emails"],
                        city_domain
                    )

                # Get phone from page
                if result.get("phones"):
                    member_phone = result["phones"][0]

                print(f"      Photo: {'Found' if photo_url else 'Not found'}")
                print(f"      Bio: {len(bio) if bio else 0} chars")
                print(f"      Term: {term_start}-{term_end}")
                print(f"      Email: {member_email or 'Not found'}")

        return {
            "name": member.get("name"),
            "position": member.get("position"),
            "district": member.get("district"),
            "email": member_email,
            "phone": member_phone,
            "profile_url": member_url,
            "photo_url": photo_url,
            "bio": bio,
            "term_start": term_start,
            "term_end": term_end,
        }

    def get_results(self):
        """Return scrape results"""
        # Set final status
        success_pages = [p for p in self.results["pages_visited"] if p["status"] == "success"]
        self.results["status"] = "success" if success_pages else "failed"
        self.results["pages_success"] = len(success_pages)
        self.results["pages_failed"] = len(self.results["pages_visited"]) - len(success_pages)
        return self.results
