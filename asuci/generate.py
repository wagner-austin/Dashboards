"""
ASUCI Dashboard HTML Generator

Run this script to generate a fresh HTML dashboard with live data.

Usage:
    python generate_asuci_html.py           # Full scrape with Playwright
    python generate_asuci_html.py --quick   # Quick refresh (Google Sheets only)
"""

import json
import csv
import re
from io import StringIO
from datetime import datetime
from pathlib import Path

import requests


def fetch_senators_playwright():
    """Fetch current senators from ASUCI website with photos."""
    from playwright.sync_api import sync_playwright
    import re

    senators = []
    leadership = []

    # Leadership positions to identify
    leadership_titles = [
        "senate president", "president pro tempore", "senate parliamentarian",
        "senate secretary", "senate historian", "senate sergeant"
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://asuci.uci.edu/senate/", wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Scroll to load lazy content
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

        # Find all fusion-text elements that contain ASUCI emails
        text_elements = page.query_selector_all(".fusion-text")

        for text_el in text_elements:
            try:
                html = text_el.inner_html()
                text = text_el.inner_text()

                # Check if this element has an ASUCI email
                if "@asuci.uci.edu" not in text:
                    continue

                # Parse the text - typically "Name\nPosition\nemail"
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if len(lines) < 2:
                    continue

                name = lines[0]
                position = ""
                email = ""

                for line in lines[1:]:
                    if "@asuci.uci.edu" in line:
                        email = line
                    elif not position:
                        position = line

                if not name or "Vacant" in name:
                    continue

                # Find associated image - look in the parent column
                parent = text_el.evaluate_handle("el => el.closest('.fusion-layout-column')")
                photo = ""
                if parent:
                    img = parent.as_element().query_selector("img")
                    if img:
                        photo = img.get_attribute("src") or img.get_attribute("data-orig-src") or ""

                senator = {"name": name, "position": position, "email": email, "photo": photo}

                # Check if this is a leadership position
                is_leader = any(title in position.lower() for title in leadership_titles)
                if is_leader:
                    leadership.append(senator)
                else:
                    senators.append(senator)

            except Exception:
                continue

        browser.close()

    # Deduplicate by email - keep first occurrence (usually the more important role)
    seen_emails = set()
    deduped_leadership = []
    for s in leadership:
        if s["email"] and s["email"] not in seen_emails:
            seen_emails.add(s["email"])
            deduped_leadership.append(s)

    deduped_senators = []
    for s in senators:
        if s["email"] and s["email"] not in seen_emails:
            seen_emails.add(s["email"])
            deduped_senators.append(s)

    return {"leadership": deduped_leadership, "senators": deduped_senators}


def fetch_meeting_links_playwright():
    """Fetch meeting links using Playwright."""
    from playwright.sync_api import sync_playwright

    meeting_links = {"agendas": {}, "minutes": {}}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # First, fetch CURRENT agendas (2025-2026)
        page.goto("https://asuci.uci.edu/senate/agendas/", wait_until="networkidle")
        page.wait_for_timeout(2000)

        current_meetings = []
        links = page.query_selector_all("a")
        for link in links:
            href = link.get_attribute("href") or ""
            text = link.inner_text().strip()
            if "agendas/print" in href and re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+,?\s*\d{4}", text):
                current_meetings.append({"date": text, "url": href})

        if current_meetings:
            meeting_links["agendas"]["25-26"] = current_meetings

        # Then fetch archive (historical years)
        page.goto("https://asuci.uci.edu/senate/agendas/archive/", wait_until="networkidle")
        page.wait_for_selector(".fusion-tabs", timeout=10000)

        tabs = page.query_selector_all(".fusion-tabs .nav-tabs a")

        for tab in tabs[:7]:
            tab_text = tab.inner_text().strip()
            if not re.match(r"\d{2}-\d{2}", tab_text):
                continue

            tab.click()
            page.wait_for_timeout(500)

            active_panel = page.query_selector(".fusion-tabs .tab-pane.active")
            if active_panel:
                links = active_panel.query_selector_all("a")
                year_links = []
                for link in links:
                    href = link.get_attribute("href") or ""
                    text = link.inner_text().strip()
                    if text and "agendas/print" in href:
                        year_links.append({"date": text, "url": href})
                if year_links:
                    meeting_links["agendas"][tab_text] = year_links

        browser.close()

    return meeting_links


def generate_html(data: dict) -> str:
    """Generate the complete HTML dashboard."""

    # Calculate stats
    num_leadership = len(data["senators"].get("leadership", []))
    num_senators = len(data["senators"].get("senators", []))
    total_agendas = sum(len(v) for v in data["meeting_links"].get("agendas", {}).values())

    # Convert data to JSON for embedding
    data_json = json.dumps(data, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1024, viewport-fit=cover, user-scalable=yes">
    <title>ASUCI Senate Dashboard</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
    <style>
        :root {{
            --primary: #0064a4;
            --primary-dark: #003d66;
            --primary-light: #e6f2fa;
            --gold: #ffc72c;
            --gold-light: #fff9e6;
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
            background: var(--gray-100);
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
            background: var(--gold-light);
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
            background: white;
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
            background: var(--gray-50);
            border-radius: 12px;
            padding: 1.25rem;
            border: 1px solid var(--gray-200);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .card.highlight {{ background: linear-gradient(135deg, var(--primary-light) 0%, #cce5f7 100%); border-color: var(--primary); }}
        .card.gold {{ background: linear-gradient(135deg, var(--gold-light) 0%, #fff3cc 100%); border-color: var(--gold); }}
        .card.success {{ background: linear-gradient(135deg, var(--success-light) 0%, #bbf7d0 100%); border-color: var(--success); }}
        .card.warning {{ background: linear-gradient(135deg, var(--warning-light) 0%, #fde68a 100%); border-color: var(--warning); }}
        .card h4 {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--gray-600); margin-bottom: 0.25rem; }}
        .card .value {{ font-size: 2rem; font-weight: 700; color: var(--gray-900); }}
        .card .subtext {{ font-size: 0.75rem; color: var(--gray-600); }}
        h2 {{ font-size: 1.25rem; margin-bottom: 1rem; color: var(--gray-800); border-bottom: 3px solid var(--gold); padding-bottom: 0.5rem; display: inline-block; }}
        h3 {{ font-size: 1rem; margin: 1.5rem 0 0.75rem; color: var(--gray-700); }}
        .section {{ margin-bottom: 2rem; }}
        .alert {{ padding: 1rem; border-radius: 8px; margin: 1rem 0; font-size: 0.9rem; }}
        .alert-info {{ background: var(--primary-light); border-left: 4px solid var(--primary); color: var(--primary-dark); }}
        .links-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin: 1.5rem 0; }}
        .link-card {{
            background: white;
            border: 1px solid var(--gray-200);
            border-radius: 12px;
            padding: 1.25rem;
            text-decoration: none;
            color: var(--gray-800);
            transition: all 0.2s;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .link-card:hover {{ border-color: var(--primary); box-shadow: 0 4px 12px rgba(0,100,164,0.15); transform: translateY(-3px); }}
        .link-card h4 {{ color: var(--primary); margin-bottom: 0.5rem; font-size: 1rem; }}
        .link-card p {{ font-size: 0.85rem; margin: 0; color: var(--gray-600); }}
        .meeting-list {{ list-style: none; }}
        .meeting-item {{
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--gray-200);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }}
        .meeting-item:hover {{ background: var(--gray-50); }}
        .meeting-date {{ font-weight: 600; color: var(--gray-800); }}
        .meeting-stats {{ display: flex; gap: 1rem; font-size: 0.85rem; }}
        .stat-present {{ color: var(--success); font-weight: 500; }}
        .stat-excused {{ color: var(--warning); font-weight: 500; }}
        .stat-absent {{ color: var(--danger); font-weight: 500; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.6rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }}
        .badge-present {{ background: var(--success-light); color: var(--success); }}
        .badge-excused {{ background: var(--warning-light); color: var(--warning); }}
        .badge-absent {{ background: var(--danger-light); color: var(--danger); }}
        .next-meeting-banner {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 15px rgba(0,100,164,0.3);
        }}
        .next-meeting-banner h3 {{ color: var(--gold); margin: 0 0 0.5rem 0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.1em; }}
        .next-meeting-banner .date {{ font-size: 1.5rem; font-weight: 700; }}
        .next-meeting-banner .location {{ opacity: 0.9; font-size: 0.9rem; margin-top: 0.25rem; }}
        .next-meeting-banner .zoom-btn {{
            background: var(--gold);
            color: var(--primary-dark);
            padding: 0.85rem 1.75rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.2s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        .next-meeting-banner .zoom-btn:hover {{ background: #ffe066; transform: scale(1.05); }}
        .year-select {{ padding: 0.6rem 1.25rem; border: 2px solid var(--gray-200); border-radius: 8px; font-size: 0.95rem; margin-bottom: 1.5rem; cursor: pointer; }}
        .year-select:focus {{ border-color: var(--primary); outline: none; }}
        .recent-meetings-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; }}
        .meeting-card {{
            background: var(--gray-50);
            border: 1px solid var(--gray-200);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.2s;
        }}
        .meeting-card:hover {{ border-color: var(--primary); box-shadow: 0 4px 12px rgba(0,100,164,0.1); }}
        .meeting-card .meeting-date {{ font-weight: 700; font-size: 1.1rem; color: var(--gray-900); margin-bottom: 0.5rem; }}
        .meeting-card .meeting-links {{ display: flex; gap: 0.75rem; margin-bottom: 0.75rem; }}
        .meeting-card .meeting-links a {{
            font-size: 0.8rem;
            color: var(--primary);
            text-decoration: none;
            padding: 0.25rem 0.5rem;
            background: var(--primary-light);
            border-radius: 4px;
        }}
        .meeting-card .meeting-links a:hover {{ background: var(--primary); color: white; }}
        .meeting-card .meeting-attendance {{ font-size: 0.8rem; color: var(--gray-600); }}
        table.dataTable {{ font-size: 0.85rem; }}
        table.dataTable thead th {{ background: var(--primary); color: white; }}
        table.dataTable tbody tr:hover {{ background: var(--primary-light) !important; }}
        .refresh-time {{ font-size: 0.75rem; color: var(--gray-600); text-align: right; padding: 1rem 2rem; background: var(--gray-100); }}
        table.dataTable tbody tr:hover {{ background: var(--primary-light) !important; }}
        .dataTables_wrapper .dataTables_length,
        .dataTables_wrapper .dataTables_filter,
        .dataTables_wrapper .dataTables_info,
        .dataTables_wrapper .dataTables_paginate {{ font-size: 0.85rem; }}
        .senator-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }}
        .senator-card {{
            background: var(--gray-50);
            border: 1px solid var(--gray-200);
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
        }}
        .senator-card .photo {{
            width: 120px;
            height: 120px;
            border-radius: 10px;
            object-fit: cover;
            margin: 0 auto 0.75rem;
            display: block;
            border: 2px solid var(--gray-200);
        }}
        .senator-card .name {{ font-weight: 600; color: var(--gray-900); margin-bottom: 0.25rem; }}
        .senator-card .position {{ font-size: 0.85rem; color: var(--primary); }}
        .senator-card .email {{ font-size: 0.75rem; color: var(--gray-600); margin-top: 0.5rem; }}
        .senator-card .email a {{ color: var(--gray-600); text-decoration: none; }}
        .senator-card .email a:hover {{ color: var(--primary); }}
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
            <h1>ASUCI Senate Dashboard</h1>
            <div class="subtitle">Associated Students of UC Irvine - Senate Meeting Tracker</div>
        </div>
        <div class="tabs">
            <button class="tab active" onclick="showTab('overview')">Overview</button>
            <button class="tab" onclick="showTab('meetings')">Meetings</button>
            <button class="tab" onclick="showTab('senators')">Senators</button>
            <button class="tab" onclick="showTab('resources')">Resources</button>
        </div>
    </div>

    <div id="overview" class="tab-content active">
        <div class="next-meeting-banner">
            <div>
                <h3>Next Meeting</h3>
                <div class="date" id="next-meeting-date">Loading...</div>
                <div class="location">Balboa Island B (4th floor, Student Center) or Zoom</div>
            </div>
            <a href="https://uci.zoom.us/j/97062458514" target="_blank" class="zoom-btn">Join via Zoom</a>
        </div>

        <div class="section">
            <h2>Recent Meetings</h2>
            <div id="recent-meetings" class="recent-meetings-grid"></div>
        </div>

        <div class="section">
            <h2>Quick Links</h2>
            <div class="links-grid">
                <a href="https://asuci.uci.edu/senate/agendas/" target="_blank" class="link-card">
                    <h4>Current Agenda</h4>
                    <p>See what's being discussed at upcoming meetings</p>
                </a>
                <a href="https://www.facebook.com/pg/associatedstudentsuci/videos/" target="_blank" class="link-card">
                    <h4>Meeting Livestreams</h4>
                    <p>Watch live or recorded meetings on Facebook</p>
                </a>
                <a href="https://docs.google.com/spreadsheets/d/1QacWHjtA3dm7VY3TufJlR4BQdmsgAn_65HKO1fBy2lM/edit" target="_blank" class="link-card">
                    <h4>Attendance Records</h4>
                    <p>Senator attendance tracking spreadsheet</p>
                </a>
                <a href="https://asuci.uci.edu/senate/legislation/" target="_blank" class="link-card">
                    <h4>Legislation Archive</h4>
                    <p>All resolutions and bills</p>
                </a>
            </div>
        </div>
    </div>

    <div id="meetings" class="tab-content">
        <h2>Meeting Archive</h2>
        <p style="margin-bottom:1rem;color:var(--gray-600)">Select a year to view meeting agendas and minutes.</p>
        <select class="year-select" id="year-select" onchange="loadYear(this.value)">
            <option value="25-26">2025-26 (Current)</option>
            <option value="24-25">2024-25</option>
            <option value="23-24">2023-24</option>
            <option value="22-23">2022-23</option>
            <option value="21-22">2021-22</option>
            <option value="20-21">2020-21</option>
            <option value="19-20">2019-20</option>
            <option value="18-19">2018-19</option>
        </select>
        <table id="meetings-table" class="display" style="width:100%">
            <thead><tr><th>Date</th><th>Agenda</th><th>Minutes</th></tr></thead>
            <tbody id="meetings-tbody"></tbody>
        </table>
    </div>

    <div id="senators" class="tab-content">
        <h2>2025-2026 Senate</h2>
        <h3 style="margin-top:1.5rem;margin-bottom:1rem;color:var(--gray-700)">Leadership</h3>
        <div id="leadership-grid" class="senator-grid"></div>
        <h3 style="margin-top:2rem;margin-bottom:1rem;color:var(--gray-700)">Senators</h3>
        <div id="senators-grid" class="senator-grid"></div>
    </div>

    <div id="resources" class="tab-content">
        <h2>ASUCI Resources</h2>
        <div class="section">
            <h3>Governing Documents</h3>
            <div class="links-grid">
                <a href="https://asuci.uci.edu/wp-content/uploads/2012/09/constitution.pdf" target="_blank" class="link-card">
                    <h4>ASUCI Constitution</h4>
                    <p>The foundational governing document</p>
                </a>
                <a href="http://asuci.uci.edu/wp-content/uploads/2025/11/ASUCI-Operational-Policies-and-Procedures-as-of-October-15-2025-R61-15.pdf" target="_blank" class="link-card">
                    <h4>Operational Policies</h4>
                    <p>Policies and procedures manual</p>
                </a>
                <a href="https://docs.google.com/document/d/1hOXFx2yhf3Ox-C2C-PQkWsUJnWJ7s8dE61-e_xTcS1E/edit" target="_blank" class="link-card">
                    <h4>ASUCI By-Laws</h4>
                    <p>Supplementary rules and regulations</p>
                </a>
                <a href="https://docs.google.com/document/d/1iqSRs4cGUwwjNWBko5-mwlAL3TP_Mz69TNpEGJoSGjQ/edit" target="_blank" class="link-card">
                    <h4>Ethics Code</h4>
                    <p>Standards of conduct for members</p>
                </a>
            </div>
        </div>
        <div class="section">
            <h3>Senate Resources</h3>
            <div class="links-grid">
                <a href="https://asuci.uci.edu/senate/committees/" target="_blank" class="link-card">
                    <h4>Committees</h4>
                    <p>Senate standing committees</p>
                </a>
                <a href="https://asuci.uci.edu/senate/legislation/" target="_blank" class="link-card">
                    <h4>Legislation</h4>
                    <p>Resolutions and bills archive</p>
                </a>
                <a href="https://docs.google.com/document/d/1QZuu0QOWiJTTVPMoGL4BjbMqZuSR21dpR5zoWMLIaEc/edit" target="_blank" class="link-card">
                    <h4>Peter's Procedures</h4>
                    <p>Parliamentary procedure guide</p>
                </a>
                <a href="https://asuci.uci.edu/senate/" target="_blank" class="link-card">
                    <h4>Senate Home</h4>
                    <p>Official Senate webpage</p>
                </a>
            </div>
        </div>
        <div class="alert alert-info" style="margin-top:2rem">
            <strong>Regular Meetings:</strong> Tuesdays and Thursdays at 5:00 PM<br>
            <strong>Location:</strong> Balboa Island B, 4th Floor, Student Center (G244)<br>
            <strong>Zoom:</strong> <a href="https://uci.zoom.us/j/97062458514" target="_blank" style="color:var(--primary)">uci.zoom.us/j/97062458514</a><br>
            <strong>Livestreams:</strong> <a href="https://www.facebook.com/pg/associatedstudentsuci/videos/" target="_blank" style="color:var(--primary)">Facebook Videos</a><br><br>
            <em>Tip: Check the <a href="https://asuci.uci.edu/senate/agendas/" target="_blank" style="color:var(--primary)">Current Agenda</a> before meetings to see what legislation will be discussed!</em>
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
            const day = now.getDay();
            const hour = now.getHours();
            let daysUntilTue = (2 - day + 7) % 7;
            let daysUntilThu = (4 - day + 7) % 7;
            if (daysUntilTue === 0 && hour >= 17) daysUntilTue = 7;
            if (daysUntilThu === 0 && hour >= 17) daysUntilThu = 7;
            const daysUntil = Math.min(daysUntilTue, daysUntilThu);
            const nextDate = new Date(now);
            nextDate.setDate(now.getDate() + daysUntil);
            return nextDate.toLocaleDateString('en-US', {{ weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }}) + ' at 5:00 PM';
        }}

        function init() {{
            document.getElementById('next-meeting-date').textContent = getNextMeeting();

            // Recent meetings - use meeting links from website (most current data)
            const recentEl = document.getElementById('recent-meetings');
            const currentYear = Object.keys(DATA.meeting_links.agendas || {{}}).sort().reverse()[0];
            const meetings = (DATA.meeting_links.agendas[currentYear] || []).slice(0, 8);
            let recentHtml = '';

            meetings.forEach(m => {{
                const agendaUrl = m.url || 'https://www.asuci.uci.edu/senate/agendas/print/?date=' + encodeURIComponent(m.date);
                const minutesUrl = 'https://www.asuci.uci.edu/senate/minutes/print/?date=' + encodeURIComponent(m.date);

                recentHtml += '<div class="meeting-card">' +
                    '<div class="meeting-date">' + m.date + '</div>' +
                    '<div class="meeting-links">' +
                        '<a href="' + agendaUrl + '" target="_blank">Agenda</a>' +
                        '<a href="' + minutesUrl + '" target="_blank">Minutes</a>' +
                    '</div>' +
                '</div>';
            }});
            recentEl.innerHTML = recentHtml || '<p>No recent meetings found</p>';

            // Senators grid
            function renderSenators(senators, containerId) {{
                const container = document.getElementById(containerId);
                let html = '';
                senators.forEach(s => {{
                    html += '<div class="senator-card">' +
                        (s.photo ? '<img class="photo" src="' + s.photo + '" alt="' + s.name + '">' : '') +
                        '<div class="name">' + s.name + '</div>' +
                        '<div class="position">' + s.position + '</div>' +
                        (s.email ? '<div class="email"><a href="mailto:' + s.email + '">' + s.email + '</a></div>' : '') +
                    '</div>';
                }});
                container.innerHTML = html || '<p>No senators found</p>';
            }}
            renderSenators(DATA.senators.leadership || [], 'leadership-grid');
            renderSenators(DATA.senators.senators || [], 'senators-grid');

            // Meetings table - default to current year
            loadYear('25-26');
        }}

        function parseDate(dateStr) {{
            // Parse "January 22, 2026" format to timestamp for sorting
            const parsed = new Date(dateStr);
            return isNaN(parsed.getTime()) ? 0 : parsed.getTime();
        }}

        function loadYear(year) {{
            if ($.fn.DataTable.isDataTable('#meetings-table')) $('#meetings-table').DataTable().destroy();
            const meetings = DATA.meeting_links.agendas[year] || [];

            // Sort meetings reverse chronologically (newest first)
            const sortedMeetings = [...meetings].sort((a, b) => parseDate(b.date) - parseDate(a.date));

            const tbody = document.getElementById('meetings-tbody');
            let html = '';
            sortedMeetings.forEach(m => {{
                const agendaUrl = m.url || 'https://www.asuci.uci.edu/senate/agendas/print/?date=' + encodeURIComponent(m.date);
                const minutesUrl = 'https://www.asuci.uci.edu/senate/minutes/print/?date=' + encodeURIComponent(m.date);
                const timestamp = parseDate(m.date);
                html += '<tr data-sort="' + timestamp + '"><td data-order="' + timestamp + '">' + m.date + '</td><td><a href="' + agendaUrl + '" target="_blank">View Agenda</a></td><td><a href="' + minutesUrl + '" target="_blank">View Minutes</a></td></tr>';
            }});
            tbody.innerHTML = html || '<tr><td colspan="3">No meetings</td></tr>';
            if (sortedMeetings.length > 0) $('#meetings-table').DataTable({{ paging: false, order: [[0, 'desc']] }});
        }}

        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>'''

    return html


def main(quick_mode=False):
    """Main function to generate the dashboard."""
    print("=" * 60)
    print("ASUCI Dashboard Generator")
    print("=" * 60)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    # Fetch senators from website
    print("\n[*] Fetching current senators...")
    senators = fetch_senators_playwright()
    print(f"    Leadership: {len(senators.get('leadership', []))}")
    print(f"    Senators: {len(senators.get('senators', []))}")

    # Fetch meeting links
    if quick_mode:
        print("\n[*] Quick mode - skipping Playwright...")
        meeting_links = {"agendas": {}, "minutes": {}}
    else:
        print("\n[*] Fetching meeting links (Playwright)...")
        meeting_links = fetch_meeting_links_playwright()
        total = sum(len(v) for v in meeting_links.get("agendas", {}).values())
        print(f"    Agendas: {total}")

    # Compile data
    data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "senators": senators,
        "meeting_links": meeting_links,
    }

    # Generate HTML
    print("\n[*] Generating HTML...")
    html = generate_html(data)

    # Save as index.html for GitHub Pages
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
