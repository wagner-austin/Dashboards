"""
Generate HTML document from collected OC city council data.

Creates a single HTML page with all council member contact info,
organized by city.

Usage:
    python generate_html.py              # Generate full HTML
    python generate_html.py --summary    # Just show data summary
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def load_master_data():
    """Load the master JSON file."""
    path = Path(__file__).parent / "oc_cities_master.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def generate_html(data):
    """Generate complete HTML from data."""
    cities = data["cities"]
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Count stats
    total_cities = len(cities)
    complete_cities = len([c for c in cities.values() if c.get("status") == "complete"])
    total_members = sum(len(c.get("council_members", [])) for c in cities.values())
    members_with_email = sum(
        1 for c in cities.values()
        for m in c.get("council_members", [])
        if m.get("email")
    )

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orange County City Council Contacts</title>
    <style>
        :root {{
            --primary: #1e40af;
            --primary-light: #dbeafe;
            --accent: #f59e0b;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
            --success: #059669;
            --success-light: #d1fae5;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: var(--gray-800);
            background: var(--gray-50);
        }}
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, #1e3a8a 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        .header h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        .header .subtitle {{ opacity: 0.9; }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }}
        .stat {{
            text-align: center;
            padding: 0.5rem 1rem;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
        }}
        .stat-value {{ font-size: 1.5rem; font-weight: 700; }}
        .stat-label {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.8; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        .toc {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .toc h2 {{ font-size: 1.25rem; margin-bottom: 1rem; color: var(--primary); }}
        .toc-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 0.5rem;
        }}
        .toc-item {{
            padding: 0.5rem;
            text-decoration: none;
            color: var(--gray-700);
            border-radius: 6px;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .toc-item:hover {{ background: var(--primary-light); }}
        .toc-item .status {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }}
        .toc-item .status.complete {{ background: var(--success); }}
        .toc-item .status.pending {{ background: var(--accent); }}
        .toc-item .status.error {{ background: #dc2626; }}
        .city-section {{
            background: white;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .city-header {{
            background: var(--primary);
            color: white;
            padding: 1rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        .city-header h2 {{ font-size: 1.25rem; }}
        .city-header .links {{ display: flex; gap: 0.75rem; }}
        .city-header a {{
            color: white;
            text-decoration: none;
            font-size: 0.85rem;
            padding: 0.35rem 0.75rem;
            background: rgba(255,255,255,0.15);
            border-radius: 4px;
            transition: background 0.2s;
        }}
        .city-header a:hover {{ background: rgba(255,255,255,0.25); }}
        .city-content {{ padding: 1.5rem; }}
        .public-comment {{
            background: var(--success-light);
            border-left: 4px solid var(--success);
            padding: 1rem;
            margin-bottom: 1.5rem;
            border-radius: 0 8px 8px 0;
        }}
        .public-comment h4 {{ color: var(--success); margin-bottom: 0.25rem; }}
        .public-comment a {{ color: var(--success); }}
        .members-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
        }}
        .member-card {{
            border: 1px solid var(--gray-200);
            border-radius: 8px;
            padding: 1rem;
            transition: border-color 0.2s, box-shadow 0.2s;
        }}
        .member-card:hover {{ border-color: var(--primary); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .member-card .name {{ font-weight: 600; font-size: 1.1rem; color: var(--gray-900); }}
        .member-card .position {{ color: var(--primary); font-size: 0.9rem; }}
        .member-card .district {{ color: var(--gray-600); font-size: 0.85rem; margin-bottom: 0.75rem; }}
        .member-card .contact {{ font-size: 0.85rem; }}
        .member-card .contact a {{
            color: var(--gray-700);
            text-decoration: none;
            display: block;
            padding: 0.25rem 0;
        }}
        .member-card .contact a:hover {{ color: var(--primary); }}
        .member-card .social {{ display: flex; gap: 0.5rem; margin-top: 0.75rem; flex-wrap: wrap; }}
        .member-card .social a {{
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
            background: var(--gray-100);
            border-radius: 4px;
            color: var(--gray-700);
            text-decoration: none;
        }}
        .member-card .social a:hover {{ background: var(--primary-light); color: var(--primary); }}
        .member-card .social .instagram {{ background: linear-gradient(45deg, #f09433, #dc2743); color: white; }}
        .no-data {{
            color: var(--gray-600);
            font-style: italic;
            padding: 1rem;
            text-align: center;
            background: var(--gray-100);
            border-radius: 8px;
        }}
        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--gray-600);
            font-size: 0.85rem;
        }}
        @media (max-width: 768px) {{
            .container {{ padding: 1rem; }}
            .city-header {{ flex-direction: column; align-items: flex-start; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Orange County City Council Contacts</h1>
        <div class="subtitle">How to Contact Your Local Representatives</div>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{total_cities}</div>
                <div class="stat-label">Cities</div>
            </div>
            <div class="stat">
                <div class="stat-value">{complete_cities}</div>
                <div class="stat-label">Complete</div>
            </div>
            <div class="stat">
                <div class="stat-value">{total_members}</div>
                <div class="stat-label">Council Members</div>
            </div>
            <div class="stat">
                <div class="stat-value">{members_with_email}</div>
                <div class="stat-label">With Email</div>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="toc">
            <h2>All Orange County Cities</h2>
            <div class="toc-grid">
'''

    # Add TOC entries
    for city_name in sorted(cities.keys()):
        city = cities[city_name]
        status = city.get("status", "pending")
        status_class = "complete" if status == "complete" else ("error" if status in ["error", "blocked"] else "pending")
        html += f'''                <a href="#{city_name.replace(' ', '-').lower()}" class="toc-item">
                    <span class="status {status_class}"></span>
                    {city_name}
                </a>
'''

    html += '''            </div>
        </div>

'''

    # Add city sections
    for city_name in sorted(cities.keys()):
        city = cities[city_name]
        city_id = city_name.replace(' ', '-').lower()
        members = city.get("council_members", [])
        public_comment = city.get("public_comment")

        html += f'''        <div class="city-section" id="{city_id}">
            <div class="city-header">
                <h2>{city_name}</h2>
                <div class="links">
                    <a href="{city.get('website', '#')}" target="_blank">City Website</a>
                    <a href="{city.get('council_url', '#')}" target="_blank">City Council</a>
                </div>
            </div>
            <div class="city-content">
'''

        # Public comment info
        if public_comment:
            method = public_comment.get("method", "Public Comment")
            url = public_comment.get("url", "#")
            notes = public_comment.get("notes", "")
            html += f'''                <div class="public-comment">
                    <h4>Submit Public Comments</h4>
                    <a href="{url}" target="_blank">{method}</a>
                    {f'<div>{notes}</div>' if notes else ''}
                </div>
'''

        # Council members
        if members:
            html += '''                <div class="members-grid">
'''
            for member in members:
                name = member.get("name", "Unknown")
                position = member.get("position", "Councilmember")
                district = member.get("district", "")
                email = member.get("email")
                phone = member.get("phone")
                website = member.get("website")
                city_profile = member.get("city_profile")
                instagram = member.get("instagram")

                html += f'''                    <div class="member-card">
                        <div class="name">{name}</div>
                        <div class="position">{position}</div>
                        {f'<div class="district">{district}</div>' if district else '<div class="district">&nbsp;</div>'}
                        <div class="contact">
                            {f'<a href="mailto:{email}">{email}</a>' if email else ''}
                            {f'<a href="tel:{phone.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")}">{phone}</a>' if phone else ''}
                        </div>
                        <div class="social">
                            {f'<a href="{city_profile}" target="_blank">City Profile</a>' if city_profile else ''}
                            {f'<a href="{website}" target="_blank">Website</a>' if website else ''}
                            {f'<a href="{instagram}" target="_blank" class="instagram">Instagram</a>' if instagram else ''}
                        </div>
                    </div>
'''

            html += '''                </div>
'''
        else:
            status = city.get("status", "pending")
            if status in ["error", "blocked"]:
                msg = "Data collection blocked - needs manual research"
            elif status == "timeout":
                msg = "Website timeout - needs retry"
            else:
                msg = "Data collection pending"
            html += f'''                <div class="no-data">{msg}</div>
'''

        html += '''            </div>
        </div>

'''

    html += f'''    </div>

    <div class="footer">
        <p>Data collected: {generated_at}</p>
        <p>Data may not be complete - verify contact information on official city websites.</p>
    </div>
</body>
</html>'''

    return html


def main():
    data = load_master_data()

    if "--summary" in sys.argv:
        cities = data["cities"]
        print("\\nOrange County City Council Data Summary")
        print("=" * 50)

        statuses = {}
        for city_name, city in cities.items():
            status = city.get("status", "needs_research")
            statuses[status] = statuses.get(status, [])
            statuses[status].append(city_name)

        for status, city_list in sorted(statuses.items()):
            print(f"\\n{status.upper()} ({len(city_list)}):")
            for city in sorted(city_list):
                members = len(data["cities"][city].get("council_members", []))
                print(f"  - {city}: {members} members")

        return

    # Generate HTML
    print("Generating HTML...")
    html = generate_html(data)

    output_path = Path(__file__).parent / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
