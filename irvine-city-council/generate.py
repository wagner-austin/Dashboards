"""
Irvine City Council Dashboard HTML Generator

Run this script to generate a fresh HTML dashboard with live data.

Usage:
    python generate.py           # Full scrape with Playwright
    python generate.py --quick   # Quick refresh (cached data only)
"""

import json
import re
from datetime import datetime
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright


def fetch_council_members():
    """Fetch current council members from City of Irvine website."""
    # Hardcoded data since the city website structure is stable
    # Photos and links are scraped from https://cityofirvine.org/city-council
    members = [
        {
            "name": "Larry Agran",
            "position": "Mayor",
            "district": "At-Large",
            "photo": "https://www.cityofirvine.org/sites/default/files/city-files/PIO/Images/Website/Ziba%20Photo%20Video%20-%20Mayor%20Larry%20Agran%203.jpg",
            "email": "LarryAgran@cityofirvine.org",
            "bio": "First served on Irvine City Council 1978-1990, including six years as Mayor. Elected Mayor in 2024 for his eighth nonconsecutive term. Harvard Law School graduate.",
            "website": "https://mayorlarryagran.org"
        },
        {
            "name": "James Mai",
            "position": "Vice Mayor",
            "district": "District 3",
            "photo": "https://www.cityofirvine.org/sites/default/files/file-repository/CM%20Mai_5x7.jpg",
            "email": "JamesMai@cityofirvine.org",
            "bio": "Vice Mayor representing District 3 on the Irvine City Council.",
            "website": None
        },
        {
            "name": "Melinda Liu",
            "position": "Councilmember",
            "district": "District 1",
            "photo": "https://www.cityofirvine.org/sites/default/files/file-repository/CM%20Liu_5x7.jpg",
            "email": "MelindaLiu@cityofirvine.org",
            "bio": "Councilmember representing District 1.",
            "website": "https://www.melindaliuirvine.com"
        },
        {
            "name": "William Go",
            "position": "Councilmember",
            "district": "District 2",
            "photo": "https://www.cityofirvine.org/sites/default/files/file-repository/CM%20Go_5x7.jpg",
            "email": "WilliamGo@cityofirvine.org",
            "bio": "Councilmember representing District 2.",
            "website": None
        },
        {
            "name": "Mike Carroll",
            "position": "Councilmember",
            "district": "District 4",
            "photo": "https://cityofirvine.org/sites/default/files/City%20Council/2024/Mike%20Carroll_with%20pin_.png",
            "email": "MikeCarroll@cityofirvine.org",
            "bio": "Serving second term on City Council. Vice Chairman of the Great Park. Corporate attorney, OCTA Board Member, and New York Times bestselling author.",
            "website": None
        },
        {
            "name": "Betty Martinez Franco",
            "position": "Councilmember",
            "district": "District 5",
            "photo": "https://cityofirvine.org/sites/default/files/City%20Council/2024/Betty%20Martinez%20Franco_400x560px.jpg",
            "email": "BettyMartinezFranco@cityofirvine.org",
            "bio": "Councilmember representing District 5.",
            "website": None
        },
        {
            "name": "Kathleen Treseder",
            "position": "Councilmember",
            "district": "At-Large",
            "photo": "https://www.cityofirvine.org/sites/default/files/City%20Council/2024/CM%20Treseder_2x3.jpg",
            "email": "KathleenTreseder@cityofirvine.org",
            "bio": "At-Large Councilmember on the Irvine City Council.",
            "website": None
        },
    ]
    return members


