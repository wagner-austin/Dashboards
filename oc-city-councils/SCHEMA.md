# OC City Council YAML Schema

Complete standardized schema for city council data files in `_council_data/*.yaml`.

## Full Schema

```yaml
# =============================================================================
# CITY IDENTIFICATION
# =============================================================================
city: anaheim                          # Slug (lowercase, hyphenated)
city_name: "Anaheim"                   # Display name
website: "https://www.anaheim.net"     # City main website
council_url: "https://www.anaheim.net/173/City-Council"  # Council page
last_updated: "2026-01-25"             # Last data update (YYYY-MM-DD)

# =============================================================================
# MEETING SCHEDULE
# =============================================================================
meetings:
  schedule: "1st and 3rd Tuesdays"     # Human-readable pattern
  time: "5:00 PM"                      # Meeting start time
  location:
    name: "Council Chamber"            # Room/venue name
    address: "200 S. Anaheim Blvd"     # Street address
    city_state_zip: "Anaheim, CA 92805"

  # Remote access options
  remote:
    zoom_url: null                     # Full Zoom/ZoomGov URL
    zoom_id: null                      # Meeting ID (formatted: 123-456-7890)
    zoom_passcode: null                # Passcode
    phone_numbers:                     # Dial-in numbers
      - "669-254-5252"
      - "669-216-1590"
    webex_url: null                    # WebEx if used instead of Zoom

# =============================================================================
# PORTALS & ARCHIVES
# =============================================================================
portals:
  # Meeting archives
  granicus: null                       # https://{city}.granicus.com/...
  legistar: null                       # Legistar portal URL
  agenda_center: null                  # CivicPlus AgendaCenter or similar

  # Video
  video_archive: null                  # Primary video archive
  youtube: null                        # YouTube channel/playlist
  ictv: null                           # Local cable TV archive
  live_stream: null                    # Live stream URL

  # Public participation
  ecomment: null                       # Granicus Ideas or similar
  public_comment_form: null            # Web form for comments

  # Other
  district_map: null                   # Find-your-district tool
  invite_form: null                    # Invite councilmember form

# =============================================================================
# BROADCAST / TV
# =============================================================================
broadcast:
  cable_channels:
    - provider: "Cox"
      channel: "30"
    - provider: "AT&T U-verse"
      channel: "99"
  live_stream: null                    # URL for live stream
  youtube_live: null                   # YouTube live URL

# =============================================================================
# CITY CLERK / CONTACT
# =============================================================================
clerk:
  name: null                           # Clerk name if known
  title: "City Clerk"                  # Title
  phone: "(714) 765-5166"              # Office phone
  email: "cityclerk@anaheim.net"       # Office email
  council_email: null                  # Shared council email if different

# =============================================================================
# PUBLIC COMMENT
# =============================================================================
public_comment:
  in_person: true                      # Can comment in person
  remote_live: false                   # Can comment via Zoom during meeting
  ecomment: false                      # Has eComment system
  written_email: true                  # Can email comments
  written_form: false                  # Has web form for comments
  deadline: null                       # Comment deadline (e.g., "24 hours before")
  instructions_url: null               # Link to public comment instructions

# =============================================================================
# ELECTIONS
# =============================================================================
elections:
  next_election: "2026-11-03"          # Next election date (YYYY-MM-DD)
  election_type: "general"             # general, primary, special
  seats_up:                            # Seats on ballot
    - district: "District 1"
      incumbent: "Name Here"
    - district: "District 3"
      incumbent: "Name Here"
  term_length: 4                       # Years per term
  term_limit: null                     # Max terms (null if none)
  election_system: "by-district"       # by-district, at-large, mixed

# =============================================================================
# COUNCIL COMPOSITION
# =============================================================================
council:
  size: 7                              # Total members including mayor
  districts: 6                         # Number of district seats
  at_large: 1                          # Number of at-large seats (usually mayor)
  mayor_rotation: false                # Mayor rotates among members?
  mayor_elected: true                  # Mayor directly elected?

# =============================================================================
# COUNCIL MEMBERS
# =============================================================================
members:
  - name: "Ashleigh E. Aitken"
    position: "Mayor"                  # Mayor, Vice Mayor, Mayor Pro Tem, Councilmember
    district: null                     # District number/name or null for at-large

    # Contact
    email: "aaitken@anaheim.net"
    phone: "(714) 765-5098"            # Direct line if available

    # Online presence
    city_page: "https://..."           # Official city profile page
    website: null                      # Personal/campaign website
    facebook: null
    twitter: null
    instagram: null
    linkedin: null

    # Media
    photo_url: "https://..."           # Official headshot URL

    # Biography
    bio: "Elected as the 48th mayor..." # Bio text (can be multi-line)

    # Term info
    term_start: 2022                   # Year started current term
    term_end: 2026                     # Year term ends
    first_elected: 2022                # Year first elected to this body

    # Committee assignments (optional)
    committees:
      - name: "Great Park Board"
        role: "Chair"
      - name: "OCTA"
        role: "Director"
```

