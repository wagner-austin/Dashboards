"""
Download the key ACLU FOIA documents that prove the ICE-Thomson Reuters-Vigilant chain.
"""

import asyncio
from pathlib import Path
import httpx

OUTPUT_DIR = Path(__file__).parent / "data" / "ice_evidence" / "aclu_foia_docs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Key documents from the ACLU blog post
DOCS = [
    # Full FOIA release (1800+ pages)
    ("https://www.aclunorcal.org/docs/DOCS_031319.pdf", "DOCS_031319_full_foia.pdf"),
    # Contract documents
    ("https://www.aclunorcal.org/docs/Pages%20from%20DOCS_031319%20280.pdf", "contract_docs_280.pdf"),
    # ICE has long desired
    ("https://www.aclunorcal.org/docs/Pages%20from%20DOCS_031319-2_684.pdf", "ice_desire_684.pdf"),
    # Rushed contract
    ("https://www.aclunorcal.org/docs/Pages%20from%20DOCS_031319_782.pdf", "rushed_782.pdf"),
    # Contract
    ("https://www.aclunorcal.org/docs/Pages%20from%20DOCS_031319-3%2071.pdf", "contract_71.pdf"),
    # September 2020 contract term
    ("https://www.aclunorcal.org/docs/Pages_from_DOCS_031319_282.pdf", "sept2020_282.pdf"),
    # 150-200 million unique plates per month
    ("https://www.aclunorcal.org/docs/Pages_from_DOCS_031319_339.pdf", "150m_plates_339.pdf"),
    # Most populous 50 metros
    ("https://www.aclunorcal.org/docs/Pages%20from%20DOCS_031319_336.pdf", "populous50_336.pdf"),
    # ICE search capabilities
    ("https://www.aclunorcal.org/docs/Pages%20from%20DOCS_031319_344.pdf", "ice_search_344.pdf"),
    # Step-by-step guide for requesting access
    ("https://www.aclunorcal.org/docs/Pages%20from%20DOCS_031319_101.pdf", "stepbystep_101.pdf"),
    # Internal report - 80 agencies sharing with ICE
    ("https://www.aclunorcal.org/docs/Pages%20from%20DOCS_031319_1822.pdf", "80agencies_1822.pdf"),
    # Released emails
    ("https://www.aclunorcal.org/docs/Pages%20from%20DOCS_031319_Emails.pdf", "emails.pdf"),
    # Privacy rules
    ("https://www.aclunorcal.org/docs/Pages%20from%20DOCS_031319_118.pdf", "privacy_rules_118.pdf"),
    # ICE claim about no access without consent
    ("https://www.aclunorcal.org/docs/Pages%20from%20DOCS_031319_1826.pdf", "ice_claim_1826.pdf"),
    # 9,200 ICE employees with access
    ("https://www.aclunorcal.org/docs/Pages%20from%20DOCS_031319_391.pdf", "9200employees_391.pdf"),
    # Privacy Guidance
    ("https://www.aclunorcal.org/docs/Pages%20from%20DOCS_031319_PrivacyGuidance.pdf", "privacy_guidance.pdf"),
    # Advocacy letters
    ("https://www.aclunorcal.org/docs/ALPRAdvocacyLetters.pdf", "advocacy_letters.pdf"),
]


async def download_doc(client: httpx.AsyncClient, url: str, filename: str):
    """Download a document."""
    filepath = OUTPUT_DIR / filename
    try:
        response = await client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Referer": "https://www.aclunorcal.org/"
        })
        response.raise_for_status()
        filepath.write_bytes(response.content)
        size_mb = len(response.content) / (1024 * 1024)
        print(f"[OK] {filename} ({size_mb:.2f} MB)")
        return True
    except Exception as e:
        print(f"[FAIL] {filename}: {e}")
        return False


async def main():
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Downloading {len(DOCS)} documents...\n")

    async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
        tasks = [download_doc(client, url, filename) for url, filename in DOCS]
        results = await asyncio.gather(*tasks)

    success = sum(results)
    print(f"\nDownloaded {success}/{len(DOCS)} documents")


if __name__ == "__main__":
    asyncio.run(main())