def fetch_meetings_granicus():
    """Fetch meeting data from Granicus portal using Playwright."""
    meetings = []
    seen_keys = set()  # Deduplicate

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Load the Granicus meeting archive
            page.goto("https://irvine.granicus.com/ViewPublisher.php?view_id=68", wait_until="networkidle")
            page.wait_for_timeout(2000)

            # Scroll to load all content (Granicus lazy loads)
            for _ in range(10):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(500)

            # Get all links that have AgendaViewer - these are meeting rows
            agenda_links = page.query_selector_all('a[href*="AgendaViewer"]')

            for link in agenda_links:
                try:
                    # Get the parent row
                    row = link.evaluate_handle("el => el.closest('tr')")
                    if not row:
                        continue

                    row_el = row.as_element()
                    if not row_el:
                        continue

                    # Get all text in row to find meeting info
                    row_text = row_el.inner_text()

                    # Skip non-council meetings
                    if "CITY COUNCIL" not in row_text.upper():
                        continue

                    # Parse date from row text - handles "Jan 13, 2026" or "January 27, 2026"
                    # Also handles non-breaking spaces
                    row_text_clean = row_text.replace('\xa0', ' ')
                    date_match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", row_text_clean)
                    if not date_match:
                        continue

                    month_str = date_match.group(1)
                    day_str = date_match.group(2)
                    year_str = date_match.group(3)

                    # Convert abbreviated month to full name for consistency
                    month_map = {
                        'Jan': 'January', 'Feb': 'February', 'Mar': 'March',
                        'Apr': 'April', 'May': 'May', 'Jun': 'June',
                        'Jul': 'July', 'Aug': 'August', 'Sep': 'September',
                        'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
                    }
                    if month_str in month_map:
                        month_str = month_map[month_str]

                    date_str = f"{month_str} {day_str}, {year_str}"

                    # Get meeting name (first line or first part)
                    lines = [l.strip() for l in row_text.split('\n') if l.strip()]
                    name_text = lines[0] if lines else "City Council Meeting"

                    # Clean up the name
                    name_text = re.sub(r'\s+', ' ', name_text).strip()
                    if len(name_text) > 100:
                        name_text = name_text[:100]

                    # Get agenda URL
                    agenda_url = link.get_attribute("href")
                    if agenda_url and agenda_url.startswith("//"):
                        agenda_url = "https:" + agenda_url

                    # Get minutes link from same row
                    minutes_link = row_el.query_selector('a[href*="MinutesViewer"]')
                    minutes_url = minutes_link.get_attribute("href") if minutes_link else None
                    if minutes_url and minutes_url.startswith("//"):
                        minutes_url = "https:" + minutes_url

                    # Get video player link (not MP4 download)
                    # Extract clip_id from agenda URL to build player URL
                    video_url = None
                    if agenda_url:
                        clip_match = re.search(r"clip_id=(\d+)", agenda_url)
                        if clip_match:
                            clip_id = clip_match.group(1)
                            video_url = f"https://irvine.granicus.com/player/clip/{clip_id}?view_id=68"

                    # Get event_id for agenda fetching
                    event_id = None
                    if agenda_url:
                        event_match = re.search(r"event_id=(\d+)", agenda_url)
                        if event_match:
                            event_id = event_match.group(1)

                    # Create unique key to avoid duplicates
                    key = f"{date_str}|{event_id or agenda_url}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    meetings.append({
                        "name": name_text,
                        "date": date_str,
                        "agenda_url": agenda_url,
                        "minutes_url": minutes_url,
                        "video_url": video_url,
                        "event_id": event_id
                    })

                except Exception:
                    continue

        finally:
            browser.close()

    # Sort meetings by date (newest first)
    def parse_date(date_str):
        try:
            # Handle dates like "January 27, 2026" or "January  2, 2026"
            return datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%B  %d, %Y")
            except ValueError:
                return datetime.min

    meetings.sort(key=lambda m: parse_date(m["date"]), reverse=True)
    return meetings


def fetch_upcoming_agenda(event_id: str):
    """Fetch agenda items for an upcoming meeting."""
    agenda_items = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            url = f"https://irvine.granicus.com/AgendaViewer.php?view_id=68&event_id={event_id}"
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(2000)

            # Get the text content
            body = page.query_selector("body")
            text = body.inner_text() if body else ""

            # Parse agenda sections
            lines = text.split("\n")
            current_section = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Detect section headers
                if re.match(r"^\d+\.\s+", line) or line.upper() in ["CLOSED SESSION", "PRESENTATIONS", "CONSENT CALENDAR", "PUBLIC HEARINGS", "COUNCIL BUSINESS"]:
                    current_section = line

                # Detect agenda items (numbered like 3.1, 4.1, etc.)
                item_match = re.match(r"^(\d+\.\d+)\s+(.+)", line)
                if item_match:
                    agenda_items.append({
                        "number": item_match.group(1),
                        "title": item_match.group(2)[:200],
                        "section": current_section
                    })

        finally:
            browser.close()

    return agenda_items


