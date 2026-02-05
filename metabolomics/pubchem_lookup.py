"""
Look up molecular formulas in PubChem database.
Uses the free PUG REST API: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
"""
import csv
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from collections import defaultdict

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

def get_cids_for_formula(formula: str, max_records: int = 5) -> list:
    """Get PubChem Compound IDs matching a formula."""
    url = f"{PUBCHEM_BASE}/compound/formula/{formula}/cids/JSON?MaxRecords={max_records}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("IdentifierList", {}).get("CID", [])
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []  # No matches
        raise
    except Exception:
        return []

def get_compound_names(cids: list) -> list:
    """Get compound names for a list of CIDs."""
    if not cids:
        return []

    cid_str = ",".join(str(c) for c in cids[:5])  # Limit to 5
    url = f"{PUBCHEM_BASE}/compound/cid/{cid_str}/property/Title,MolecularFormula,MolecularWeight/JSON"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("PropertyTable", {}).get("Properties", [])
    except Exception:
        return []

def main():
    # Load formulas
    formula_path = Path(__file__).parent / "formulas_assigned.csv"
    if not formula_path.exists():
        print("Error: formulas_assigned.csv not found")
        return

    formulas = defaultdict(list)  # formula -> list of (mz, rt) tuples

    with open(formula_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            formula = row["formula"]
            mz = row["exp_mass"]
            rt = row["RT"]
            formulas[formula].append((mz, rt))

    unique_formulas = list(formulas.keys())
    print(f"Found {len(unique_formulas)} unique formulas to look up")
    print(f"(from {sum(len(v) for v in formulas.values())} total assignments)")
    print()

    # Look up each formula
    results = []
    found_count = 0

    for i, formula in enumerate(unique_formulas):
        if (i + 1) % 10 == 0 or i == 0:
            print(f"Processing {i+1}/{len(unique_formulas)}: {formula}")

        cids = get_cids_for_formula(formula)

        if cids:
            compounds = get_compound_names(cids)
            found_count += 1

            for comp in compounds:
                results.append({
                    "formula": formula,
                    "peak_count": len(formulas[formula]),
                    "cid": comp.get("CID", ""),
                    "name": comp.get("Title", ""),
                    "mw": comp.get("MolecularWeight", ""),
                })
        else:
            results.append({
                "formula": formula,
                "peak_count": len(formulas[formula]),
                "cid": "",
                "name": "NOT FOUND IN PUBCHEM",
                "mw": "",
            })

        # Rate limit: PubChem allows 5 requests/second
        time.sleep(0.25)

    # Save results
    output_path = Path(__file__).parent / "pubchem_results.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["formula", "peak_count", "cid", "name", "mw"])
        writer.writeheader()
        writer.writerows(results)

    print()
    print(f"Done! Found matches for {found_count}/{len(unique_formulas)} formulas ({100*found_count/len(unique_formulas):.1f}%)")
    print(f"Results saved to: {output_path}")

    # Show sample results
    print()
    print("=== Sample Results (formulas with most peaks) ===")
    # Sort by peak count
    by_peaks = sorted(results, key=lambda x: -x["peak_count"])
    for r in by_peaks[:15]:
        if r["name"] and r["name"] != "NOT FOUND IN PUBCHEM":
            print(f"  {r['formula']:15} ({r['peak_count']:3} peaks) -> {r['name'][:50]}")

if __name__ == "__main__":
    main()
