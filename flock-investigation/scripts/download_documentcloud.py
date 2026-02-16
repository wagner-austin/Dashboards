"""
Download DocumentCloud documents that prove ICE-Thomson Reuters-Vigilant chain.
"""

import asyncio
from pathlib import Path
import httpx

OUTPUT_DIR = Path(__file__).parent / "data" / "ice_evidence" / "documentcloud"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DOCS = [
    # Privacy International letter to Thomson Reuters
    ("https://s3.documentcloud.org/documents/4546858/PI-Letter-TR-21-06.pdf",
     "privacy_international_thomson_reuters_letter.pdf"),
    # Vigilant LEARN user guide
    ("https://s3.documentcloud.org/documents/20389371/vigilant-solutions-alpr-learn-51-system-user-guide.pdf",
     "vigilant_learn_user_guide.pdf"),
]


async def download_doc(client: httpx.AsyncClient, url: str, filename: str):
    """Download a document."""
    filepath = OUTPUT_DIR / filename
    try:
        response = await client.get(url)
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