def generate_html(data: dict) -> str:
    """Generate the complete HTML dashboard."""

    # Convert data to JSON for embedding
    data_json = json.dumps(data, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1024, viewport-fit=cover, user-scalable=yes">
    <title>Irvine City Council Dashboard</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
    <style>
        :root {{
            --primary: #0066a1;
            --primary-dark: #004d7a;
            --primary-light: #e8f4fc;
            --accent: #4da6d9;
            --accent-light: #d9eef8;
            --success: #16a34a;
            --success-light: #dcfce7;
            --warning: #ca8a04;
            --warning-light: #fef3c7;
            --danger: #dc2626;
            --danger-light: #fee2e2;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            font-size: 1rem;
            line-height: 1.6;
            color: var(--gray-800);
            background: linear-gradient(135deg, #e8f4fc 0%, #f0f7fc 50%, #e0f0f8 100%);
            min-height: 100vh;
        }}
        .header-container {{
            position: sticky;
            top: 0;
            z-index: 100;
            background: white;
        }}
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 1.5rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 1.5rem; }}
        .header .subtitle {{ font-size: 0.9rem; opacity: 0.9; margin-top: 0.25rem; }}
        .tabs {{
            display: flex;
            gap: 0.25rem;
            background: white;
            padding: 0.5rem 2rem;
            border-bottom: 1px solid var(--gray-200);
            overflow-x: auto;
        }}
        .tab {{
            padding: 0.75rem 1.25rem;
            cursor: pointer;
            border: none;
            background: var(--accent-light);
            font-size: 0.9rem;
            font-weight: 500;
            color: var(--gray-700);
            border-radius: 6px 6px 0 0;
            transition: all 0.2s;
            white-space: nowrap;
        }}
        .tab:hover {{ background: var(--primary-light); }}
        .tab.active {{
            color: var(--primary-dark);
            border-bottom: 3px solid var(--primary);
            background: white;
        }}
        .tab-content {{
            display: none;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.5);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            min-height: calc(100vh - 150px);
        }}
        .tab-content.active {{ display: block; }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1.25rem;
            border: 1px solid rgba(255, 255, 255, 0.3);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,102,161,0.15); }}
        .card.highlight {{ background: linear-gradient(135deg, var(--primary-light) 0%, #c8e6dc 100%); border-color: var(--primary); }}
        .card.gold {{ background: linear-gradient(135deg, var(--accent-light) 0%, #fff3cc 100%); border-color: var(--accent); }}
        .card h4 {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--gray-600); margin-bottom: 0.25rem; }}
        .card .value {{ font-size: 2rem; font-weight: 700; color: var(--gray-900); }}
        .card .subtext {{ font-size: 0.75rem; color: var(--gray-600); }}
        h2 {{ font-size: 1.25rem; margin-bottom: 1rem; color: var(--gray-800); border-bottom: 3px solid var(--accent); padding-bottom: 0.5rem; display: inline-block; }}
        h3 {{ font-size: 1rem; margin: 1.5rem 0 0.75rem; color: var(--gray-700); }}
        .section {{ margin-bottom: 2rem; }}
        .alert {{ padding: 1rem; border-radius: 8px; margin: 1rem 0; font-size: 0.9rem; }}
        .alert-info {{ background: var(--primary-light); border-left: 4px solid var(--primary); color: var(--primary-dark); }}
        .links-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin: 1.5rem 0; }}
        .link-card {{
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.4);
            border-radius: 12px;
            padding: 1.25rem;
            text-decoration: none;
            color: var(--gray-800);
            transition: all 0.2s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        .link-card:hover {{ border-color: var(--primary); box-shadow: 0 8px 24px rgba(0,102,161,0.2); transform: translateY(-3px); }}
        .link-card h4 {{ color: var(--primary); margin-bottom: 0.5rem; font-size: 1rem; }}
        .link-card p {{ font-size: 0.85rem; margin: 0; color: var(--gray-600); }}
        .next-meeting-banner {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 15px rgba(0,87,63,0.3);
        }}
        .next-meeting-banner h3 {{ color: var(--accent); margin: 0 0 0.5rem 0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.1em; }}
        .next-meeting-banner .date {{ font-size: 1.5rem; font-weight: 700; }}
        .next-meeting-banner .location {{ opacity: 0.9; font-size: 0.9rem; margin-top: 0.25rem; }}
        .next-meeting-banner .zoom-btn {{
            background: var(--accent);
            color: var(--primary-dark);
            padding: 0.85rem 1.75rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.2s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        .next-meeting-banner .zoom-btn:hover {{ background: #6bb8e0; transform: scale(1.05); }}
        .recent-meetings-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; }}
        .meeting-card {{
            background: rgba(255, 255, 255, 0.75);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.4);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.2s;
        }}
        .meeting-card:hover {{ border-color: var(--primary); box-shadow: 0 8px 24px rgba(0,102,161,0.15); }}
        .meeting-card .meeting-date {{ font-weight: 700; font-size: 1.1rem; color: var(--gray-900); margin-bottom: 0.25rem; }}
        .meeting-card .meeting-type {{ font-size: 0.85rem; color: var(--gray-600); margin-bottom: 0.5rem; }}
        .meeting-card .meeting-links {{ display: flex; gap: 0.75rem; flex-wrap: wrap; }}
        .meeting-card .meeting-links a {{
            font-size: 0.8rem;
            color: var(--primary);
            text-decoration: none;
            padding: 0.25rem 0.5rem;
            background: var(--primary-light);
            border-radius: 4px;
        }}
        .meeting-card .meeting-links a:hover {{ background: var(--primary); color: white; }}
        table.dataTable {{ font-size: 0.85rem; }}
        table.dataTable thead th {{ background: var(--primary); color: white; }}
        table.dataTable tbody tr:hover {{ background: var(--primary-light) !important; }}
        .dataTables_wrapper .dataTables_length,
        .dataTables_wrapper .dataTables_filter,
        .dataTables_wrapper .dataTables_info,
        .dataTables_wrapper .dataTables_paginate {{ font-size: 0.85rem; }}
        .refresh-time {{ font-size: 0.75rem; color: var(--gray-600); text-align: right; padding: 1rem 2rem; background: var(--gray-100); }}
        .council-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1.25rem; }}
        .council-card {{
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.4);
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            transition: all 0.2s;
        }}
        .council-card:hover {{ border-color: var(--primary); box-shadow: 0 8px 24px rgba(0,102,161,0.15); }}
        .council-card .photo {{
            width: 140px;
            height: 175px;
            object-fit: cover;
            object-position: top;
            margin: 0 auto 1rem;
            display: block;
            border-radius: 8px;
        }}
        .council-card .name {{ font-weight: 700; color: var(--gray-900); margin-bottom: 0.25rem; font-size: 1.1rem; }}
        .council-card .position {{ font-size: 0.9rem; color: var(--primary); font-weight: 500; }}
        .council-card .district {{ font-size: 0.8rem; color: var(--gray-600); margin-top: 0.25rem; }}
        .council-card .email {{ font-size: 0.75rem; color: var(--gray-600); margin-top: 0.75rem; }}
        .council-card .email a {{ color: var(--gray-600); text-decoration: none; }}
        .council-card .email a:hover {{ color: var(--primary); }}
        .agenda-list {{ list-style: none; }}
        .agenda-item {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--gray-200);
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
        }}
        .agenda-item:hover {{ background: var(--gray-50); }}
        .agenda-item .number {{ font-weight: 600; color: var(--primary); min-width: 3rem; }}
        .agenda-item .title {{ color: var(--gray-800); }}
        @media (max-width: 768px) {{
            .tabs {{ padding: 0.5rem 1rem; }}
            .tab {{ padding: 0.5rem 0.75rem; font-size: 0.8rem; }}
            .tab-content {{ padding: 1rem; }}
            .summary-cards {{ grid-template-columns: repeat(2, 1fr); }}
            .next-meeting-banner {{ flex-direction: column; text-align: center; gap: 1rem; }}
        }}
    </style>
