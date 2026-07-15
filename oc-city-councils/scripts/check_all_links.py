"""Sweep every dashboard URL across all 34 cities and flag broken/collapsed links.

Two-phase probe:
  1. Fast curl HEAD with a Firefox UA (~30s for 34 cities × ~20 URLs).
  2. For anything that failed with a WAF-like signal, re-probe with Playwright + Firefox
     — real browser fingerprint defeats Imperva/F5/Cloudflare.

Reports four buckets:
  - COLLAPSED     : source had a real path but final URL is just "/" — the deep page
                    is gone. Classic site-redomain / redesign signal (Irvine, June 2026).
  - TRULY BROKEN  : both phases failed AND the domain returned an HTTP status somewhere
                    (so the server is talking to us — a specific page is genuinely dead).
  - UNVERIFIABLE  : whole domain refused every probe at the network layer (no HTTP status
                    for anything), typically an aggressive WAF geo/IP-blocking cloud egress.
                    Real users on residential IPs likely see these load fine — verify manually.
  - WAF-ONLY      : curl blocked but Playwright succeeded. Link works for real users;
                    reported as summary count only.

Covers every URL the dashboard renders: website, council_url, portals.*, broadcast.live_stream,
members[].{city_page,photo_url,website}. Distinct from check_agenda_links.py, which only
probes the portals section.
"""
import asyncio
import concurrent.futures
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

import yaml
from playwright.async_api import async_playwright, Error as PWError, TimeoutError as PWTimeout

DATA_DIR = Path(__file__).resolve().parent.parent / "_council_data"
UA_FX = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
CURL_WORKERS = 20
PW_CONCURRENCY = 8
CURL_TIMEOUT = 20
PW_TIMEOUT_MS = 25_000

CTX_KW_FX = {
    "user_agent": UA_FX,
    "viewport": {"width": 1366, "height": 768},
    "locale": "en-US",
    "timezone_id": "America/Los_Angeles",
    "extra_http_headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Upgrade-Insecure-Requests": "1",
    },
    "ignore_https_errors": True,
}


def extract_urls(city, data):
    for key in ("website", "council_url"):
        v = data.get(key)
        if isinstance(v, str) and v.strip():
            yield city, key, v.strip()
    for k, v in (data.get("portals") or {}).items():
        if isinstance(v, str) and v.strip():
            yield city, f"portals.{k}", v.strip()
    ls = (data.get("broadcast") or {}).get("live_stream")
    if isinstance(ls, str) and ls.strip():
        yield city, "broadcast.live_stream", ls.strip()
    for i, mem in enumerate(data.get("members") or []):
        tag = (mem.get("name") or f"m{i}").split()[0]
        for key in ("city_page", "photo_url", "website"):
            v = mem.get(key)
            if isinstance(v, str) and v.strip():
                yield city, f"members[{tag}].{key}", v.strip()


def _urlpath(u: str) -> str:
    p = (urlparse(u).path or "/").rstrip("/")
    return p or "/"


def _collapsed(src: str, final: str) -> bool:
    return _urlpath(src) != "/" and _urlpath(final) == "/"


IMAGE_EXT_RE = re.compile(r"\.(jpe?g|png|gif|webp|svg|bmp|tiff?)$", re.I)


def _looks_like_image(field: str, url: str) -> bool:
    if "photo_url" in field:
        return True
    path = urlparse(url).path
    if IMAGE_EXT_RE.search(path):
        return True
    if "/showpublishedimage/" in path.lower():
        return True
    return False


def _encode_spaces(url: str) -> str:
    """Percent-encode spaces in the path segment. Preserves internal double-spaces
    (e.g. Buena Park's "Lamiya Hoque  Cropped.jpg" — the file on the server really
    does have two spaces; collapsing would 404).

    Browsers auto-encode literal spaces in <img src>/<a href> URLs but curl and Playwright
    do not — this normalizes the same way. Real fix: URL-encode the value in the YAML.
    """
    cleaned = url.strip()
    if " " not in cleaned:
        return cleaned
    parts = urlparse(cleaned)
    return urlunparse(parts._replace(path=quote(parts.path, safe="/%")))


