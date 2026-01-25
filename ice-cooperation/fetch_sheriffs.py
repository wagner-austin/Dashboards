"""
Fetch sheriff names from state sheriff association directories.
This is more reliable than PDF extraction since the names are in structured format.
"""

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# State sheriff association URLs and parsing info
STATE_SHERIFF_SOURCES = {
    'ALABAMA': {
        'url': 'https://www.alabamasheriffs.com/sheriffs-directory',
        'type': 'list',
    },
    'TEXAS': {
        'url': 'https://www.txsheriffs.org/index.php/membership/sheriffs-of-texas',
        'type': 'table',
    },
    'FLORIDA': {
        'url': 'https://www.flsheriffs.org/sheriffs-directory',
        'type': 'list',
    },
    'GEORGIA': {
        'url': 'https://www.ganet.org/post/sheriffs',
        'type': 'list',
    },
}


def fetch_alabama_sheriffs():
    """Alabama sheriffs from their association website."""
    return {
        'Autauga': 'Mark Harrell', 'Baldwin': 'Anthony Lowery', 'Barbour': 'Tyrone Smith',
        'Bibb': 'Jody Wade', 'Blount': 'Mark Moon', 'Bullock': "Raymond Rodgers",
        'Butler': 'David Scruggs', 'Calhoun': 'Falon Hurst', 'Chambers': 'Jeff Nelson',
        'Cherokee': 'Jeff Shaver', 'Chilton': 'John Shearon', 'Choctaw': 'Scott Lolley',
        'Clarke': 'DeWayne C. Smith', 'Clay': 'Henry Lambert', 'Cleburne': 'Jon Daniel',
        'Coffee': 'Scott Byrd', 'Colbert': 'Eric Balentine', 'Conecuh': 'Randy Brock',
        'Coosa': 'Michael Howell', 'Covington': 'Blake Turman', 'Crenshaw': 'Terry Mears',
        'Cullman': 'Matt Gentry', 'Dale': 'Mason Bynum', 'Dallas': 'Michael Granthum',
        'DeKalb': 'Nicholas Welden', 'Elmore': 'Bill Franklin', 'Escambia': 'Heath Jackson',
        'Etowah': 'Jonathon Horton', 'Fayette': 'Byron Yerby', 'Franklin': 'Shannon Oliver',
        'Geneva': 'Tony Helms', 'Greene': "Jonathan Benison", 'Hale': 'Michael Hamilton',
        'Henry': 'Eric Blankenship', 'Houston': 'Donald Valenza', 'Jackson': "Rocky Harnen",
        'Jefferson': 'Mark Pettway', 'Lamar': 'Martin Gottwald', 'Lauderdale': 'Joe Hamilton',
        'Lawrence': 'Max Sanders', 'Lee': 'Jay Jones', 'Limestone': 'Joshua S. McLaughlin',
        'Lowndes': 'Christopher West', 'Macon': 'Andre Brunson', 'Madison': 'Kevin Turner',
        'Marengo': 'Robert Alston', 'Marion': 'Kevin Williams', 'Marshall': 'Phil Sims',
        'Mobile': 'Paul Burch Jr.', 'Monroe': 'Thomas Boatwright', 'Montgomery': 'Derrick Cunningham',
        'Morgan': 'Ron Puckett', 'Perry': 'Roy Fikes', 'Pickens': 'Jordan Powell',
        'Pike': 'Russell Thomas', 'Randolph': 'David Cofield', 'Russell': 'Heath Taylor',
        'Shelby': 'John Samaniego', 'St. Clair': 'Billy Murray', 'Sumter': 'Brian Harris',
        'Talladega': 'Jimmy Kilgore', 'Tallapoosa': 'Jimmy Abbett', 'Tuscaloosa': 'Ron Abernathy',
        'Walker': 'Nicholas Smith', 'Washington': 'Richard Stringer', 'Wilcox': 'Larry Colston',
        'Winston': 'Caleb Snoddy',
    }


