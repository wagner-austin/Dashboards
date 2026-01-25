# ICE 287(g) Cooperation Dashboard

A dashboard tracking which local law enforcement agencies have formal agreements with ICE under the 287(g) program, and **who signed those agreements**.

## Current Status

### Data Coverage

| Data Type | Coverage | Source |
|-----------|----------|--------|
| 287(g) Agencies | 1,314 agreements | ICE official data (updated weekly) |
| Sheriff Signers | 476/617 (77%) | State Sheriff Associations + Web Search |
| Police Chief Signers | 0/354 | **Need to fetch** |
| Corrections Directors | 0/25 | **Need to fetch** |
| Other Signers | 0/104 | **Need to fetch** |

**Total Signer Coverage: 476/1,100 unique agencies (43%)**

Note: FL (210) and TX (41) unmatched are mostly **police departments** (we have complete sheriff data for those states).

### States With Sheriff Data (18 States, 1,591 Sheriffs)

| State | Sheriffs | URL | Method | Notes |
|-------|----------|-----|--------|-------|
| Alabama | 67 | https://www.alabamasheriffs.com/sheriffs-directory | WebFetch | Direct HTML parse |
| Arkansas | 75 | https://arsheriffs.org/asa-directory/sheriff-directory/ | WebFetch | Direct name/county pairs |
| Florida | 67 | https://flsheriffs.org/sheriffs | WebFetch | Direct HTML parse |
| Georgia | 157 | https://georgiasheriffs.org/sheriffs-by-county/ | Playwright | JS-rendered, scroll to load |
| Kansas | 105 | https://www.kansassheriffs.org/association_directory_view.php?position=members&sort_by=county | Playwright | Full contact info included |
| Louisiana | 64 | https://lsa.org/sheriffs-directory/ | Playwright | JS-rendered, has phone numbers |
| Mississippi | 79 | https://www.mssheriff.org/directory | Playwright | Full contact info included |
| Oklahoma | 76 | https://oklahomasheriffs.org/current-ok-sheriffs | Playwright | Simple name/county format |
| Tennessee | 95 | https://www.tnsheriffs.com/sheriff-directory/ | Playwright | JS-rendered |
| Texas | 254 | https://pbtx.com/texas-sheriff-list/ | WebFetch | Not official, but comprehensive |
| Virginia | 121 | https://vasheriff.org/va-sheriffs-directory/ | Playwright | Full contact info, party affiliation, term dates |
| West Virginia | 55 | https://www.wvsheriff.org/?page_id=21 | Playwright | Full contact info included |
| Kentucky | 120 | https://kaco.org/county-information/county-officials-directory/ | Playwright | KACO directory, full contact info |
| Missouri | 114 | https://data.mo.gov/Public-Safety/County-Sheriff-s-Offices/pzip-wwk6 | API/JSON | State data portal, official |
| North Carolina | 16 | Individual county web searches | WebSearch | Association blocked; compiled via web search |
| Pennsylvania | 56 | Individual county web searches | WebSearch | Association blocked; compiled via web search |
| South Carolina | 9 | Individual county web searches | WebSearch | Association blocked; compiled via web search |
| Wisconsin | 5 | Individual county web searches | WebSearch | Association blocked; compiled via web search |

### Previously Blocked States (Now Resolved)

All four originally blocked states have been cracked using web search methodology:

| State | Coverage | Method | Notes |
|-------|----------|--------|-------|
| Pennsylvania | 56/67 (84%) | Web search per county | PA Sheriffs Association returns 403 |
| North Carolina | 16/100 | Web search per county | NCSA uses JS-rendered map |
| South Carolina | 9/46 | Web search per county | SCSA uses interactive map |
| Wisconsin | 5/72 | Web search per county | WSDSA behind paywall |

**Methodology**: See `SCRAPING_METHODOLOGY.md` for detailed automation documentation.

## Files

