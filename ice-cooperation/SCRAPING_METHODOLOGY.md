# Sheriff Data Scraping Methodology

This document describes what methods work for each state, for future automation.

## Summary Table

| State | Method | URL/Source | Success Rate | Notes |
|-------|--------|------------|--------------|-------|
| Alabama | WebFetch | https://www.alabamasheriffs.com/sheriffs-directory | 100% | Direct HTML, no JS |
| Arkansas | WebFetch | https://arsheriffs.org/asa-directory/sheriff-directory/ | 100% | Direct HTML |
| Florida | WebFetch | https://flsheriffs.org/sheriffs | 100% | Direct HTML |
| Georgia | Playwright | https://georgiasheriffs.org/sheriffs-by-county/ | 100% | JS-rendered, scroll to load |
| Kansas | Playwright | https://www.kansassheriffs.org/association_directory_view.php | 100% | Full contact info |
| Kentucky | Playwright | https://kaco.org/county-information/county-officials-directory/ | 100% | KACO directory |
| Louisiana | Playwright | https://lsa.org/sheriffs-directory/ | 100% | JS-rendered |
| Mississippi | Playwright | https://www.mssheriff.org/directory | 100% | Full contact info |
| Missouri | API/JSON | https://data.mo.gov/resource/pzip-wwk6.json | 100% | State data portal |
| Oklahoma | Playwright | https://oklahomasheriffs.org/current-ok-sheriffs | 100% | Simple format |
| Pennsylvania | WebSearch | Individual county searches | 84% | Association blocked |
| Tennessee | Playwright | https://www.tnsheriffs.com/sheriff-directory/ | 100% | JS-rendered |
| Texas | WebFetch | https://pbtx.com/texas-sheriff-list/ | 100% | Unofficial but complete |
| Virginia | Playwright | https://vasheriff.org/va-sheriffs-directory/ | 100% | Full info + party |
| West Virginia | Playwright | https://www.wvsheriff.org/?page_id=21 | 100% | Full contact info |

## Method Details

### Method 1: WebFetch (Direct HTML)
**Best for**: Sites with static HTML, no JavaScript rendering
**Tool**: `requests` + BeautifulSoup or WebFetch API
**Example states**: Alabama, Arkansas, Florida, Texas

```python
import requests
from bs4 import BeautifulSoup

response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
# Parse sheriff/county pairs from HTML
```

### Method 2: Playwright with Stealth
**Best for**: JavaScript-rendered sites, sites requiring scrolling
**Tool**: `playwright` + `playwright-stealth`
**Example states**: Georgia, Kansas, Louisiana, Mississippi, Tennessee, Virginia

```python
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await context.new_page()

    stealth = Stealth()
    await stealth.apply_stealth_async(page)

    await page.goto(url, wait_until='networkidle')
    # Scroll to load dynamic content
    for _ in range(10):
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await page.wait_for_timeout(500)
```

### Method 3: State Data Portal API
**Best for**: States with open data portals
**Tool**: Direct JSON API requests
**Example states**: Missouri

```python
import requests

# Missouri uses Socrata API
url = 'https://data.mo.gov/resource/pzip-wwk6.json'
response = requests.get(url)
data = response.json()
# Data is already structured
```

### Method 4: Web Search (Fallback)
**Best for**: States where association websites block automation
**Tool**: WebSearch API for each county
**Example states**: Pennsylvania

Process:
1. For each county, search: `"{County} County {State} sheriff 2025"`
2. Extract sheriff name from search results
3. Validate against known patterns

```
Query: "Allegheny County Pennsylvania sheriff 2025"
Result: Kevin M. Kraus
```

## State-Specific Notes

### Pennsylvania (56/67 = 84%)
- **Problem**: PA Sheriffs Association (pasheriffs.org) returns 403 and serves placeholder image
- **Solution**: Individual web searches for each county
- **Missing counties**: Cameron, Columbia, Forest, Fulton, Greene, Mifflin, Montour, Perry, Snyder, Sullivan, Union, Warren (small counties)
- **Automation**: Can be scripted using search API or Bing scraping

### North Carolina (BLOCKED)
- **Problem**: Interactive map with XHR data loading
- **Potential solutions**:
  1. Intercept XHR requests for JSON data
  2. Use Playwright to click through map
  3. NC Sheriffs Association may have PDF directory

### South Carolina (BLOCKED)
- **Problem**: Interactive map, dynamic loading
- **Potential solutions**:
  1. PDF download available on site
  2. XHR interception
  3. Individual county searches

### Wisconsin (BLOCKED)
- **Problem**: Wix-based site, directory behind paywall
- **Potential solutions**:
  1. Individual county searches
  2. Wisconsin county association
  3. Ballotpedia

## Recommended Automation Pipeline

1. **First pass**: Try WebFetch on association URL
2. **If blocked/JS**: Use Playwright with stealth
3. **If still blocked**: Check for state data portal API
4. **Fallback**: Individual web searches per county
5. **Verification**: Cross-reference with MOA PDFs if available

## Election Cycle Refresh Schedule

Sheriff elections are typically every 4 years. Key election years by state:

| Year | States |
|------|--------|
| 2026 | Alabama, Arkansas, Tennessee, Kentucky |
| 2027 | Louisiana, Mississippi, Virginia |
| 2028 | Florida, Georgia, Kansas, Oklahoma, Texas, West Virginia, Missouri |

**Recommended refresh**: Re-scrape all states in January after election years.