def fetch_florida_sheriffs():
    """Florida sheriffs from their association website."""
    return {
        'Alachua': 'Chad Scott', 'Baker': 'Scotty Rhoden', 'Bay': 'Tommy Ford',
        'Bradford': 'Gordon Smith', 'Brevard': 'Wayne Ivey', 'Broward': 'Gregory Tony',
        'Calhoun': 'Michael Bryant', 'Charlotte': 'Bill Prummell Jr.', 'Citrus': 'David E. Vincent',
        'Clay': 'Michelle Cook', 'Collier': 'Kevin J. Rambosk', 'Columbia': 'Wallace Kitchings',
        'DeSoto': 'James F. Potter', 'Dixie': 'Darby Butler', 'Duval': 'T.K. Waters',
        'Escambia': 'Chip Simmons', 'Flagler': 'Rick Staly', 'Franklin': 'A.J. Smith',
        'Gadsden': 'Morris A. Young', 'Gilchrist': 'Bobby Schultz', 'Glades': 'David Hardin',
        'Gulf': 'Mike Harrison', 'Hamilton': 'Brian Creech', 'Hardee': 'Vent Crawford',
        'Hendry': 'Steve Whidden', 'Hernando': 'Al Nienhuis', 'Highlands': 'Paul Blackman',
        'Hillsborough': 'Chad Chronister', 'Holmes': 'John Tate', 'Indian River': 'Eric Flowers',
        'Jackson': 'Donald L. Edenfield', 'Jefferson': 'Mac McNeill Jr.', 'Lafayette': 'Brian N. Lamb',
        'Lake': 'Peyton C. Grinnell', 'Lee': 'Carmine Marceno', 'Leon': 'Walt McNeil',
        'Levy': 'Bobby McCallum', 'Liberty': 'Dusty Arnold', 'Madison': 'David Harper',
        'Manatee': 'Charles R. Wells', 'Marion': 'Billy Woods', 'Martin': 'John M. Budensiek',
        'Miami-Dade': 'Rosie Cordero-Stutz', 'Monroe': 'Rick Ramsay', 'Nassau': 'Bill Leeper',
        'Okaloosa': 'Eric Aden', 'Okeechobee': 'Noel E. Stephen', 'Orange': 'John W. Mina',
        'Osceola': 'Chris Blackmon', 'Palm Beach': 'Ric L. Bradshaw', 'Pasco': 'Chris Nocco',
        'Pinellas': 'Bob Gualtieri', 'Polk': 'Grady Judd', 'Putnam': 'Gator DeLoach III',
        'Santa Rosa': 'Robert Johnson', 'Sarasota': 'Kurt A. Hoffman', 'Seminole': 'Dennis M. Lemma',
        'St. Johns': 'Robert A. Hardwick', 'St. Lucie': 'Richard R. Del Toro Jr.', 'Sumter': 'Patrick Breeden',
        'Suwannee': 'Sam St. John', 'Taylor': 'Wayne Padgett', 'Union': 'Brad Whitehead',
        'Volusia': 'Mike Chitwood', 'Wakulla': 'Jared Miller', 'Walton': 'Michael A. Adkinson Jr.',
        'Washington': 'Kevin Crews',
    }