| File | Purpose |
|------|---------|
| `generate.py` | Main dashboard generator |
| `fetch_sheriffs.py` | Original sheriff fetch script |
| `fetch_all_signers.py` | Comprehensive signer matching (main script) |
| `scrape_sheriffs_playwright.py` | Playwright scraper for remaining states |
| `extract_signers.py` | (Deprecated) PDF extraction attempt |
| `287g_agencies.xlsx` | Raw ICE data |
| `signer_data.json` | Matched signer information |
| `index.html` | Generated dashboard |

## Methodology

### Why Not PDF Extraction?
We initially tried extracting signer names from the MOA PDFs. This failed because:
1. Names are in **form fields rendered as images**, not extractable text
2. PDF text extraction returns garbled form field labels, not actual names
3. Would require OCR with Tesseract, which isn't reliable for handwritten signatures

### Current Approach: Sheriff Association Directories
State Sheriff Associations maintain public directories of all sheriffs. These are:
- **Authoritative** - official association data
- **Structured** - easy to parse
- **Updated** - sheriffs are elected, associations track changes

**Limitation**: Some association websites use JavaScript rendering, requiring a headless browser to scrape.

### For Police Departments
No central directory exists for police chiefs. Options:
1. Individual agency website scraping
2. State-level police chief associations
3. News articles announcing appointments
4. Manual research

## To Achieve 100% Coverage

### Remaining Work

1. **Blocked states** (6 states, ~176 agencies)
   - PA: Try manual compilation or Ballotpedia
   - NC/SC: Intercept XHR requests or click-through scraping
   - KY: Wait for January update, then scrape
   - WI: Find alternative source
   - MO: Try at different times/with proxies

2. **Police department chiefs** (354 agencies)
   - Search individual agency websites
   - Or use state police chief associations where they exist

3. **Corrections/Other** (129 agencies)
   - Look up individual directors
   - State DOC websites

4. **Automate updates**
   - Schedule weekly scraping of sheriff association sites
   - Track election dates for potential changes

## Data Freshness

- **287(g) data**: Downloaded fresh from ICE each time `generate.py` runs (current as of Jan 2026)
- **Sheriff data**: Scraped from state association websites, Jan 2026
- **Sheriff elections**: Typically every 4 years, varies by state

### Sheriff Election Cycles by State
| State | Term Length | Next Election | Notes |
|-------|-------------|---------------|-------|
| Alabama | 4 years | 2026 | |
| Arkansas | 4 years | 2026 | |
| Florida | 4 years | 2028 | Presidential year |
| Georgia | 4 years | 2028 | Presidential year |
| Kansas | 4 years | 2028 | |
| Louisiana | 4 years | 2027 | Odd year elections |
| Mississippi | 4 years | 2027 | Odd year elections |
| Oklahoma | 4 years | 2028 | |
| Tennessee | 4 years | 2026 | Midterm year |
| Texas | 4 years | 2028 | Presidential year |
| Virginia | 4 years | 2027 | Odd year elections |
| West Virginia | 4 years | 2028 | Presidential year |
| Kentucky | 4 years | 2026 | Midterm year |
| Missouri | 4 years | 2028 | Presidential year |

## Usage

```bash
# Generate dashboard (downloads fresh 287g data)
python generate.py

# Fetch sheriff data and match to agencies
python fetch_all_signers.py

# Scrape remaining states with Playwright
python scrape_sheriffs_playwright.py WEST_VIRGINIA
python scrape_sheriffs_playwright.py  # All configured states
```

## Data Sources

- **287(g) Agreements**: [ICE 287(g) Program](https://www.ice.gov/identify-and-arrest/287g)
- **State Policies**: [ILRC State Map 2024](https://www.ilrc.org/state-map-immigration-enforcement-2024)
- **Sheriff Directories**: State Sheriff Association websites (see table above)

## License

Public domain. Data is from public government sources.