</head>
<body>
    <div class="header-container">
        <div class="header">
            <h1>Irvine City Council Dashboard</h1>
            <div class="subtitle">City of Irvine, California - Meeting Tracker</div>
        </div>
        <div class="tabs">
            <button class="tab active" onclick="showTab('overview')">Overview</button>
            <button class="tab" onclick="showTab('meetings')">Meetings</button>
            <button class="tab" onclick="showTab('council')">Council Members</button>
            <button class="tab" onclick="showTab('resources')">Resources</button>
        </div>
    </div>

    <div id="overview" class="tab-content active">
        <div class="next-meeting-banner">
            <div>
                <h3>Next Meeting</h3>
                <div class="date" id="next-meeting-date">Loading...</div>
                <div class="location">City Council Chamber, 1 Civic Center Plaza</div>
            </div>
            <div style="text-align: right;">
                <a href="https://www.zoomgov.com/j/1600434844" target="_blank" class="zoom-btn">Join via Zoom</a>
                <div style="margin-top: 0.5rem; font-size: 0.8rem; opacity: 0.9;">Meeting ID: 160 043 4844 &nbsp;|&nbsp; Passcode: 272906</div>
            </div>
        </div>

        <div class="section">
            <h2>Recent Meetings</h2>
            <div id="recent-meetings" class="recent-meetings-grid"></div>
        </div>

        <div class="section">
            <h2>Quick Links</h2>
            <div class="links-grid">
                <a href="https://irvine.granicus.com/ViewPublisher.php?view_id=68" target="_blank" class="link-card">
                    <h4>Meeting Archive</h4>
                    <p>View all past meetings, agendas, minutes, and videos</p>
                </a>
                <a href="https://irvine.granicusideas.com/meetings" target="_blank" class="link-card">
                    <h4>Submit eComment</h4>
                    <p>Submit public comments on agenda items</p>
                </a>
                <a href="https://cityofirvine.org/city-council" target="_blank" class="link-card">
                    <h4>City Council</h4>
                    <p>Council member profiles and contact info</p>
                </a>
                <a href="https://legacy.cityofirvine.org/cityhall/citymanager/pio/ictv/default.asp" target="_blank" class="link-card">
                    <h4>ICTV Live</h4>
                    <p>Watch meetings live on Irvine Community TV</p>
                </a>
            </div>
        </div>
    </div>

    <div id="meetings" class="tab-content">
        <h2>Meeting Archive</h2>
        <p style="margin-bottom:1rem;color:var(--gray-600)">All City Council meetings with agendas, minutes, and video recordings.</p>
        <table id="meetings-table" class="display" style="width:100%">
            <thead><tr><th>Date</th><th>Meeting Type</th><th>Agenda</th><th>Minutes</th><th>Video</th></tr></thead>
            <tbody id="meetings-tbody"></tbody>
        </table>
    </div>

    <div id="council" class="tab-content">
        <h2>2024-2028 City Council</h2>
        <p style="margin-bottom:1.5rem;color:var(--gray-600)">The Irvine City Council expanded to 7 members in March 2024: a Mayor at-large and 6 Councilmembers by district.</p>
        <div id="council-grid" class="council-grid"></div>
    </div>

    <div id="resources" class="tab-content">
        <h2>City Resources</h2>
        <div class="section">
            <h3>Meeting Information</h3>
            <div class="links-grid">
                <a href="https://cityofirvine.org/city-council/city-council-meetings" target="_blank" class="link-card">
                    <h4>Meeting Schedule</h4>
                    <p>2nd and 4th Tuesdays at 4:00 PM</p>
                </a>
                <a href="https://irvine.granicus.com/ViewPublisher.php?view_id=68" target="_blank" class="link-card">
                    <h4>Agendas</h4>
                    <p>Current and archived meeting agendas</p>
                </a>
                <a href="https://irvine.granicus.com/ViewPublisher.php?view_id=68" target="_blank" class="link-card">
                    <h4>Video Archive</h4>
                    <p>Watch recorded meetings on Granicus</p>
                </a>
                <a href="https://legacy.cityofirvine.org/cityhall/citymanager/pio/ictv/player/default.asp?ID=512" target="_blank" class="link-card">
                    <h4>ICTV Archive</h4>
                    <p>Meeting videos on Irvine Community TV</p>
                </a>
            </div>
        </div>
        <div class="section">
            <h3>Public Participation</h3>
            <div class="links-grid">
                <a href="https://irvine.granicusideas.com/meetings" target="_blank" class="link-card">
                    <h4>eComment System</h4>
                    <p>Submit written comments on agenda items</p>
                </a>
                <a href="https://cityofirvine.org/city-council/contact-council" target="_blank" class="link-card">
                    <h4>Contact the Council</h4>
                    <p>Email or call your representatives</p>
                </a>
                <a href="https://cityofirvine.maps.arcgis.com/apps/dashboards/99a9ff74e04f433ab1f49d015ba1a2cb" target="_blank" class="link-card">
                    <h4>District Dashboard</h4>
                    <p>Find your council district</p>
                </a>
                <a href="https://irvineca.seamlessdocs.com/f/citycouncilinvitation" target="_blank" class="link-card">
                    <h4>Invite a Councilmember</h4>
                    <p>Request a councilmember to attend your event</p>
                </a>
            </div>
        </div>
        <div class="alert alert-info" style="margin-top:2rem">
            <strong>Regular Meetings:</strong> 2nd and 4th Tuesdays at 4:00 PM<br>
            <strong>Location:</strong> City Council Chamber, 1 Civic Center Plaza, Irvine, CA 92606<br>
            <strong>Zoom:</strong> Meeting ID 160-043-4844 | Passcode 272906<br>
            <strong>Phone:</strong> 669-254-5252 or 669-216-1590<br>
            <strong>TV:</strong> ICTV (Cox Channel 30, AT&T U-verse Channel 99)<br><br>
            <em>Contact City Clerk's Office: (949) 724-6205 | irvinecitycouncil@cityofirvine.org</em>
        </div>
    </div>

    <div class="refresh-time">Data generated: {data["generated_at"]}</div>

    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <script>
        const DATA = {data_json};

        function showTab(id) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            event.target.classList.add('active');
        }}

        function getNextMeeting() {{
            const now = new Date();
            const year = now.getFullYear();
            const month = now.getMonth();

            // Find 2nd and 4th Tuesday of current month
            function getNthTuesday(year, month, n) {{
                let count = 0;
                for (let day = 1; day <= 31; day++) {{
                    const date = new Date(year, month, day);
                    if (date.getMonth() !== month) break;
                    if (date.getDay() === 2) {{ // Tuesday
                        count++;
                        if (count === n) return date;
                    }}
                }}
                return null;
            }}

            const secondTue = getNthTuesday(year, month, 2);
            const fourthTue = getNthTuesday(year, month, 4);

            let nextMeeting = null;
            const today = new Date(year, month, now.getDate());
            today.setHours(16, 0, 0, 0); // 4 PM

            if (secondTue && secondTue >= now) {{
                nextMeeting = secondTue;
            }} else if (fourthTue && fourthTue >= now) {{
                nextMeeting = fourthTue;
            }} else {{
                // Next month
                nextMeeting = getNthTuesday(year, month + 1, 2);
            }}

            if (nextMeeting) {{
                return nextMeeting.toLocaleDateString('en-US', {{ weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }}) + ' at 4:00 PM';
            }}
            return 'Check schedule';
        }}

        function parseDate(dateStr) {{
            const parsed = new Date(dateStr);
            return isNaN(parsed.getTime()) ? 0 : parsed.getTime();
        }}

        function init() {{
            document.getElementById('next-meeting-date').textContent = getNextMeeting();

            // Recent meetings
            const recentEl = document.getElementById('recent-meetings');
            const meetings = (DATA.meetings || []).slice(0, 8);
            let recentHtml = '';

            meetings.forEach(m => {{
                recentHtml += '<div class="meeting-card">' +
                    '<div class="meeting-date">' + m.date + '</div>' +
                    '<div class="meeting-type">' + m.name + '</div>' +
                    '<div class="meeting-links">' +
                        (m.agenda_url ? '<a href="' + m.agenda_url + '" target="_blank">Agenda</a>' : '') +
                        (m.minutes_url ? '<a href="' + m.minutes_url + '" target="_blank">Minutes</a>' : '') +
                        (m.video_url ? '<a href="' + m.video_url + '" target="_blank">Video</a>' : '') +
                    '</div>' +
                '</div>';
            }});
            recentEl.innerHTML = recentHtml || '<p>No recent meetings found</p>';

            // Council members grid
            const councilEl = document.getElementById('council-grid');
            let councilHtml = '';
            (DATA.council_members || []).forEach(m => {{
                councilHtml += '<div class="council-card">' +
                    '<img class="photo" src="' + m.photo + '" alt="' + m.name + '">' +
                    '<div class="name">' + m.name + '</div>' +
                    '<div class="position">' + m.position + '</div>' +
                    '<div class="district">' + m.district + '</div>' +
                    '<div class="email"><a href="mailto:' + m.email + '">' + m.email + '</a></div>' +
                '</div>';
            }});
            councilEl.innerHTML = councilHtml;

            // Meetings table
            const tbody = document.getElementById('meetings-tbody');
            let tableHtml = '';
            (DATA.meetings || []).forEach(m => {{
                const timestamp = parseDate(m.date);
                tableHtml += '<tr>' +
                    '<td data-order="' + timestamp + '">' + m.date + '</td>' +
                    '<td>' + m.name + '</td>' +
                    '<td>' + (m.agenda_url ? '<a href="' + m.agenda_url + '" target="_blank">View</a>' : '-') + '</td>' +
                    '<td>' + (m.minutes_url ? '<a href="' + m.minutes_url + '" target="_blank">View</a>' : '-') + '</td>' +
                    '<td>' + (m.video_url ? '<a href="' + m.video_url + '" target="_blank">Watch</a>' : '-') + '</td>' +
                '</tr>';
            }});
            tbody.innerHTML = tableHtml || '<tr><td colspan="5">No meetings found</td></tr>';

            if (DATA.meetings && DATA.meetings.length > 0) {{
                $('#meetings-table').DataTable({{
                    paging: true,
                    pageLength: 25,
                    order: [[0, 'desc']]
                }});
            }}
        }}

        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>'''

    return html


def main(quick_mode=False):
    """Main function to generate the dashboard."""
    print("=" * 60)
    print("Irvine City Council Dashboard Generator")
    print("=" * 60)

    # Fetch council members
    print("\n[*] Loading council member data...")
    council_members = fetch_council_members()
    print(f"    Council members: {len(council_members)}")

    # Fetch meetings
    if quick_mode:
        print("\n[*] Quick mode - skipping Playwright scrape...")
        meetings = []
    else:
        print("\n[*] Fetching meetings from Granicus (Playwright)...")
        meetings = fetch_meetings_granicus()
        print(f"    Meetings found: {len(meetings)}")

    # Compile data
    data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "council_members": council_members,
        "meetings": meetings,
    }

    # Generate HTML
    print("\n[*] Generating HTML...")
    html = generate_html(data)

    # Save as index.html
    output_path = Path(__file__).parent / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[*] Dashboard saved to: {output_path}")
    print("[*] Ready for GitHub Pages!")

    return str(output_path)


if __name__ == "__main__":
    import sys
    quick = "--quick" in sys.argv
    main(quick_mode=quick)