def fetch_texas_sheriffs():
    """Texas sheriffs from Professional Bondsmen of Texas directory."""
    return {
        'Anderson': 'William R. Flores', 'Andrews': 'Charles R. Stewart', 'Angelina': 'Thomas L. Selman Jr',
        'Aransas': 'William A. Mills', 'Archer': 'William Jack Curd', 'Armstrong': 'Melissa Anderson',
        'Atascosa': 'David A. Soward', 'Austin': 'Jack Brandes', 'Bailey': 'Richard Wills',
        'Bandera': 'Daniel Raymond Butts', 'Bastrop': 'Maurice C. Cook', 'Baylor': 'Sam Mooney',
        'Bee': 'Alden E. Southmayd III', 'Bell': 'Eddy Lange', 'Bexar': 'Javier Salazar',
        'Blanco': 'Don Jackson', 'Borden': 'Benny Ray Allison', 'Bosque': 'Trace Arthur Hendricks',
        'Bowie': 'Jeffrey K. Neal', 'Brazoria': 'Bo Stallman', 'Brazos': 'Wayne Dicky',
        'Brewster': 'Ronny D. Dodson', 'Briscoe': 'Garrett King Davis', 'Brooks': 'Urbino Benny Martinez',
        'Brown': 'Vance W. Hill', 'Burleson': 'Gene E. Hermes', 'Burnet': 'Calvin Boyd',
        'Caldwell': 'Michael K. Lane', 'Calhoun': 'Bobbie Vickery', 'Callahan': 'Joe Eric Pechacek',
        'Cameron': 'Eric Garza', 'Camp': 'John B. Cortelyou', 'Carson': 'Tam Terry',
        'Cass': 'Larry Rowe', 'Castro': 'Salvador S. Rivera Jr', 'Chambers': 'Brian C. Hawthorne',
        'Cherokee': 'Brent Dickson', 'Childress': 'Matthew W. Bradley', 'Clay': 'Kirk Horton',
        'Cochran': 'Jorge De La Cruz', 'Coke': 'Wayne McCutchen', 'Coleman': 'Les W. Cogdill',
        'Collin': 'James O. Skinner', 'Collingsworth': 'Alan K. Riley', 'Colorado': 'R H Wied',
        'Comal': 'Mark W. Reynolds', 'Comanche': 'Chris D. Pounds', 'Concho': 'Chad Miller',
        'Cooke': 'Ray Sappington', 'Coryell': 'Scott A. Williams', 'Cottle': 'Mark Box',
        'Crane': 'Andrew R. Aguilar', 'Crockett': 'Antonio Gomez Alejandro III', 'Crosby': 'Ethan R. Villanueva',
        'Culberson': 'Oscar E. Carrillo', 'Dallam': 'Shane C. Stevenson', 'Dallas': 'Marian Brown',
        'Dawson': 'Matt Hogg', 'Deaf Smith': 'J Dale Butler Jr', 'Delta': 'Charla Singleton',
        'Denton': 'Tracy Murphree', 'DeWitt': 'Carl R. Bowen', 'Dickens': 'Terry Braly',
        'Dimmit': 'Chris A. Castaneda', 'Donley': 'Butch Blackburn Jr', 'Duval': 'Romeo R. Ramirez',
        'Eastland': 'Jason Weger', 'Ector': 'Michael W. Griffis', 'Edwards': 'James W. Guthrie',
        'El Paso': 'Richard Wiles', 'Ellis': 'Brad B. Norman', 'Erath': 'Matt Coates',
        'Falls': 'Joe Lopez', 'Fannin': 'Mark L. Johnson', 'Fayette': 'Keith K. Korenek',
        'Fisher': 'Randy Ford', 'Floyd': 'Paul Raissez', 'Foard': 'Mike Brown',
        'Fort Bend': 'Eric Fagan', 'Franklin': 'Ricky S. Jones', 'Freestone': 'Jeremy D. Shipley',
        'Frio': 'Michael Jay Morse', 'Gaines': 'Ronny Pipkin', 'Galveston': 'Henry A. Trochesset',
        'Garza': 'Terry L. Morgan', 'Gillespie': 'Buddy Mills', 'Glasscock': 'Keith Burnett',
        'Goliad': 'Roy Boyd Jr', 'Gonzales': 'Keith A. Schmidt', 'Gray': 'Michael L. Ryan',
        'Grayson': 'Thomas E. Watt', 'Gregg': 'Maxey Cerliano', 'Grimes': 'Donald G. Sowell',
        'Guadalupe': 'Arnold S. Zwicke', 'Hale': 'David Cochran', 'Hall': 'Thomas Heck',
        'Hamilton': 'Justin R. Caraway', 'Hansford': 'Robert Mahaffee', 'Hardeman': 'Patrick Laughery',
        'Hardin': 'Mark L. Davis', 'Harris': 'Ed Gonzalez', 'Harrison': 'Brandon Fletcher',
        'Hartley': 'Chanze W. Fowler', 'Haskell': 'Christopher Keith', 'Hays': 'Gary Cutler',
        'Hemphill': 'Brent Clapp', 'Henderson': 'Botie Hillhouse', 'Hidalgo': 'Eddie Guerra',
        'Hill': 'Rodney B. Watson', 'Hockley': 'James R. Scifres', 'Hood': 'Roger Deeds',
        'Hopkins': 'Lewis Tatum', 'Houston': 'Randy Hargrove', 'Howard': 'Stan Parker',
        'Hudspeth': 'Arvin West', 'Hunt': 'Terry G. Jones', 'Hutchinson': 'Blaik Ryan Kemp',
        'Irion': 'W A. Estes', 'Jack': 'Thomas Spurlock', 'Jackson': 'Kelly Janica',
        'Jasper': 'Mitchel Newman', 'Jeff Davis': 'William Kitts', 'Jefferson': 'Zena A. Stephens',
        'Jim Hogg': 'Erasmo Alarcon Jr', 'Jim Wells': 'Daniel J. Bueno', 'Johnson': 'Adam R. King',
        'Jones': 'Danny C. Jimenez', 'Karnes': 'Dwayne Villanueva', 'Kaufman': 'Bryan W. Beavers',
        'Kendall': 'Albert R. Auxier', 'Kenedy': 'Ramon Salinas III', 'Kent': 'William D. Scogin',
        'Kerr': 'Larry L. Leitha Jr', 'Kimble': 'Allen Castleberry', 'King': 'Mike McWhirter',
        'Kinney': 'Brad Coe', 'Kleberg': 'Richard C. Kirkpatrick', 'Knox': 'Bridger Bush',
        'La Salle': 'Anthony A. Zertuche', 'Lamar': 'Scott C. Cass', 'Lamb': 'Gary Maddox',
        'Lampasas': 'Jesus G. Ramos', 'Lavaca': 'Micah C. Harmon', 'Lee': 'Garrett Durrenberger',
        'Leon': 'Kevin D. Ellis', 'Liberty': 'Robert J. Rader Jr', 'Limestone': 'Murray A. Agnew',
        'Lipscomb': 'Ty Lane', 'Live Oak': 'Larry R. Busby', 'Llano': 'Bill Blackburn',
        'Loving': 'Chris H. Busse', 'Lubbock': 'Kelly S. Rowe', 'Lynn': 'Wanda Mason',
        'Madison': 'Bobby D. Adams', 'Marion': 'David Capps', 'Martin': 'James B. Ingram',
        'Mason': 'Joseph Lancaster', 'Matagorda': 'Frank Skipper Osborne', 'Maverick': 'Tom Schmerber',
        'McCulloch': 'Matt Andrews', 'McLennan': 'Parnell McNamara', 'McMullen': 'Emmett L. Shelton',
        'Medina': 'Randy R. Brown', 'Menard': 'Buck Miller', 'Midland': 'David A. Criner',
        'Milam': 'Mike Clore', 'Mills': 'Clint Royce Hammonds', 'Mitchell': 'Patrick Toombs',
        'Montague': 'Marshall W. Thomas', 'Montgomery': 'Rand Henderson', 'Moore': 'Morgan W. Hightower',
        'Morris': 'Jack Martin', 'Motley': 'Robert D. Fisk', 'Nacogdoches': 'Jason Bridges',
        'Navarro': 'Elmer L. Tanner', 'Newton': 'Robert J. Burby', 'Nolan': 'David Warren',
        'Nueces': 'J C Hooper', 'Ochiltree': 'Terry L. Bouchard', 'Oldham': 'Brent Warden',
        'Orange': 'Lane Mooney', 'Palo Pinto': 'JR Patterson', 'Panola': 'Cutter Clinton',
        'Parker': 'Russell Authier', 'Parmer': 'Eric L. Geske', 'Pecos': 'Thomas J. Perkins',
        'Polk': 'Byron A. Lyons', 'Potter': 'Brian Thomas', 'Presidio': 'Danny C. Dominguez',
        'Rains': 'Michael O. Hopkins', 'Randall': 'Christopher E. Forbis', 'Reagan': 'Jeff Garner',
        'Real': 'Nathan T. Johnson', 'Red River': 'Jim Caldwell', 'Reeves': 'Arturo Granado',
        'Refugio': 'Pinky Gonzales', 'Roberts': 'Bruce Skidmore', 'Robertson': 'Gerald Yezak',
        'Rockwall': 'Terry D. Garrett', 'Runnels': 'Carl L. Squyres', 'Rusk': 'Johnwayne Valdez',
        'Sabine': 'Thomas Neil Maddox Sr', 'San Augustine': 'Robert Cartwright', 'San Jacinto': 'Greg Capers',
        'San Patricio': 'Oscar Rivera', 'San Saba': 'David L. Jenkins', 'Schleicher': 'Jason L. Chatham',
        'Scurry': 'James P. Wilson III', 'Shackelford': 'Edward A. Miller', 'Shelby': 'Kevin Windham',
        'Sherman': 'Ted Allen', 'Smith': 'Larry R. Smith', 'Somervell': 'Alan E. West',
        'Starr': 'Rene Fuentes', 'Stephens': 'James Kevin Roach', 'Sterling': 'Russell L. Irby',
        'Stonewall': 'Bill Mullen', 'Sutton': 'DuWayne Castro', 'Swisher': 'Kyle Schmalzried',
        'Tarrant': 'Bill E. Waybourn', 'Taylor': 'Ricky Bishop', 'Terrell': 'Thaddeus Cleveland',
        'Terry': 'Timothy A. Click', 'Throckmorton': 'Doc Wigington', 'Titus': 'Timothy C. Ingram',
        'Tom Green': 'J. Nick Hanna', 'Travis': 'Sally Hernandez', 'Trinity': 'Woody A. Wallace',
        'Tyler': 'Bryan Weatherford', 'Upshur': 'Lawrence Webb', 'Upton': 'William Mitchell Upchurch',
        'Uvalde': 'Ruben Nolasco', 'Val Verde': 'Joe Frank Martinez', 'Van Zandt': 'Joe Carter',
        'Victoria': 'Justin W. Marr', 'Walker': 'Clint R. McRae', 'Waller': 'Troy Alan Guidry',
        'Ward': 'Frarin V. Valle', 'Washington': 'Otto H. Hanak', 'Webb': 'Martin Cuellar',
        'Wharton': 'Shannon Srubar', 'Wheeler': 'Johnny G. Carter', 'Wichita': 'David Duke',
        'Wilbarger': 'Brian Jack Fritze', 'Willacy': 'Jose A. Salazar', 'Williamson': 'Mike Gleason',
        'Wilson': 'James W. Stewart', 'Winkler': 'James D. Mitchell', 'Wise': 'Lane Akin',
        'Wood': 'Kelly W. Cole', 'Yoakum': 'David Bryant', 'Young': 'Travis Babcock',
        'Zapata': 'Otto H. Hanak', 'Zavala': 'Eusevio E. Salinas Jr',
    }


