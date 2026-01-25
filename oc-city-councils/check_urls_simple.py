"""
Simple URL checker using requests library.

Usage:
    python check_urls_simple.py
"""

import json
from datetime import datetime
from pathlib import Path
import requests


def load_master_data():
    """Load the master JSON file."""
    path = Path(__file__).parent / "oc_cities_master.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_urls():
    """Check all city council URLs using requests."""
    data = load_master_data()
    cities = data["cities"]

    print("=" * 60)
    print("OC City Council URL Check (requests)")
    print("=" * 60)

    results = {"ok": [], "error": []}

    for i, (city_name, city_info) in enumerate(sorted(cities.items())):
        url = city_info["council_url"]
        print(f"[{i+1:2}/{len(cities)}] {city_name}... ", end="", flush=True)

        try:
            response = requests.get(
                url,
                timeout=15,
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )

            status = response.status_code
            final_url = response.url

            if status == 200:
                # Check if we got actual content
                if len(response.text) > 1000:
                    print(f"OK (200, {len(response.text)} bytes)")
                    results["ok"].append({
                        "city": city_name,
                        "url": url,
                        "final_url": final_url,
                        "size": len(response.text)
                    })
                else:
                    print(f"OK but minimal content ({len(response.text)} bytes)")
                    results["error"].append({"city": city_name, "error": "minimal_content"})
            else:
                print(f"HTTP {status}")
                results["error"].append({"city": city_name, "error": f"http_{status}"})

        except requests.exceptions.SSLError as e:
            print(f"SSL Error")
            results["error"].append({"city": city_name, "error": "ssl_error"})
        except requests.exceptions.Timeout:
            print(f"Timeout")
            results["error"].append({"city": city_name, "error": "timeout"})
        except Exception as e:
            print(f"Error: {str(e)[:40]}")
            results["error"].append({"city": city_name, "error": str(e)[:100]})

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Accessible: {len(results['ok'])}")
    for r in results["ok"]:
        print(f"  + {r['city']}: {r['size']} bytes")

    print(f"\nErrors: {len(results['error'])}")
    for r in results["error"]:
        print(f"  - {r['city']}: {r['error']}")

    return results


if __name__ == "__main__":
    check_urls()
