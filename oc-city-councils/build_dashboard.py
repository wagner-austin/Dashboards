#!/usr/bin/env python3
"""Build dashboard JSON from YAML council data."""
import json
from pathlib import Path
import yaml

def slug_to_name(slug):
    """Convert slug to city name: 'aliso-viejo' -> 'Aliso Viejo'"""
    return ' '.join(word.capitalize() for word in slug.split('-'))

def build_dashboard():
    data_dir = Path(__file__).parent / "_council_data"
    cities = []

    for yaml_file in sorted(data_dir.glob("*.yaml")):
        with open(yaml_file, encoding="utf-8") as f:
            city = yaml.safe_load(f)
            # Generate city_name from slug if missing
            if not city.get("city_name"):
                city["city_name"] = slug_to_name(city.get("city", yaml_file.stem))
            cities.append(city)

    cities.sort(key=lambda c: c.get("city_name", ""))

    output = Path(__file__).parent / "dashboard_data.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(cities, f, indent=2)

    print(f"Built {output} with {len(cities)} cities")

if __name__ == "__main__":
    build_dashboard()