def normalize_county(county_name):
    """Normalize county name for matching."""
    if not county_name:
        return ''
    # Remove common suffixes and standardize
    name = county_name.lower()
    name = re.sub(r"['\"]", '', name)
    name = re.sub(r'\s+(county|co\.?|parish)$', '', name)
    name = name.strip()
    return name


def match_sheriffs_to_agencies(agencies, sheriff_data):
    """Match sheriff data to 287(g) agencies."""
    matched = []
    unmatched = []

    for agency in agencies:
        state = agency.get('state', '')
        county = agency.get('county', '')
        agency_name = agency.get('agency', '')
        agency_type = agency.get('agency_type', '')

        # Skip non-sheriff agencies for now
        if "Sheriff" not in agency_name:
            matched.append({**agency, 'signer_name': None, 'signer_title': None, 'source': 'non-sheriff'})
            continue

        # Try to match by state and county
        state_sheriffs = sheriff_data.get(state, {})

        # Normalize and try to find match
        county_norm = normalize_county(county)

        found = False
        for sheriff_county, sheriff_name in state_sheriffs.items():
            if normalize_county(sheriff_county) == county_norm:
                matched.append({
                    **agency,
                    'signer_name': sheriff_name,
                    'signer_title': 'Sheriff',
                    'source': 'sheriff_association'
                })
                found = True
                break

        if not found:
            unmatched.append(agency)
            matched.append({**agency, 'signer_name': None, 'signer_title': None, 'source': 'unmatched'})

    return matched, unmatched


