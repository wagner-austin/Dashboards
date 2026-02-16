"""
Parse the downloaded PDFs to extract evidence about ICE-Thomson Reuters-Vigilant relationship.
"""

import json
from pathlib import Path

# pip install pypdf
from pypdf import PdfReader

OUTPUT_DIR = Path(__file__).parent / "data" / "ice_evidence"


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract all text from a PDF."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n\n"
    return text


def search_for_evidence(text: str) -> dict:
    """Search for key evidence in the text."""
    evidence = {
        "mentions_thomson_reuters": False,
        "mentions_west_publishing": False,
        "mentions_vigilant": False,
        "mentions_nvls": False,
        "mentions_clear": False,
        "contract_amounts": [],
        "key_quotes": []
    }

    text_lower = text.lower()

    # Check for key terms
    evidence["mentions_thomson_reuters"] = "thomson reuters" in text_lower
    evidence["mentions_west_publishing"] = "west publishing" in text_lower
    evidence["mentions_vigilant"] = "vigilant" in text_lower
    evidence["mentions_nvls"] = "nvls" in text_lower or "national vehicle location" in text_lower
    evidence["mentions_clear"] = "clear" in text_lower and ("database" in text_lower or "platform" in text_lower)

    # Find key quotes - search line by line
    lines = text.split("\n")
    key_terms = [
        "commercial", "contract", "vendor", "license plate",
        "thomson", "vigilant", "west publishing", "clear",
        "million", "billion", "nvls", "data sharing"
    ]

    for i, line in enumerate(lines):
        line_lower = line.lower()
        for term in key_terms:
            if term in line_lower and len(line.strip()) > 20:
                # Get context (this line and surrounding)
                start = max(0, i - 1)
                end = min(len(lines), i + 2)
                context = " ".join(lines[start:end]).strip()
                if context and len(context) > 30:
                    evidence["key_quotes"].append({
                        "term": term,
                        "quote": context[:500]
                    })
                break

    # Deduplicate quotes
    seen = set()
    unique_quotes = []
    for q in evidence["key_quotes"]:
        if q["quote"] not in seen:
            seen.add(q["quote"])
            unique_quotes.append(q)
    evidence["key_quotes"] = unique_quotes[:50]  # Limit to 50 most relevant

    return evidence


def main():
    results = {}

    # Find all PDFs in the output directory
    pdf_files = list(OUTPUT_DIR.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files")

    for pdf_path in pdf_files:
        print(f"\nParsing: {pdf_path.name}")

        try:
            text = extract_pdf_text(pdf_path)
            print(f"  Extracted {len(text)} characters")

            # Save raw text
            txt_path = pdf_path.with_suffix(".txt")
            txt_path.write_text(text, encoding="utf-8")
            print(f"  Saved text to: {txt_path.name}")

            # Search for evidence
            evidence = search_for_evidence(text)
            results[pdf_path.name] = evidence

            print(f"  Thomson Reuters: {evidence['mentions_thomson_reuters']}")
            print(f"  West Publishing: {evidence['mentions_west_publishing']}")
            print(f"  Vigilant: {evidence['mentions_vigilant']}")
            print(f"  NVLS: {evidence['mentions_nvls']}")
            print(f"  CLEAR: {evidence['mentions_clear']}")
            print(f"  Key quotes found: {len(evidence['key_quotes'])}")

        except Exception as e:
            print(f"  Error: {e}")
            results[pdf_path.name] = {"error": str(e)}

    # Save analysis results
    analysis_file = OUTPUT_DIR / "pdf_analysis.json"
    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Analysis saved to: {analysis_file}")
    print(f"{'='*60}")

    # Print summary
    print("\n\nSUMMARY OF EVIDENCE FOUND:")
    print("="*60)
    for pdf_name, evidence in results.items():
        if isinstance(evidence, dict) and "error" not in evidence:
            print(f"\n{pdf_name}:")
            if evidence["mentions_thomson_reuters"]:
                print("  [✓] Mentions Thomson Reuters")
            if evidence["mentions_west_publishing"]:
                print("  [✓] Mentions West Publishing")
            if evidence["mentions_vigilant"]:
                print("  [✓] Mentions Vigilant")
            if evidence["mentions_nvls"]:
                print("  [✓] Mentions NVLS")
            if evidence["mentions_clear"]:
                print("  [✓] Mentions CLEAR database")

    return results


if __name__ == "__main__":
    main()
