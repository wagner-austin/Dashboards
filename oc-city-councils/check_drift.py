#!/usr/bin/env python3
"""Check for drift between scraper JSON output and curated YAML data."""
import json
from pathlib import Path
import yaml

def normalize_name(name):
    """Normalize name for comparison."""
    return name.lower().strip().replace("  ", " ")

def check_drift():
    yaml_dir = Path(__file__).parent / "_council_data"
    json_dir = Path(__file__).parent / "cities"

    issues = []

    for yaml_file in sorted(yaml_dir.glob("*.yaml")):
        city_slug = yaml_file.stem
        json_file = json_dir / f"{city_slug}.json"

        if not json_file.exists():
            issues.append(f"{city_slug}: No JSON file found")
            continue

        with open(yaml_file, encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
        with open(json_file, encoding="utf-8") as f:
            json_data = json.load(f)

        yaml_members = yaml_data.get("members", [])
        json_members = json_data.get("council_members", [])

        # Build lookup by normalized name
        yaml_by_name = {normalize_name(m["name"]): m for m in yaml_members}
        json_by_name = {normalize_name(m["name"]): m for m in json_members}

        city_name = yaml_data.get("city_name", city_slug)

        # Check for members in YAML but not JSON
        for name in yaml_by_name:
            if name not in json_by_name:
                issues.append(f"{city_name}: '{name}' in YAML but not in JSON (outdated?)")

        # Check for members in JSON but not YAML
        for name in json_by_name:
            if name not in yaml_by_name:
                issues.append(f"{city_name}: '{name}' in JSON but not in YAML (new member?)")

        # Check key fields for matching members
        for name in yaml_by_name:
            if name not in json_by_name:
                continue

            ym = yaml_by_name[name]
            jm = json_by_name[name]

            # Compare emails
            y_email = (ym.get("email") or "").lower()
            j_email = (jm.get("email") or "").lower()
            if y_email != j_email and y_email and j_email:
                issues.append(f"{city_name}: {name} email differs - YAML: {y_email}, JSON: {j_email}")

            # Compare city_page / city_profile URLs
            y_url = ym.get("city_page", "")
            j_url = jm.get("city_profile", "")
            if y_url and j_url and y_url != j_url:
                issues.append(f"{city_name}: {name} city_page differs:\n    YAML: {y_url}\n    JSON: {j_url}")

            # Compare positions
            y_pos = (ym.get("position") or "").lower()
            j_pos = (jm.get("position") or "").lower()
            if y_pos != j_pos:
                issues.append(f"{city_name}: {name} position differs - YAML: {y_pos}, JSON: {j_pos}")

    if issues:
        print(f"Found {len(issues)} drift issues:\n")
        for issue in issues:
            print(f"  - {issue}\n")
    else:
        print("No drift detected between JSON and YAML")

if __name__ == "__main__":
    check_drift()
