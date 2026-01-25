"""
ICE Cooperation Dashboard Generator

Generates a dashboard showing:
1. 287(g) agreements by state/county
2. State sanctuary law status
3. Searchable/filterable table

Data sources:
- ICE 287(g) list: https://www.ice.gov/identify-and-arrest/287g
- State laws: ILRC State Map on Immigration Enforcement

Usage:
    python generate.py
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests


# State-level policy categorization based on ILRC 2024 data
# https://www.ilrc.org/state-map-immigration-enforcement-2024
STATE_POLICIES = {
    # Sanctuary states (limit cooperation)
    "OREGON": {"category": "sanctuary", "level": 5, "description": "Comprehensive sanctuary law restricting transfers to ICE"},
    "ILLINOIS": {"category": "sanctuary", "level": 5, "description": "Comprehensive sanctuary law restricting transfers to ICE"},
    "CALIFORNIA": {"category": "sanctuary", "level": 4, "description": "Broad sanctuary statute (CA Values Act)"},
    "NEW JERSEY": {"category": "sanctuary", "level": 4, "description": "Broad sanctuary statute"},
    "WASHINGTON": {"category": "sanctuary", "level": 4, "description": "Broad sanctuary statute"},
    "COLORADO": {"category": "sanctuary", "level": 3, "description": "Some protections against immigration enforcement involvement"},
    "CONNECTICUT": {"category": "sanctuary", "level": 3, "description": "Some protections against immigration enforcement involvement"},
    "MARYLAND": {"category": "sanctuary", "level": 3, "description": "Some protections against immigration enforcement involvement"},
    "VERMONT": {"category": "sanctuary", "level": 3, "description": "Some protections against immigration enforcement involvement"},
    "NEW YORK": {"category": "limited", "level": 2, "description": "Limited steps toward reducing enforcement"},
    "RHODE ISLAND": {"category": "limited", "level": 2, "description": "Limited steps toward reducing enforcement"},
    "MASSACHUSETTS": {"category": "limited", "level": 2, "description": "Some local protections, no statewide law"},

    # Anti-sanctuary states (mandate cooperation)
    "FLORIDA": {"category": "anti-sanctuary", "level": -5, "description": "Aggressive anti-sanctuary law mandating ICE cooperation"},
    "GEORGIA": {"category": "anti-sanctuary", "level": -5, "description": "Aggressive anti-sanctuary law mandating ICE cooperation"},
    "IOWA": {"category": "anti-sanctuary", "level": -5, "description": "Aggressive anti-sanctuary law with state deportation mechanism"},
    "TEXAS": {"category": "anti-sanctuary", "level": -5, "description": "Aggressive anti-sanctuary law with SB4 state deportation mechanism"},
    "WEST VIRGINIA": {"category": "anti-sanctuary", "level": -5, "description": "Aggressive anti-sanctuary law mandating ICE cooperation"},
    "ALABAMA": {"category": "anti-sanctuary", "level": -4, "description": "Broad anti-sanctuary law"},
    "TENNESSEE": {"category": "anti-sanctuary", "level": -4, "description": "Broad anti-sanctuary law"},
    "ARIZONA": {"category": "anti-sanctuary", "level": -3, "description": "Law mandating participation in immigration enforcement"},
    "ARKANSAS": {"category": "anti-sanctuary", "level": -3, "description": "Law mandating participation in immigration enforcement"},
    "IDAHO": {"category": "anti-sanctuary", "level": -3, "description": "Law mandating participation in immigration enforcement"},
    "INDIANA": {"category": "anti-sanctuary", "level": -3, "description": "Law mandating participation in immigration enforcement"},
    "KANSAS": {"category": "anti-sanctuary", "level": -3, "description": "Law mandating participation in immigration enforcement"},
    "LOUISIANA": {"category": "anti-sanctuary", "level": -3, "description": "Law mandating participation in immigration enforcement"},
    "MISSISSIPPI": {"category": "anti-sanctuary", "level": -3, "description": "Law mandating participation in immigration enforcement"},
    "MISSOURI": {"category": "anti-sanctuary", "level": -3, "description": "Law mandating participation in immigration enforcement"},
    "MONTANA": {"category": "anti-sanctuary", "level": -3, "description": "Law mandating participation in immigration enforcement"},
    "NORTH CAROLINA": {"category": "anti-sanctuary", "level": -3, "description": "Law mandating participation in immigration enforcement"},
    "NORTH DAKOTA": {"category": "anti-sanctuary", "level": -3, "description": "Law mandating participation in immigration enforcement"},
    "OKLAHOMA": {"category": "anti-sanctuary", "level": -3, "description": "Law mandating participation in immigration enforcement"},
    "SOUTH CAROLINA": {"category": "anti-sanctuary", "level": -3, "description": "Law mandating participation in immigration enforcement"},
}


def download_287g_data():
    """Download latest 287(g) data from ICE."""
    # ICE updates this regularly - we fetch the latest
    # The URL includes a date, so we need to find the current one
    # For now, use the known January 2026 URL
    url = "https://www.ice.gov/doclib/about/offices/ero/287g/participatingAgencies01232026am.xlsx"

    print(f"[*] Downloading 287(g) data from ICE...")
    response = requests.get(url)

    if response.status_code != 200:
        print(f"    Warning: Could not download fresh data (status {response.status_code})")
        print("    Using cached data if available...")
        return None

    # Save to local file
    output_path = Path(__file__).parent / "287g_agencies.xlsx"
    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"    Downloaded {len(response.content)} bytes")
    return output_path


def parse_287g_data(filepath):
    """Parse 287(g) Excel data into structured format."""
    print("[*] Parsing 287(g) data...")

    df = pd.read_excel(filepath)

    # Clean up column names
    df.columns = df.columns.str.strip()

    # Get unique agencies (some have multiple agreement types)
    agencies = []
    grouped = df.groupby(["STATE", "LAW ENFORCEMENT AGENCY", "COUNTY"])

    # Load signer data if available
    signer_lookup = {}
    signer_file = Path(__file__).parent / "signer_data.json"
    if signer_file.exists():
        with open(signer_file) as f:
            signer_data = json.load(f)
            for entry in signer_data:
                key = (entry.get('state', ''), entry.get('agency', ''), entry.get('county', ''))
                if entry.get('signer_name'):
                    signer_lookup[key] = {
                        'name': entry['signer_name'],
                        'title': entry.get('signer_title', 'Unknown')
                    }
        print(f"    Loaded {len(signer_lookup)} signer records")

    for (state, agency, county), group in grouped:
        support_types = group["SUPPORT TYPE"].str.strip().unique().tolist()
        # Get earliest signed date
        signed_dates = pd.to_datetime(group["SIGNED"])
        earliest_signed = signed_dates.min()

        # Look up signer
        state_clean = state.strip() if isinstance(state, str) else state
        agency_clean = agency.strip() if isinstance(agency, str) else agency
        county_clean = county.strip() if isinstance(county, str) else county
        signer = signer_lookup.get((state_clean, agency_clean, county_clean), {})

        agencies.append({
            "state": state_clean,
            "agency": agency_clean,
            "county": county_clean,
            "type": group["TYPE"].iloc[0].strip() if isinstance(group["TYPE"].iloc[0], str) else group["TYPE"].iloc[0],
            "support_types": support_types,
            "signed": earliest_signed.strftime("%Y-%m-%d") if pd.notna(earliest_signed) else None,
            "signer_name": signer.get('name'),
            "signer_title": signer.get('title'),
        })

    print(f"    Found {len(agencies)} unique agencies")
    return agencies


def get_state_stats(agencies):
    """Calculate statistics by state."""
    stats = {}

    for agency in agencies:
        state = agency["state"]
        if state not in stats:
            stats[state] = {
                "total_agencies": 0,
                "jail_enforcement": 0,
                "task_force": 0,
                "warrant_service": 0,
                "agencies": [],
            }

        stats[state]["total_agencies"] += 1
        stats[state]["agencies"].append(agency["agency"])

        for st in agency["support_types"]:
            if "Jail" in st:
                stats[state]["jail_enforcement"] += 1
            elif "Task" in st:
                stats[state]["task_force"] += 1
            elif "Warrant" in st:
                stats[state]["warrant_service"] += 1

    # Add policy info
    for state in stats:
        policy = STATE_POLICIES.get(state, {"category": "neutral", "level": 0, "description": "No statewide policy"})
        stats[state]["policy"] = policy

    return stats


def generate_html(agencies, state_stats):
    """Generate the HTML dashboard."""
    print("[*] Generating HTML...")

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Prepare data for JSON embedding
    data = {
        "generated_at": generated_at,
        "agencies": agencies,
        "state_stats": state_stats,
        "state_policies": STATE_POLICIES,
        "summary": {
            "total_agencies": len(agencies),
            "total_states": len(state_stats),
            "sanctuary_states": len([s for s, p in STATE_POLICIES.items() if p["category"] == "sanctuary"]),
            "anti_sanctuary_states": len([s for s, p in STATE_POLICIES.items() if p["category"] == "anti-sanctuary"]),
        }
    }

    data_json = json.dumps(data, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1024, viewport-fit=cover, user-scalable=yes">
    <title>ICE Cooperation Dashboard</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
    <style>
        :root {{
            --sanctuary: #16a34a;
            --sanctuary-light: #dcfce7;
            --anti-sanctuary: #dc2626;
            --anti-sanctuary-light: #fee2e2;
            --neutral: #6b7280;
            --neutral-light: #f3f4f6;
            --primary: #1e40af;
            --primary-light: #dbeafe;
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
            background: linear-gradient(135deg, var(--gray-800) 0%, var(--gray-900) 100%);
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
            background: var(--gray-100);
            font-size: 0.9rem;
            font-weight: 500;
            color: var(--gray-700);
            border-radius: 6px 6px 0 0;
            transition: all 0.2s;
            white-space: nowrap;
        }}
        .tab:hover {{ background: var(--primary-light); }}
        .tab.active {{
            color: var(--primary);
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
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: var(--gray-50);
            border-radius: 12px;
            padding: 1.25rem;
            border: 1px solid var(--gray-200);
        }}
        .card.danger {{ background: var(--anti-sanctuary-light); border-color: var(--anti-sanctuary); }}
        .card.success {{ background: var(--sanctuary-light); border-color: var(--sanctuary); }}
        .card h4 {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--gray-600); margin-bottom: 0.25rem; }}
        .card .value {{ font-size: 2rem; font-weight: 700; color: var(--gray-900); }}
        .card .subtext {{ font-size: 0.75rem; color: var(--gray-600); }}
        h2 {{ font-size: 1.25rem; margin-bottom: 1rem; color: var(--gray-800); border-bottom: 3px solid var(--primary); padding-bottom: 0.5rem; display: inline-block; }}
        h3 {{ font-size: 1rem; margin: 1.5rem 0 0.75rem; color: var(--gray-700); }}
        .section {{ margin-bottom: 2rem; }}
        .alert {{ padding: 1rem; border-radius: 8px; margin: 1rem 0; font-size: 0.9rem; }}
        .alert-warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; color: #92400e; }}
        .alert-info {{ background: var(--primary-light); border-left: 4px solid var(--primary); color: #1e3a8a; }}
        .state-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
        }}
        .state-card {{
            background: white;
            border: 1px solid var(--gray-200);
            border-radius: 10px;
            padding: 1rem;
            transition: all 0.2s;
        }}
        .state-card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .state-card.sanctuary {{ border-left: 4px solid var(--sanctuary); }}
        .state-card.anti-sanctuary {{ border-left: 4px solid var(--anti-sanctuary); }}
        .state-card .state-name {{ font-weight: 700; font-size: 1.1rem; margin-bottom: 0.25rem; }}
        .state-card .policy-badge {{
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .policy-badge.sanctuary {{ background: var(--sanctuary-light); color: var(--sanctuary); }}
        .policy-badge.anti-sanctuary {{ background: var(--anti-sanctuary-light); color: var(--anti-sanctuary); }}
        .policy-badge.neutral {{ background: var(--neutral-light); color: var(--neutral); }}
        .state-card .agency-count {{ font-size: 1.5rem; font-weight: 700; color: var(--gray-900); margin: 0.5rem 0; }}
        .state-card .description {{ font-size: 0.8rem; color: var(--gray-600); }}
        table.dataTable {{ font-size: 0.85rem; }}
        table.dataTable thead th {{ background: var(--gray-800); color: white; }}
        table.dataTable tbody tr:hover {{ background: var(--primary-light) !important; }}
        .refresh-time {{ font-size: 0.75rem; color: var(--gray-600); text-align: right; padding: 1rem 2rem; background: var(--gray-100); }}
        .search-box {{
            padding: 0.75rem 1rem;
            border: 2px solid var(--gray-200);
            border-radius: 8px;
            font-size: 1rem;
            width: 100%;
            max-width: 400px;
            margin-bottom: 1rem;
        }}
        .search-box:focus {{ border-color: var(--primary); outline: none; }}
        .legend {{
            display: flex;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
        }}
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }}
        .legend-color.sanctuary {{ background: var(--sanctuary); }}
        .legend-color.anti-sanctuary {{ background: var(--anti-sanctuary); }}
        .legend-color.neutral {{ background: var(--neutral); }}
        @media (max-width: 768px) {{
            .tabs {{ padding: 0.5rem 1rem; }}
            .tab {{ padding: 0.5rem 0.75rem; font-size: 0.8rem; }}
            .tab-content {{ padding: 1rem; }}
            .summary-cards {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="header-container">
        <div class="header">
            <h1>ICE Cooperation Dashboard</h1>
            <div class="subtitle">287(g) Agreements & State Sanctuary Policies</div>
        </div>
        <div class="tabs">
            <button class="tab active" onclick="showTab('overview')">Overview</button>
            <button class="tab" onclick="showTab('states')">By State</button>
            <button class="tab" onclick="showTab('agencies')">All Agencies</button>
            <button class="tab" onclick="showTab('about')">About</button>
        </div>
    </div>

    <div id="overview" class="tab-content active">
        <div class="alert alert-warning">
            <strong>Note:</strong> This dashboard shows <em>formal</em> 287(g) agreements. Many jurisdictions cooperate with ICE informally (honoring detainers, sharing info) without formal agreements.
        </div>

        <div class="summary-cards">
            <div class="card danger">
                <h4>287(g) Agencies</h4>
                <div class="value" id="total-agencies">-</div>
                <div class="subtext">Formally deputized by ICE</div>
            </div>
            <div class="card">
                <h4>States with 287(g)</h4>
                <div class="value" id="total-states">-</div>
                <div class="subtext">Out of 50 states</div>
            </div>
            <div class="card danger">
                <h4>Anti-Sanctuary States</h4>
                <div class="value" id="anti-sanctuary-count">-</div>
                <div class="subtext">Mandate ICE cooperation</div>
            </div>
            <div class="card success">
                <h4>Sanctuary States</h4>
                <div class="value" id="sanctuary-count">-</div>
                <div class="subtext">Limit ICE cooperation</div>
            </div>
        </div>

        <div class="section">
            <h2>Top States by 287(g) Agreements</h2>
            <div id="top-states" class="state-grid"></div>
        </div>

        <div class="section">
            <h2>Recent Signups</h2>
            <p style="color: var(--gray-600); margin-bottom: 1rem;">Agencies that signed 287(g) agreements in the last 90 days.</p>
            <div id="recent-signups"></div>
        </div>
    </div>

    <div id="states" class="tab-content">
        <h2>State Policies</h2>
        <div class="legend">
            <div class="legend-item"><div class="legend-color sanctuary"></div> Sanctuary (limits cooperation)</div>
            <div class="legend-item"><div class="legend-color anti-sanctuary"></div> Anti-sanctuary (mandates cooperation)</div>
            <div class="legend-item"><div class="legend-color neutral"></div> No statewide policy</div>
        </div>
        <input type="text" class="search-box" id="state-search" placeholder="Search states..." onkeyup="filterStates()">
        <div id="states-grid" class="state-grid"></div>
    </div>

    <div id="agencies" class="tab-content">
        <h2>All 287(g) Agencies</h2>
        <p style="color: var(--gray-600); margin-bottom: 1rem;">Search and filter all law enforcement agencies with formal ICE agreements.</p>
        <table id="agencies-table" class="display" style="width:100%">
            <thead>
                <tr>
                    <th>State</th>
                    <th>Agency</th>
                    <th>County</th>
                    <th>Signed By</th>
                    <th>Agreement Types</th>
                    <th>Signed</th>
                </tr>
            </thead>
            <tbody id="agencies-tbody"></tbody>
        </table>
    </div>

    <div id="about" class="tab-content">
        <h2>About This Dashboard</h2>
        <div class="section">
            <h3>What is 287(g)?</h3>
            <p>Section 287(g) of the Immigration and Nationality Act allows ICE to deputize local law enforcement to perform immigration enforcement functions. There are three types:</p>
            <ul style="margin: 1rem 0 1rem 1.5rem;">
                <li><strong>Jail Enforcement Model:</strong> Local jails screen inmates for immigration status</li>
                <li><strong>Warrant Service Officer:</strong> Local officers can serve ICE warrants</li>
                <li><strong>Task Force Model:</strong> Local officers do immigration enforcement in the field</li>
            </ul>
        </div>
        <div class="section">
            <h3>Data Sources</h3>
            <ul style="margin: 1rem 0 1rem 1.5rem;">
                <li><strong>287(g) Agreements:</strong> <a href="https://www.ice.gov/identify-and-arrest/287g" target="_blank">ICE 287(g) Program</a> (updated weekly)</li>
                <li><strong>State Policies:</strong> <a href="https://www.ilrc.org/state-map-immigration-enforcement-2024" target="_blank">ILRC State Map on Immigration Enforcement 2024</a></li>
            </ul>
        </div>
        <div class="section">
            <h3>Limitations</h3>
            <p>This dashboard only shows <em>formal</em> 287(g) agreements. Many jurisdictions cooperate with ICE without formal agreements by:</p>
            <ul style="margin: 1rem 0 1rem 1.5rem;">
                <li>Honoring ICE detainers (requests to hold people)</li>
                <li>Notifying ICE of release dates</li>
                <li>Allowing ICE access to jails</li>
                <li>Sharing information informally</li>
            </ul>
            <p>For county-level cooperation data beyond 287(g), see the <a href="https://www.ilrc.org/local-enforcement-map" target="_blank">ILRC Local Enforcement Map</a> (note: last updated 2019).</p>
        </div>
        <div class="alert alert-info">
            <strong>Open Source:</strong> This dashboard is open source. Data updates automatically via GitHub Actions.
            <a href="https://github.com/wagner-austin/Dashboards" target="_blank">View on GitHub</a>
        </div>
    </div>

    <div class="refresh-time">Data generated: {generated_at} | 287(g) data from ICE as of January 23, 2026</div>

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

        function getCategoryClass(category) {{
            if (category === 'sanctuary' || category === 'limited') return 'sanctuary';
            if (category === 'anti-sanctuary') return 'anti-sanctuary';
            return 'neutral';
        }}

        function init() {{
            // Summary cards
            document.getElementById('total-agencies').textContent = DATA.summary.total_agencies.toLocaleString();
            document.getElementById('total-states').textContent = DATA.summary.total_states;
            document.getElementById('sanctuary-count').textContent = DATA.summary.sanctuary_states;
            document.getElementById('anti-sanctuary-count').textContent = DATA.summary.anti_sanctuary_states;

            // Top states
            const topStatesEl = document.getElementById('top-states');
            const sortedStates = Object.entries(DATA.state_stats)
                .sort((a, b) => b[1].total_agencies - a[1].total_agencies)
                .slice(0, 8);

            let topHtml = '';
            sortedStates.forEach(([state, stats]) => {{
                const policy = stats.policy || {{ category: 'neutral', description: 'No statewide policy' }};
                const catClass = getCategoryClass(policy.category);
                topHtml += `<div class="state-card ${{catClass}}">
                    <div class="state-name">${{state}}</div>
                    <span class="policy-badge ${{catClass}}">${{policy.category}}</span>
                    <div class="agency-count">${{stats.total_agencies}} agencies</div>
                    <div class="description">${{policy.description}}</div>
                </div>`;
            }});
            topStatesEl.innerHTML = topHtml;

            // Recent signups (last 90 days)
            const recentEl = document.getElementById('recent-signups');
            const now = new Date();
            const ninetyDaysAgo = new Date(now - 90 * 24 * 60 * 60 * 1000);
            const recent = DATA.agencies.filter(a => {{
                if (!a.signed) return false;
                return new Date(a.signed) >= ninetyDaysAgo;
            }}).slice(0, 20);

            if (recent.length > 0) {{
                let recentHtml = '<table class="display" style="width:100%"><thead><tr><th>State</th><th>Agency</th><th>Signed</th></tr></thead><tbody>';
                recent.forEach(a => {{
                    recentHtml += `<tr><td>${{a.state}}</td><td>${{a.agency}}</td><td>${{a.signed}}</td></tr>`;
                }});
                recentHtml += '</tbody></table>';
                recentEl.innerHTML = recentHtml;
            }} else {{
                recentEl.innerHTML = '<p>No signups in the last 90 days.</p>';
            }}

            // States grid
            const statesEl = document.getElementById('states-grid');
            const allStates = Object.entries(DATA.state_stats)
                .sort((a, b) => a[0].localeCompare(b[0]));

            let statesHtml = '';
            allStates.forEach(([state, stats]) => {{
                const policy = stats.policy || {{ category: 'neutral', description: 'No statewide policy' }};
                const catClass = getCategoryClass(policy.category);
                statesHtml += `<div class="state-card ${{catClass}}" data-state="${{state.toLowerCase()}}">
                    <div class="state-name">${{state}}</div>
                    <span class="policy-badge ${{catClass}}">${{policy.category}}</span>
                    <div class="agency-count">${{stats.total_agencies}} 287(g) agencies</div>
                    <div class="description">${{policy.description}}</div>
                    <div style="font-size: 0.75rem; color: var(--gray-600); margin-top: 0.5rem;">
                        Jail: ${{stats.jail_enforcement}} | Task Force: ${{stats.task_force}} | Warrant: ${{stats.warrant_service}}
                    </div>
                </div>`;
            }});
            statesEl.innerHTML = statesHtml;

            // Agencies table
            const tbody = document.getElementById('agencies-tbody');
            let tableHtml = '';
            DATA.agencies.forEach(a => {{
                const signerDisplay = a.signer_name ?
                    `<strong>${{a.signer_name}}</strong><br><span style="font-size:0.8em;color:var(--gray-600)">${{a.signer_title || ''}}</span>` :
                    '<span style="color:var(--gray-400)">-</span>';
                tableHtml += `<tr>
                    <td>${{a.state}}</td>
                    <td>${{a.agency}}</td>
                    <td>${{a.county}}</td>
                    <td>${{signerDisplay}}</td>
                    <td>${{a.support_types.join(', ')}}</td>
                    <td>${{a.signed || '-'}}</td>
                </tr>`;
            }});
            tbody.innerHTML = tableHtml;

            $('#agencies-table').DataTable({{
                paging: true,
                pageLength: 50,
                order: [[0, 'asc'], [1, 'asc']]
            }});
        }}

        function filterStates() {{
            const query = document.getElementById('state-search').value.toLowerCase();
            document.querySelectorAll('#states-grid .state-card').forEach(card => {{
                const state = card.dataset.state;
                card.style.display = state.includes(query) ? 'block' : 'none';
            }});
        }}

        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>'''

    return html


def main():
    """Main function to generate the dashboard."""
    print("=" * 60)
    print("ICE Cooperation Dashboard Generator")
    print("=" * 60)

    # Download fresh data
    filepath = download_287g_data()
    if filepath is None:
        filepath = Path(__file__).parent / "287g_agencies.xlsx"
        if not filepath.exists():
            print("ERROR: No 287(g) data available")
            return

    # Parse data
    agencies = parse_287g_data(filepath)
    state_stats = get_state_stats(agencies)

    # Generate HTML
    html = generate_html(agencies, state_stats)

    # Save
    output_path = Path(__file__).parent / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[*] Dashboard saved to: {output_path}")
    print(f"[*] Total agencies: {len(agencies)}")
    print(f"[*] States covered: {len(state_stats)}")
    print("[*] Ready for GitHub Pages!")

    return str(output_path)


if __name__ == "__main__":
    main()
