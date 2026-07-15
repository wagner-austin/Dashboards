"""Probe each city's portal URLs with Playwright and report status.

Strategy:
  1. Sweep all URLs with Chromium (fast).
  2. Retry any 403 / non-2xx with Firefox + realistic context (different fingerprint
     defeats most civic-site WAFs — Imperva, F5, Cloudflare).
  3. Treat "Download is starting" as success: the URL serves a valid file (PDF).
"""
import asyncio
import sys
from pathlib import Path

import yaml
from playwright.async_api import async_playwright, Error as PWError, TimeoutError as PWTimeout

DATA_DIR = Path(__file__).resolve().parent.parent / "_council_data"
NAV_TIMEOUT_MS = 30_000
CONCURRENCY = 6
PORTAL_FIELDS = [
    "agendas",
    "live_stream",
    "video_archive",
    "ecomment",
    "youtube",
    "document_center",
    "municipal_code",
    "charter_url",
]

UA_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
UA_FIREFOX = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
    "Gecko/20100101 Firefox/124.0"
)

CTX_KW_FF = {
    "user_agent": UA_FIREFOX,
    "viewport": {"width": 1366, "height": 768},
    "locale": "en-US",
    "timezone_id": "America/Los_Angeles",
    "extra_http_headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Upgrade-Insecure-Requests": "1",
    },
    "ignore_https_errors": True,
}


def _classify(err: str) -> str:
    # Direct file downloads (PDFs, etc.) trigger a navigation error in Playwright
    # even though the link is perfectly valid.
    if "Download is starting" in err:
        return "DOWNLOAD"
    return ""


async def probe(browser, city: str, field: str, url: str, *, engine: str) -> dict:
    if engine == "firefox":
        ctx = await browser.new_context(**CTX_KW_FF)
    else:
        ctx = await browser.new_context(user_agent=UA_CHROME, ignore_https_errors=True)
    page = await ctx.new_page()
    out = {
        "city": city, "field": field, "url": url, "engine": engine,
        "status": None, "title": "", "error": "", "final_url": "", "kind": "",
    }
    try:
        resp = await page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
        out["status"] = resp.status if resp else None
        out["final_url"] = page.url
        try:
            await page.wait_for_load_state("networkidle", timeout=8_000)
        except PWTimeout:
            pass
        out["title"] = (await page.title()) or ""
    except PWTimeout as e:
        out["error"] = f"timeout: {str(e).splitlines()[0][:200]}"
    except PWError as e:
        msg = str(e).splitlines()[0][:200]
        out["error"] = f"pw: {msg}"
        out["kind"] = _classify(msg)
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
    finally:
        await ctx.close()
    return out


def _is_success(r: dict) -> bool:
    if r["kind"] == "DOWNLOAD":
        return True
    if r["error"]:
        return False
    return bool(r["status"]) and 200 <= r["status"] < 400


def _needs_retry(r: dict) -> bool:
    if _is_success(r):
        return False
    # Retry HTTP-level blocks (403/401/406/451) and any error that isn't an outright
    # connection failure. Connection timeouts/refusals won't be fixed by a different engine.
    if r["status"] in (401, 403, 406, 429, 451):
        return True
    if r["error"].startswith("pw: ") and "Download is starting" not in r["error"]:
        # Some Imperva pages serve 403s via Playwright as nav errors w/o a status.
        return "net::ERR_CONNECTION" not in r["error"] and "ERR_NAME_NOT_RESOLVED" not in r["error"]
    return False


async def main() -> int:
    jobs = []
    for path in sorted(DATA_DIR.glob("*.yaml")):
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        portals = data.get("portals") or {}
        for field in PORTAL_FIELDS:
            raw = portals.get(field)
            url = (raw or "").strip() if isinstance(raw, str) else ""
            jobs.append((path.stem, field, url))

    async with async_playwright() as pw:
        chromium = await pw.chromium.launch(headless=True)
        sem = asyncio.Semaphore(CONCURRENCY)

        async def run_chromium(city, field, url):
            if not url:
                return {"city": city, "field": field, "url": "", "engine": "-",
                        "status": None, "title": "", "error": "MISSING",
                        "final_url": "", "kind": ""}
            async with sem:
                return await probe(chromium, city, field, url, engine="chromium")

        results = await asyncio.gather(*[run_chromium(c, f, u) for c, f, u in jobs])
        await chromium.close()

        # Phase 2: retry the ones likely blocked by WAF, with Firefox.
        retry_targets = [(i, r) for i, r in enumerate(results) if _needs_retry(r)]
        if retry_targets:
            print(f"Retrying {len(retry_targets)} blocked URL(s) with Firefox...", file=sys.stderr)
            firefox = await pw.firefox.launch(headless=True)

            async def run_firefox(idx, r):
                async with sem:
                    return idx, await probe(firefox, r["city"], r["field"], r["url"], engine="firefox")

            retried = await asyncio.gather(*[run_firefox(i, r) for i, r in retry_targets])
            for idx, new_r in retried:
                # Only overwrite if the retry did better.
                if _is_success(new_r) or (new_r["status"] and not results[idx]["status"]):
                    results[idx] = new_r
            await firefox.close()

    ok, missing, fail = [], [], []
    for r in results:
        if r["error"] == "MISSING":
            missing.append(r)
        elif _is_success(r):
            ok.append(r)
        else:
            fail.append(r)

    cw = max(len(r["city"]) for r in results)
    fw = max(len(r["field"]) for r in results)
    print(f"\n{'CITY'.ljust(cw)}  {'FIELD'.ljust(fw)}  ENG  STATUS  RESULT")
    print("-" * (cw + fw + 70))
    for r in results:
        if r["error"] == "MISSING":
            tag, status = "(no url)", "-"
        elif r["kind"] == "DOWNLOAD":
            tag, status = "(file download — link valid)", (r["status"] or "dl")
        elif r["error"]:
            tag, status = f"ERR {r['error']}", (r["status"] or "-")
        else:
            tag, status = r["title"], r["status"]
        eng = (r.get("engine") or "-")[:3]
        print(f"{r['city'].ljust(cw)}  {r['field'].ljust(fw)}  {eng:<3}  {str(status):<6}  {tag[:80]}")

    print(f"\nSummary: {len(ok)} ok, {len(missing)} no url set, {len(fail)} failed")
    if fail:
        print("\nFailures (broken links):")
        for r in fail:
            print(f"  - {r['city']}.{r['field']}: status={r['status']} err={r['error']} url={r['url']}")
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
