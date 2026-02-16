"""
Scrape primary evidence for ICE -> Thomson Reuters -> Vigilant data chain.
Uses Playwright with Firefox to get actual documents.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import httpx

OUTPUT_DIR = Path(__file__).parent / "data" / "ice_evidence"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def download_pdf(url: str, filename: str) -> Path:
    """Download a PDF file directly."""
    filepath = OUTPUT_DIR / filename
    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        filepath.write_bytes(response.content)
        print(f"Downloaded: {filepath}")
    return filepath


async def scrape_usaspending_contracts(page):
    """Scrape Thomson Reuters contracts from USAspending.gov"""

    contracts = []

    # Thomson Reuters Special Services - all contracts
    url = "https://www.usaspending.gov/recipient/65494435-f70c-9a3e-15e0-474723c82d88-C/latest"
    print(f"\nFetching: {url}")
    await page.goto(url, wait_until="networkidle", timeout=60000)
    await page.wait_for_timeout(3000)

    # Save screenshot
    await page.screenshot(path=str(OUTPUT_DIR / "thomson_reuters_contracts.png"), full_page=True)

    # Get page content
    content = await page.content()
    with open(OUTPUT_DIR / "thomson_reuters_contracts.html", "w", encoding="utf-8") as f:
        f.write(content)

    # Get all text content for analysis
    body_text = await page.inner_text("body")
    contracts.append({"type": "full_text", "url": url, "text": body_text[:50000]})

    # Now search for ICE-specific contracts
    ice_search_url = "https://www.usaspending.gov/search/?hash=eyJmaWx0ZXJzIjp7InJlY2lwaWVudFNlYXJjaCI6WyJ0aG9tc29uIHJldXRlcnMiXSwiYWdlbmNpZXMiOlt7ImlkIjo2NzQsInRpZXIiOiJzdWJ0aWVyIiwidHlwZSI6ImZ1bmRpbmciLCJuYW1lIjoiSW1taWdyYXRpb24gYW5kIEN1c3RvbXMgRW5mb3JjZW1lbnQifV19fQ%3D%3D"
    print(f"\nFetching ICE contracts: {ice_search_url}")

    await page.goto(ice_search_url, wait_until="networkidle", timeout=60000)
    await page.wait_for_timeout(5000)

    await page.screenshot(path=str(OUTPUT_DIR / "ice_thomson_reuters_search.png"), full_page=True)

    ice_content = await page.content()
    with open(OUTPUT_DIR / "ice_thomson_reuters_search.html", "w", encoding="utf-8") as f:
        f.write(ice_content)

    ice_text = await page.inner_text("body")
    contracts.append({"type": "ice_search_results", "url": ice_search_url, "text": ice_text[:50000]})

    return contracts


async def scrape_aclu_foia_docs(page):
    """Get ACLU FOIA case documents"""

    docs = []

    # ACLU case page
    url = "https://www.aclunorcal.org/our-work/legal-docket/aclu-northern-california-v-ice-license-plate-readers"
    print(f"\nFetching ACLU case: {url}")

    await page.goto(url, wait_until="networkidle", timeout=60000)
    await page.wait_for_timeout(2000)

    await page.screenshot(path=str(OUTPUT_DIR / "aclu_case_page.png"), full_page=True)

    content = await page.content()
    with open(OUTPUT_DIR / "aclu_case_page.html", "w", encoding="utf-8") as f:
        f.write(content)

    # Find all PDF links
    pdf_links = await page.query_selector_all("a[href$='.pdf']")
    for link in pdf_links:
        href = await link.get_attribute("href")
        text = await link.inner_text()
        docs.append({"text": text, "url": href})
        print(f"Found PDF: {text} -> {href}")

    # Also get all links that might be documents
    all_links = await page.query_selector_all("a")
    for link in all_links:
        href = await link.get_attribute("href")
        text = await link.inner_text()
        if href and ("document" in href.lower() or "foia" in href.lower() or ".pdf" in href.lower()):
            if {"text": text, "url": href} not in docs:
                docs.append({"text": text, "url": href})

    # Get full page text
    body_text = await page.inner_text("body")
    docs.append({"type": "page_content", "text": body_text})

    return docs


async def scrape_afsc_investigate(page):
    """Get AFSC Investigate data on Thomson Reuters contracts"""

    url = "https://investigate.afsc.org/company/thomson-reuters"
    print(f"\nFetching AFSC data: {url}")

    await page.goto(url, wait_until="networkidle", timeout=60000)
    await page.wait_for_timeout(3000)

    await page.screenshot(path=str(OUTPUT_DIR / "afsc_thomson_reuters.png"), full_page=True)

    content = await page.content()
    with open(OUTPUT_DIR / "afsc_thomson_reuters.html", "w", encoding="utf-8") as f:
        f.write(content)

    # Get full text
    body_text = await page.inner_text("body")

    return {"url": url, "text": body_text}


async def scrape_dhs_pia(page):
    """Get DHS Privacy Impact Assessment for ICE LPR"""

    # Main PIA page
    url = "https://www.dhs.gov/publication/dhs-ice-pia-039-acquisition-and-use-license-plate-reader-data-commercial-service"
    print(f"\nFetching DHS PIA page: {url}")

    await page.goto(url, wait_until="networkidle", timeout=60000)
    await page.wait_for_timeout(2000)

    await page.screenshot(path=str(OUTPUT_DIR / "dhs_pia_039_page.png"), full_page=True)

    content = await page.content()
    with open(OUTPUT_DIR / "dhs_pia_039_page.html", "w", encoding="utf-8") as f:
        f.write(content)

    # Find PDF links
    pdf_links = []
    links = await page.query_selector_all("a[href$='.pdf']")
    for link in links:
        href = await link.get_attribute("href")
        text = await link.inner_text()
        pdf_links.append({"text": text, "url": href})
        print(f"Found DHS PDF: {text} -> {href}")

    body_text = await page.inner_text("body")

    return {"url": url, "text": body_text, "pdfs": pdf_links}


async def download_key_pdfs():
    """Download the key PDF documents directly"""

    pdfs_to_download = [
        # DHS Privacy Impact Assessment
        ("https://www.dhs.gov/sites/default/files/publications/privacy-pia-ice-lpr-january2018.pdf",
         "dhs_pia_039_jan2018.pdf"),
        ("https://www.dhs.gov/sites/default/files/publications/privacy-pia30b-ice-acquisitionanduseoflprdatafromacommercialservice-june2021_0.pdf",
         "dhs_pia_039_june2021.pdf"),
        # Georgetown Law analysis
        ("https://www.law.georgetown.edu/immigration-law-journal/wp-content/uploads/sites/19/2020/11/U.S.-Immigration-and-Customs-Enforcement-Use-of-Automated-License-Plate-Reader-Databases.pdf",
         "georgetown_ice_alpr_analysis.pdf"),
        # ILRC/ACLU organizer guide
        ("https://www.ilrc.org/sites/default/files/resources/ilrc_aclu_alpr_for_organizers.pdf",
         "ilrc_aclu_alpr_organizers.pdf"),
    ]

    downloaded = []
    for url, filename in pdfs_to_download:
        try:
            path = await download_pdf(url, filename)
            downloaded.append({"url": url, "path": str(path), "status": "success"})
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            downloaded.append({"url": url, "error": str(e), "status": "failed"})

    return downloaded


async def main():
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Started: {datetime.now().isoformat()}")

    results = {
        "timestamp": datetime.now().isoformat(),
        "output_dir": str(OUTPUT_DIR),
        "sources": {}
    }

    # Download PDFs first (doesn't need browser)
    print("\n" + "="*60)
    print("DOWNLOADING KEY PDFs")
    print("="*60)
    results["sources"]["pdfs"] = await download_key_pdfs()

    # Browser scraping
    async with async_playwright() as p:
        print("\n" + "="*60)
        print("LAUNCHING FIREFOX")
        print("="*60)

        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        )
        page = await context.new_page()

        # Apply stealth
        stealth_config = Stealth()
        await stealth_config.apply_stealth_async(page)

        # Scrape each source
        print("\n" + "="*60)
        print("SCRAPING USAspending.gov")
        print("="*60)
        try:
            results["sources"]["usaspending"] = await scrape_usaspending_contracts(page)
        except Exception as e:
            print(f"Error: {e}")
            results["sources"]["usaspending"] = {"error": str(e)}

        print("\n" + "="*60)
        print("SCRAPING ACLU FOIA CASE")
        print("="*60)
        try:
            results["sources"]["aclu_foia"] = await scrape_aclu_foia_docs(page)
        except Exception as e:
            print(f"Error: {e}")
            results["sources"]["aclu_foia"] = {"error": str(e)}

        print("\n" + "="*60)
        print("SCRAPING AFSC INVESTIGATE")
        print("="*60)
        try:
            results["sources"]["afsc"] = await scrape_afsc_investigate(page)
        except Exception as e:
            print(f"Error: {e}")
            results["sources"]["afsc"] = {"error": str(e)}

        print("\n" + "="*60)
        print("SCRAPING DHS PIA PAGE")
        print("="*60)
        try:
            results["sources"]["dhs_pia"] = await scrape_dhs_pia(page)
        except Exception as e:
            print(f"Error: {e}")
            results["sources"]["dhs_pia"] = {"error": str(e)}

        await browser.close()

    # Save results
    results_file = OUTPUT_DIR / "scrape_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print("\n" + "="*60)
    print(f"DONE - Results saved to {results_file}")
    print("="*60)

    return results


if __name__ == "__main__":
    asyncio.run(main())