def curl_probe(city, field, url):
    original = url.strip()
    cleaned = _encode_spaces(original)
    space_encoded = cleaned != original
    try:
        r = subprocess.run(
            ["curl", "-sI", "-L", "--max-time", str(CURL_TIMEOUT),
             "-A", UA_FX, "-o", "/dev/null",
             "-w", "%{http_code} %{url_effective}",
             cleaned],
            capture_output=True, text=True, timeout=CURL_TIMEOUT + 5,
        )
        code_str, _, final = r.stdout.strip().partition(" ")
        code = int(code_str) if code_str.isdigit() else 0
        error = "" if code else (r.stderr.strip().splitlines()[-1][:120] if r.stderr else "no response")
    except subprocess.TimeoutExpired:
        return dict(city=city, field=field, url=cleaned, original_url=original, space_encoded=space_encoded, status=0, final="", error="timeout")
    except Exception as e:
        return dict(city=city, field=field, url=cleaned, original_url=original, space_encoded=space_encoded, status=0, final="", error=f"{type(e).__name__}"[:120])
    return dict(city=city, field=field, url=cleaned, original_url=original, space_encoded=space_encoded, status=code, final=final, error=error)


async def pw_probe(browser, city, field, url):
    ctx = await browser.new_context(**CTX_KW_FX)
    out = dict(city=city, field=field, url=url, status=None, final=url, error="")
    try:
        if _looks_like_image(field, url):
            # context.request uses the browser network stack (real headers/fingerprint) but
            # doesn't try to render — avoids the DOMContentLoaded-never-fires timeout on images.
            resp = await ctx.request.get(
                url,
                timeout=PW_TIMEOUT_MS,
                headers={
                    "Accept": "image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5",
                    "Sec-Fetch-Dest": "image",
                    "Sec-Fetch-Mode": "no-cors",
                    "Sec-Fetch-Site": "same-origin",
                },
            )
            out["status"] = resp.status
            out["final"] = resp.url
        else:
            page = await ctx.new_page()
            resp = await page.goto(url, timeout=PW_TIMEOUT_MS, wait_until="domcontentloaded")
            out["status"] = resp.status if resp else None
            out["final"] = page.url
    except PWTimeout as e:
        out["error"] = f"timeout: {str(e).splitlines()[0][:120]}"
    except PWError as e:
        msg = str(e).splitlines()[0][:160]
        if "Download is starting" in msg:
            out["status"] = 200  # Direct file download — link is valid
        else:
            out["error"] = f"pw: {msg}"
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {str(e)[:120]}"
    finally:
        await ctx.close()
    return out


async def pw_verify(failures):
    async with async_playwright() as pw:
        browser = await pw.firefox.launch(headless=True)
        sem = asyncio.Semaphore(PW_CONCURRENCY)

        async def _run(f):
            async with sem:
                return await pw_probe(browser, f["city"], f["field"], f["url"])

        results = await asyncio.gather(*[_run(f) for f in failures])
        await browser.close()
    return results


def _curl_ok(r) -> bool:
    return not r["error"] and r["status"] and 200 <= r["status"] < 400


def _pw_ok(r) -> bool:
    return not r["error"] and r["status"] and 200 <= r["status"] < 400


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower()


CONNECTION_ERROR_SIGNALS = (
    "etimedout", "econnrefused", "econnreset",
    "ns_error_net_timeout", "ns_error_net_reset", "ns_error_net_interrupt",
    "timeout", "no response", "net::err_",
)


def _is_connection_error(r) -> bool:
    """True when we never got an HTTP status — server refused/dropped before responding.

    Distinct from a 4xx/5xx, which means the server DID respond and the specific URL is bad.
    Connection-level failures across a whole domain usually mean an IP-scoped WAF block,
    not a dead site (see: ggcity.org from cloud egress, July 2026).
    """
    if r.get("status"):
        return False
    err = (r.get("error") or "").lower()
    return any(sig in err for sig in CONNECTION_ERROR_SIGNALS)