## Required vs Optional Fields

### Required (must have for all cities)
```yaml
city: string
city_name: string
website: string
council_url: string
last_updated: string

members:
  - name: string
    position: string
    email: string
```

### Highly Recommended
```yaml
meetings:
  schedule: string
  time: string
  location:
    address: string

clerk:
  phone: string
  email: string

members:
  - phone: string
    city_page: string
    photo_url: string
```

### Optional (include if available)
```yaml
meetings:
  remote: {...}           # If city offers Zoom/remote

portals:
  granicus: string        # If city uses Granicus
  ecomment: string        # If eComment available

broadcast: {...}          # If meetings are broadcast

members:
  - bio: string
    term_start: int
    term_end: int
    website: string
    committees: [...]
```

## Platform-Specific Notes

### CivicPlus Cities
- Usually have AgendaCenter for agendas
- Directory.aspx pages for contacts
- May not have Granicus

### Granicus Cities
- Have full meeting archives with video
- Often have Granicus Ideas for eComment
- URL pattern: `{city}.granicus.com`

### Legistar Cities
- Meeting management through Legistar
- Different URL patterns

## Example: Minimal City

```yaml
city: villa-park
city_name: "Villa Park"
website: "https://villapark.org"
council_url: "https://villapark.org/council-and-committees/city-council"
last_updated: "2026-01-25"

meetings:
  schedule: "2nd and 4th Tuesdays"
  time: "6:00 PM"
  location:
    address: "17855 Santiago Blvd, Villa Park, CA 92861"

clerk:
  phone: "(714) 998-1500"
  email: "cityclerk@villapark.org"

members:
  - name: "Jordan Wu"
    position: "Mayor"
    email: "jwu@villapark.org"
    phone: "(714) 998-1500"
  # ...
```

## Example: Full-Featured City

```yaml
city: irvine
city_name: "Irvine"
website: "https://www.cityofirvine.org"
council_url: "https://www.cityofirvine.org/city-council"
last_updated: "2026-01-25"

meetings:
  schedule: "2nd and 4th Tuesdays"
  time: "4:00 PM"
  location:
    name: "City Council Chamber"
    address: "1 Civic Center Plaza"
    city_state_zip: "Irvine, CA 92606"
  remote:
    zoom_url: "https://www.zoomgov.com/j/1600434844"
    zoom_id: "160-043-4844"
    zoom_passcode: "272906"
    phone_numbers:
      - "669-254-5252"
      - "669-216-1590"

portals:
  granicus: "https://irvine.granicus.com/ViewPublisher.php?view_id=68"
  ecomment: "https://irvine.granicusideas.com/meetings"
  video_archive: "https://irvine.granicus.com/ViewPublisher.php?view_id=68"
  ictv: "https://legacy.cityofirvine.org/cityhall/citymanager/pio/ictv/default.asp"
  district_map: "https://cityofirvine.maps.arcgis.com/apps/dashboards/99a9ff74e04f433ab1f49d015ba1a2cb"
  invite_form: "https://irvineca.seamlessdocs.com/f/citycouncilinvitation"

broadcast:
  cable_channels:
    - provider: "Cox"
      channel: "30"
    - provider: "AT&T U-verse"
      channel: "99"

clerk:
  phone: "(949) 724-6205"
  email: "irvinecitycouncil@cityofirvine.org"

public_comment:
  in_person: true
  remote_live: true
  ecomment: true
  written_email: true

elections:
  next_election: "2026-11-03"
  term_length: 4
  election_system: "mixed"

council:
  size: 7
  districts: 6
  at_large: 1
  mayor_elected: true

members:
  - name: "Larry Agran"
    position: "Mayor"
    district: "At-Large"
    email: "LarryAgran@cityofirvine.org"
    phone: "(949) 724-6000"
    city_page: "https://www.cityofirvine.org/city-council/mayor-larry-agran"
    website: "https://mayorlarryagran.org"
    photo_url: "https://www.cityofirvine.org/sites/default/files/city-files/PIO/Images/Website/Ziba%20Photo%20Video%20-%20Mayor%20Larry%20Agran%203.jpg"
    bio: "First served on Irvine City Council 1978-1990, including six years as Mayor. Elected Mayor in 2024 for his eighth nonconsecutive term."
    term_start: 2024
    term_end: 2028
    first_elected: 1978
  # ...
```

## Migration Notes

Current YAML files have:
- city, last_updated, next_election, seats_up, members

Need to add:
- city_name, website, council_url
- meetings (schedule, time, location, remote)
- portals (granicus, ecomment, etc.)
- clerk (phone, email)
- public_comment options
- council composition info
- Enhanced member fields (city_page, photo_url, bio, term dates)
