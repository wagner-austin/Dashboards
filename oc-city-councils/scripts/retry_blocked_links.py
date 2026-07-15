"""Retry the 403/blocked portal URLs with Firefox + realistic context."""
import asyncio
from playwright.async_api import async_playwright, Error as PWError, TimeoutError as PWTimeout

BLOCKED = [
    ("laguna-beach", "agendas",        "https://www.lagunabeachcity.net/live-here/city-council/meetings-agendas-and-minutes"),
    ("laguna-beach", "live_stream",    "https://www.lagunabeachcity.net/meetings"),
    ("laguna-beach", "ecomment",       "https://www.lagunabeachcity.net/government/departments/city-council/online-comment-form"),
    ("cypress",      "live_stream",    "https://www.cypressca.org/government/watch-cypress-channel-36"),
    ("cypress",      "charter_url",    "https://www.cypressca.org/home/showpublisheddocument/13560/638996819924737488"),
    ("fullerton",    "live_stream",    "https://www.cityoffullerton.com/ftv3"),
    ("fullerton",    "municipal_code", "https://codelibrary.amlegal.com/codes/fullerton/latest/fullerton_ca/0-0-0-1"),
    ("orange",       "live_stream",    "https://www.cityoforange.org/residents/orange-tv3-live"),
]

UA_FX = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
    "Gecko/20100101 Firefox/124.0"
)


async def probe(browser, city, field, url):
    ctx = await browser.new_context(
        user_agent=UA_FX,
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="America/Los_Angeles",
        extra_http_headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Upgrade-Insecure-Requests": "1",
        },
        ignore_https_errors=True,
    )
    page = await ctx.new_page()
    out = {"city": city, "field": field, "status": None, "title": "", "error": ""}
    try:
        resp = await page.goto(url, timeout=30_000, wait_until="domcontentloaded")
        out["status"] = resp.status if resp else None
        try:
            await page.wait_for_load_state("networkidle", timeout=6_000)
        except PWTimeout:
            pass
        out["title"] = (await page.title()) or ""
    except PWTimeout as e:
        out["error"] = f"timeout: {str(e).splitlines()[0][:160]}"
    except PWError as e:
        out["error"] = f"pw: {str(e).splitlines()[0][:160]}"
    finally:
        await ctx.close()
    return out


async def main():
    async with async_playwright() as pw:
        browser = await pw.firefox.launch(headless=True)
        results = await asyncio.gather(*[probe(browser, c, f, u) for c, f, u in BLOCKED])
        await browser.close()

    w = max(len(r["city"]) + len(r["field"]) for r in results) + 2
    print(f"\n{'CITY.FIELD'.ljust(w)}  STATUS  RESULT")
    print("-" * (w + 70))
    cleared, still_blocked = 0, 0
    for r in results:
        key = f"{r['city']}.{r['field']}"
        ok = (not r["error"]) and r["status"] and 200 <= r["status"] < 400
        tag = r["title"] if ok else (r["error"] or f"status {r['status']}")
        flag = "OK  " if ok else "FAIL"
        print(f"{key.ljust(w)}  {str(r['status'] or '-'):<6}  {flag}  {tag[:80]}")
        cleared += 1 if ok else 0
        still_blocked += 0 if ok else 1
    print(f"\nFirefox cleared {cleared}/{len(results)}; {still_blocked} still blocked")


if __name__ == "__main__":
    asyncio.run(main())