def main():
    jobs = []
    for path in sorted(DATA_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        jobs.extend(extract_urls(path.stem, data))

    n_cities = len(list(DATA_DIR.glob("*.yaml")))
    print(f"Phase 1: curl-probing {len(jobs)} URLs across {n_cities} cities...", file=sys.stderr)
    with concurrent.futures.ThreadPoolExecutor(max_workers=CURL_WORKERS) as ex:
        curl_results = list(ex.map(lambda j: curl_probe(*j), jobs))

    # Retry every curl failure with Playwright — curl false positives are rampant on civic WAFs.
    retry_pool = [r for r in curl_results if not _curl_ok(r)]
    print(f"Phase 2: verifying {len(retry_pool)} curl failures with Playwright + Firefox...", file=sys.stderr)
    pw_results = asyncio.run(pw_verify(retry_pool)) if retry_pool else []
    pw_by_url = {r["url"]: r for r in pw_results}

    collapsed, truly_broken, waf_only, ok, needs_encode = [], [], [], [], []
    for r in curl_results:
        if r.get("space_encoded"):
            needs_encode.append(r)
        if _curl_ok(r):
            if _collapsed(r["url"], r["final"]):
                collapsed.append({**r, "phase": "curl"})
            else:
                ok.append(r)
            continue
        p = pw_by_url[r["url"]]
        if _pw_ok(p):
            if _collapsed(p["url"], p["final"]):
                collapsed.append({**p, "phase": "pw"})
            else:
                waf_only.append({**p, "curl_status": r["status"]})
        else:
            truly_broken.append({**p, "curl_status": r["status"], "curl_error": r["error"],
                                 "original_url": r.get("original_url"), "space_encoded": r.get("space_encoded")})

    # Partition truly_broken: separate whole-domain network-refusals (likely IP-scoped WAF,
    # not real breakage) from URLs where the server actually returned an HTTP status.
    domain_success = {}
    for r in ok + waf_only + collapsed:
        domain_success[_domain(r["url"])] = domain_success.get(_domain(r["url"]), 0) + 1

    fails_by_domain = {}
    for r in truly_broken:
        fails_by_domain.setdefault(_domain(r["url"]), []).append(r)

    unverifiable, real_broken = [], []
    for r in truly_broken:
        d = _domain(r["url"])
        if domain_success.get(d, 0) == 0 and all(_is_connection_error(x) for x in fails_by_domain[d]):
            unverifiable.append(r)
        else:
            real_broken.append(r)

    print(f"\nSummary of {len(curl_results)} URLs:")
    print(f"  OK (curl):        {len(ok)}")
    print(f"  OK (browser only, WAF-blocked to curl): {len(waf_only)}")
    print(f"  COLLAPSED-TO-ROOT: {len(collapsed)}")
    print(f"  TRULY BROKEN:     {len(real_broken)}")
    print(f"  UNVERIFIABLE (whole domain refused connection — likely WAF, spot-check manually): {len(unverifiable)}")
    print(f"  YAML has literal spaces (should be %20): {len(needs_encode)}\n")

    if needs_encode:
        print("=== YAML DATA QUALITY: URLs with literal spaces (encode as %20) ===")
        by_city = {}
        for r in needs_encode:
            by_city.setdefault(r["city"], []).append(r)
        for city, items in sorted(by_city.items()):
            print(f"\n  {city}:")
            for r in items:
                print(f"    {r['field']}: {r['original_url']}")
        print()

    if collapsed:
        print("=== COLLAPSED-TO-ROOT (deep page gone, redirect to homepage) ===")
        by_city = {}
        for r in collapsed:
            by_city.setdefault(r["city"], []).append(r)
        for city, items in sorted(by_city.items()):
            print(f"\n  {city}:")
            for r in items:
                print(f"    {r['field']}")
                print(f"      {r['url']}")
                print(f"      -> {r['final']}")

    if real_broken:
        print("\n=== TRULY BROKEN (server responded on this domain, but this URL is dead) ===")
        by_city = {}
        for r in real_broken:
            by_city.setdefault(r["city"], []).append(r)
        for city, items in sorted(by_city.items()):
            print(f"\n  {city}:")
            for r in items:
                tag = r["error"] or f"status {r['status']}"
                curl_tag = r.get("curl_error") or f"curl {r.get('curl_status')}"
                print(f"    {r['field']}  [browser: {tag}]  [curl: {curl_tag}]")
                print(f"      {r['url']}")

    if unverifiable:
        print("\n=== UNVERIFIABLE (whole domain refused every probe — likely IP-scoped WAF, spot-check) ===")
        by_city = {}
        for r in unverifiable:
            by_city.setdefault(r["city"], []).append(r)
        for city, items in sorted(by_city.items()):
            domains = sorted({_domain(r["url"]) for r in items})
            print(f"\n  {city} ({', '.join(domains)}): {len(items)} URL(s)")
            for r in items:
                print(f"    {r['field']}: {r['url']}")

    return 1 if (real_broken or collapsed) else 0


if __name__ == "__main__":
    sys.exit(main())
