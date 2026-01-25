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

    async def visit_page(self, url, page_type="unknown"):
        """Visit a page and log the result"""
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
            response = await self.page.goto(url, timeout=30000, wait_until='domcontentloaded')

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

    def add_council_member(self, name, position, email=None, phone=None, district=None, profile_url=None):
        """Add a council member to results"""
        member = {
            "name": name,
            "position": position,
            "district": district,
            "email": email,
            "phone": phone,
            "city_profile": profile_url
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

        # Also handle middle names (e.g., "Ana Gutierrez" -> "anagutierrez")
        if len(name_parts) > 2:
            # Try first + last without middle
            patterns.insert(0, f"{first_name}{last_name}")

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

    def get_results(self):
        """Return scrape results"""
        # Set final status
        success_pages = [p for p in self.results["pages_visited"] if p["status"] == "success"]
        self.results["status"] = "success" if success_pages else "failed"
        self.results["pages_success"] = len(success_pages)
        self.results["pages_failed"] = len(self.results["pages_visited"]) - len(success_pages)
        return self.results
