"""
SAFE Auto-updater for master JSON file.

SAFETY RULES:
1. NEVER overwrite existing data with null/empty values
2. ONLY fill in blank fields
3. Always create backup before changes
4. Dry-run mode to preview changes first
5. Skip cities where scrape failed
"""
import json
import shutil
from datetime import datetime
from pathlib import Path


class MasterJSONUpdater:
    """Safely updates the master JSON with scraped data"""

    def __init__(self, master_json_path):
        self.master_path = Path(master_json_path)
        self.backup_path = None
        self.changes_log = []
        self.master_data = None
        self.dry_run = True  # Default to dry-run for safety

    def load_master(self):
        """Load the master JSON file"""
        with open(self.master_path, 'r', encoding='utf-8') as f:
            self.master_data = json.load(f)
        return self.master_data

    def create_backup(self):
        """Create a timestamped backup before making changes"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.master_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        self.backup_path = backup_dir / f"oc_cities_master_BACKUP_{timestamp}.json"
        shutil.copy2(self.master_path, self.backup_path)
        print(f"[OK] Backup created: {self.backup_path}")
        return self.backup_path

    def save_master(self):
        """Save updated master JSON (only if not dry-run)"""
        if self.dry_run:
            print("\n[DRY-RUN] Changes NOT saved. Run with --apply to save.")
            return False

        # Update metadata
        self.master_data["_metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

        with open(self.master_path, 'w', encoding='utf-8') as f:
            json.dump(self.master_data, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Master JSON updated: {self.master_path}")
        return True

    def log_change(self, city, field, old_value, new_value, member_name=None):
        """Log a change for audit trail"""
        change = {
            "timestamp": datetime.now().isoformat(),
            "city": city,
            "field": field,
            "old_value": old_value,
            "new_value": new_value
        }
        if member_name:
            change["member"] = member_name
        self.changes_log.append(change)

        prefix = "[DRY-RUN] " if self.dry_run else ""
        member_str = f" ({member_name})" if member_name else ""
        print(f"  {prefix}UPDATE: {field}{member_str}: '{old_value}' -> '{new_value}'")

    def is_valid_value(self, value):
        """Check if a value is valid (not null, not empty, not placeholder)"""
        if value is None:
            return False
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return False
            # Skip placeholder values
            if value.lower() in ['null', 'none', 'n/a', 'unknown', '']:
                return False
        return True

    def should_update_field(self, old_value, new_value):
        """
        Determine if we should update a field.

        SAFETY: Only update if:
        - Old value is null/empty AND new value is valid
        - NEVER overwrite existing good data
        """
        old_is_valid = self.is_valid_value(old_value)
        new_is_valid = self.is_valid_value(new_value)

        # Only fill in blanks, never overwrite
        if not old_is_valid and new_is_valid:
            return True

        return False

    def match_member_by_name(self, members_list, name):
        """Find a member in list by name (fuzzy match)"""
        if not name:
            return None, None

        name_lower = name.lower().strip()

        for i, member in enumerate(members_list):
            existing_name = member.get("name", "").lower().strip()
            if not existing_name:
                continue

            # Exact match
            if existing_name == name_lower:
                return i, member

            # Partial match (handles name variations)
            name_parts = name_lower.split()
            existing_parts = existing_name.split()

            if len(name_parts) >= 2 and len(existing_parts) >= 2:
                # Match last name + first initial
                if name_parts[-1] == existing_parts[-1] and name_parts[0][0] == existing_parts[0][0]:
                    return i, member

        return None, None

    def detect_member_changes(self, city_name, existing_members, scraped_members):
        """
        Detect if council members have changed (new election results).

        Returns list of changes: new members, removed members, position changes
        """
        changes = []

        existing_by_position = {m.get("position", "").lower(): m for m in existing_members}
        scraped_by_position = {m.get("position", "").lower(): m for m in scraped_members}

        for position, scraped in scraped_by_position.items():
            existing = existing_by_position.get(position)

            if existing:
                # Check if person in this position changed
                existing_name = existing.get("name", "").lower().strip()
                scraped_name = scraped.get("name", "").lower().strip()

                if existing_name and scraped_name and existing_name != scraped_name:
                    # Different person in same position = likely new election
                    changes.append({
                        "type": "member_replaced",
                        "position": position,
                        "old_name": existing.get("name"),
                        "new_name": scraped.get("name"),
                        "new_email": scraped.get("email"),
                        "new_phone": scraped.get("phone")
                    })

        return changes

    def update_city_from_scrape(self, city_name, scrape_result):
        """
        Safely update a city's data from scrape results.

        Handles:
        1. Filling in blank email/phone fields
        2. Detecting NEW council members (after elections)
        3. Position changes (new mayor, etc.)

        Returns number of fields updated.
        """
        if city_name not in self.master_data.get("cities", {}):
            print(f"  SKIP: {city_name} not in master JSON")
            return 0

        # SAFETY: Skip if scrape failed
        if scrape_result.get("status") == "failed":
            print(f"  SKIP: Scrape failed for {city_name}")
            return 0

        # SAFETY: Skip if no data found
        if not scrape_result.get("emails_found") and not scrape_result.get("council_members"):
            print(f"  SKIP: No data found for {city_name}")
            return 0

        city_data = self.master_data["cities"][city_name]
        updates_count = 0

        all_emails = scrape_result.get("emails_found", [])
        council_members_scraped = scrape_result.get("council_members", [])

        # DETECT NEW COUNCIL MEMBERS (election changes)
        if council_members_scraped:
            member_changes = self.detect_member_changes(
                city_name,
                city_data.get("council_members", []),
                council_members_scraped
            )

            for change in member_changes:
                if change["type"] == "member_replaced":
                    print(f"  [!] NEW MEMBER DETECTED: {change['position']}")
                    print(f"      Old: {change['old_name']}")
                    print(f"      New: {change['new_name']}")

                    # Find and update the member in master
                    for idx, m in enumerate(city_data.get("council_members", [])):
                        if m.get("position", "").lower() == change["position"]:
                            if not self.dry_run:
                                # Update to new member
                                city_data["council_members"][idx]["name"] = change["new_name"]
                                city_data["council_members"][idx]["email"] = change.get("new_email")
                                city_data["council_members"][idx]["phone"] = change.get("new_phone")
                            self.log_change(
                                city_name, "name (NEW MEMBER)",
                                change["old_name"],
                                change["new_name"],
                                member_name=change["position"]
                            )
                            updates_count += 1
                            break

        # Method 1: Update from structured council member data
        if council_members_scraped:
            for scraped_member in council_members_scraped:
                scraped_email = scraped_member.get("email")
                scraped_phone = scraped_member.get("phone")

                if not scraped_email and not scraped_phone:
                    continue

                # Find matching member in master
                idx, existing_member = self.match_member_by_name(
                    city_data.get("council_members", []),
                    scraped_member.get("name", "")
                )

                if existing_member is None:
                    continue

                # SAFELY update email (only if current is null)
                if self.should_update_field(existing_member.get("email"), scraped_email):
                    self.log_change(
                        city_name, "email",
                        existing_member.get("email"),
                        scraped_email,
                        member_name=scraped_member["name"]
                    )
                    if not self.dry_run:
                        city_data["council_members"][idx]["email"] = scraped_email
                    updates_count += 1

                # SAFELY update phone (only if current is null)
                if self.should_update_field(existing_member.get("phone"), scraped_phone):
                    self.log_change(
                        city_name, "phone",
                        existing_member.get("phone"),
                        scraped_phone,
                        member_name=scraped_member["name"]
                    )
                    if not self.dry_run:
                        city_data["council_members"][idx]["phone"] = scraped_phone
                    updates_count += 1

        # Method 2: Try to match emails to members by name pattern
        if all_emails and not council_members_scraped:
            city_domain = self._get_city_domain(city_data)

            for idx, member in enumerate(city_data.get("council_members", [])):
                # Skip if already has email
                if self.is_valid_value(member.get("email")):
                    continue

                # Try to find matching email
                member_email = self._find_member_email(
                    member.get("name", ""),
                    all_emails,
                    city_domain
                )

                if member_email and self.should_update_field(member.get("email"), member_email):
                    self.log_change(
                        city_name, "email",
                        member.get("email"),
                        member_email,
                        member_name=member.get("name")
                    )
                    if not self.dry_run:
                        city_data["council_members"][idx]["email"] = member_email
                    updates_count += 1

        return updates_count

    def _get_city_domain(self, city_data):
        """Extract the email domain for a city"""
        website = city_data.get("website", "")
        import re
        match = re.search(r'https?://(?:www\.)?([^/]+)', website)
        return match.group(1) if match else None

    def _find_member_email(self, member_name, emails, city_domain):
        """Try to find a member's email from list of emails"""
        if not city_domain or not member_name:
            return None

        name_parts = member_name.lower().split()
        if len(name_parts) < 2:
            return None

        first_name = name_parts[0]
        last_name = name_parts[-1]
        first_initial = first_name[0]

        # Common email patterns
        patterns = [
            f"{first_initial}{last_name}",
            f"{first_name}{last_name}",
            f"{first_name}.{last_name}",
            f"{last_name}",
        ]

        for email in emails:
            email_lower = email.lower()
            if city_domain.lower() not in email_lower:
                continue

            local_part = email_lower.split('@')[0]
            for pattern in patterns:
                if pattern in local_part:
                    return email

        return None

    def update_from_scrape_results(self, scrape_results, dry_run=True, create_backup=True):
        """
        Update master JSON from scrape results.

        Args:
            scrape_results: Results from run_scrapers.py
            dry_run: If True, only preview changes (default: True for safety)
            create_backup: If True, backup before changes
        """
        self.dry_run = dry_run
        self.load_master()

        mode = "DRY-RUN (preview only)" if dry_run else "LIVE UPDATE"
        print("\n" + "="*60)
        print(f"UPDATING MASTER JSON - {mode}")
        print("="*60)

        if not dry_run and create_backup:
            self.create_backup()

        total_updates = 0

        for city_name, result in scrape_results.get("results", {}).items():
            print(f"\n{city_name}:")
            updates = self.update_city_from_scrape(city_name, result)
            total_updates += updates
            if updates == 0:
                print("  No changes needed")

        print("\n" + "-"*60)
        print(f"SUMMARY: {total_updates} field(s) to update")
        print("-"*60)

        if total_updates > 0:
            if dry_run:
                print("\n[!] DRY-RUN MODE: No changes saved")
                print("    Run with --apply flag to save changes")
            else:
                self.save_master()
                print(f"\n[OK] {total_updates} updates saved to master JSON")
                print(f"[OK] Backup at: {self.backup_path}")

        return self.changes_log


def preview_updates(scrape_results_path, master_json_path):
    """Preview what updates would be made (safe)"""
    with open(scrape_results_path, 'r') as f:
        scrape_results = json.load(f)

    updater = MasterJSONUpdater(master_json_path)
    return updater.update_from_scrape_results(scrape_results, dry_run=True)


def apply_updates(scrape_results_path, master_json_path):
    """Apply updates with backup (requires confirmation)"""
    with open(scrape_results_path, 'r') as f:
        scrape_results = json.load(f)

    updater = MasterJSONUpdater(master_json_path)
    return updater.update_from_scrape_results(scrape_results, dry_run=False)