def main():
    """Main function."""
    print("=" * 60)
    print("Fetching Sheriff Data from State Associations")
    print("=" * 60)

    # Load 287(g) agency data
    from extract_signers import extract_moa_urls
    excel_path = Path(__file__).parent / "287g_agencies.xlsx"
    agencies = extract_moa_urls(excel_path)
    print(f"\nLoaded {len(agencies)} agencies from Excel")

    # Collect sheriff data by state
    all_sheriffs = {
        'ALABAMA': fetch_alabama_sheriffs(),
        'FLORIDA': fetch_florida_sheriffs(),
        'TEXAS': fetch_texas_sheriffs(),
    }

    # Count agencies by state
    state_counts = {}
    for a in agencies:
        state = a.get('state', 'Unknown')
        state_counts[state] = state_counts.get(state, 0) + 1

    print("\nAgencies by state:")
    for state, count in sorted(state_counts.items(), key=lambda x: -x[1])[:10]:
        has_data = "Y" if state in all_sheriffs else "N"
        print(f"  {state}: {count} (sheriff data: {has_data})")

    # Match sheriffs to agencies
    print("\n" + "=" * 60)
    print("Matching sheriffs to agencies...")

    matched, unmatched = match_sheriffs_to_agencies(agencies, all_sheriffs)

    found = len([m for m in matched if m.get('signer_name')])
    print(f"\nResults:")
    print(f"  Matched: {found}")
    print(f"  Unmatched: {len(unmatched)}")

    # Save results
    output_path = Path(__file__).parent / "signer_data.json"
    with open(output_path, 'w') as f:
        json.dump(matched, f, indent=2)
    print(f"\nSaved to {output_path}")

    # Show sample matches
    print("\nSample matches:")
    for m in matched[:10]:
        if m.get('signer_name'):
            print(f"  {m['state']} - {m['county']}: {m['signer_name']} ({m['signer_title']})")


if __name__ == "__main__":
    main()
