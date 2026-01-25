"""
URL Verification Tool for OC City Council websites.

Checks which URLs are accessible and saves snapshots for manual review.

Usage:
    python verify_urls.py           # Check all URLs
    python verify_urls.py --save    # Also save HTML snapshots
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright


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


def verify_urls(save_snapshots=False):
    """Check all city council URLs for accessibility."""
    data = load_master_data()
    cities = data["cities"]

    results = {
        "accessible": [],
        "blocked": [],
        "error": [],
        "redirect": []
    }

    snapshot_dir = Path(__file__).parent / "snapshots"
    if save_snapshots:
        snapshot_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("OC City Council URL Verification")
    print("=" * 60)
    print(f"Checking {len(cities)} cities...")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(15000)

        for i, (city_name, city_info) in enumerate(sorted(cities.items())):
            url = city_info["council_url"]
            print(f"[{i+1:2}/{len(cities)}] {city_name}... ", end="", flush=True)

            try:
                response = page.goto(url, wait_until="domcontentloaded")

                if not response:
                    print("NO RESPONSE")
                    results["error"].append(city_name)
                    city_info["url_status"] = "no_response"
                    continue

                status = response.status
                final_url = page.url

                if status >= 400:
                    print(f"HTTP {status}")
                    results["blocked"].append(city_name)
                    city_info["url_status"] = f"http_{status}"
                elif final_url != url and "login" in final_url.lower():
                    print(f"REDIRECT to login")
                    results["redirect"].append(city_name)
                    city_info["url_status"] = "redirect_login"
                else:
                    print(f"OK ({status})")
                    results["accessible"].append(city_name)
                    city_info["url_status"] = "ok"
                    city_info["url_verified"] = datetime.now().isoformat()

                    if save_snapshots:
                        # Wait for content to load
                        page.wait_for_timeout(2000)

                        # Save screenshot
                        ss_path = snapshot_dir / f"{city_name.replace(' ', '_')}.png"
                        page.screenshot(path=str(ss_path), full_page=True)

                        # Save HTML
                        html_path = snapshot_dir / f"{city_name.replace(' ', '_')}.html"
                        with open(html_path, "w", encoding="utf-8") as f:
                            f.write(page.content())

            except Exception as e:
                error_msg = str(e).split("\n")[0][:50]
                print(f"ERROR: {error_msg}")
                results["error"].append(city_name)
                city_info["url_status"] = "error"
                city_info["url_error"] = str(e)[:200]

        browser.close()

    # Save updated data
    save_master_data(data)

    # Print summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Accessible: {len(results['accessible'])}")
    for city in results["accessible"]:
        print(f"  + {city}")

    print(f"\nBlocked (HTTP error): {len(results['blocked'])}")
    for city in results["blocked"]:
        print(f"  - {city}")

    print(f"\nRedirect: {len(results['redirect'])}")
    for city in results["redirect"]:
        print(f"  ~ {city}")

    print(f"\nError: {len(results['error'])}")
    for city in results["error"]:
        print(f"  ! {city}")

    if save_snapshots:
        print(f"\nSnapshots saved to: {snapshot_dir}")

    # Create a simple report
    report_path = Path(__file__).parent / "url_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Orange County City Council URLs\n\n")
        f.write(f"Verified: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        f.write("## Accessible Sites\n\n")
        f.write("| City | Council URL |\n")
        f.write("|------|-------------|\n")
        for city in sorted(results["accessible"]):
            url = cities[city]["council_url"]
            f.write(f"| {city} | [{url}]({url}) |\n")

        f.write("\n## Blocked/Error Sites\n\n")
        f.write("| City | Issue | URL |\n")
        f.write("|------|-------|-----|\n")
        for city in sorted(results["blocked"] + results["error"]):
            url = cities[city]["council_url"]
            status = cities[city].get("url_status", "unknown")
            f.write(f"| {city} | {status} | {url} |\n")

    print(f"\nReport saved: {report_path}")

    return results


if __name__ == "__main__":
    save_snapshots = "--save" in sys.argv
    verify_urls(save_snapshots)
