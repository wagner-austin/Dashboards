# YAML Template for City Data

Use this template when creating or updating city YAML files. All fields should be present even if null.

```yaml
# =============================================================================
# BASIC INFO
# =============================================================================
city: city-slug                      # lowercase, hyphens (e.g., aliso-viejo)
city_name: Full City Name            # Display name (e.g., Aliso Viejo)
website: https://...                 # Official city website
council_url: https://...             # City council page
last_updated: 'YYYY-MM-DD'           # Date of last verification
email: info@city.gov                 # City general email
phone: (XXX) XXX-XXXX                # City main phone
instagram:                           # City Instagram handle (null if none)

# =============================================================================
# COUNCIL MEMBERS
# =============================================================================
members:
- name: Full Name                    # As appears on city website
  position: Mayor | Mayor Pro Tem | Councilmember
  district: District N | At-Large    # District assignment
  email: email@city.gov
  phone: (XXX) XXX-XXXX
  city_page: https://...             # Individual bio page
  photo_url: https://...             # Official photo
  bio: |                             # Multi-line biography
    Biography text here...
  term_start: YYYY                   # Year term began
  term_end: YYYY                     # Year term ends
  term_start_date: 'YYYY-MM-DD'      # Exact swearing-in date (for term limit calc)
  term_end_date: 'YYYY-MM-DD'        # Exact term end date

# =============================================================================
# MEETINGS
# =============================================================================
meetings:
  schedule: "1st and 3rd Tuesdays"   # Meeting pattern
  time: "7:00 PM"                    # Start time
  closed_session_time: "5:00 PM"     # If applicable (null if none)
  location:
    name: Council Chambers
    address: Street Address
    city_state_zip: City, CA XXXXX
  remote:                            # Remote meeting info (null if not offered)
    zoom_url: https://...
    zoom_id: "XXX XXX XXXX"
    zoom_passcode: "XXXXX"
    phone_numbers:                   # List of dial-in numbers
    - "XXX-XXX-XXXX"

# =============================================================================
# PORTALS & URLS
# =============================================================================
portals:
  agendas: https://...               # Agenda portal
  live_stream: https://...           # Live meeting stream
  video_archive: https://...         # Past meeting videos
  youtube: https://...               # YouTube channel if different
  document_center: https://...       # City document repository
  municipal_code: https://...        # Online municipal code
  ecomment: https://...              # eComment portal if applicable

# =============================================================================
# BROADCAST
# =============================================================================
broadcast:
  cable_channels:
  - provider: Provider Name
    channel: 'XX'
  live_stream: https://...

# =============================================================================
# CITY CLERK
# =============================================================================
clerk:
  name: Clerk Name
  title: City Clerk
  phone: (XXX) XXX-XXXX
  fax: (XXX) XXX-XXXX                # If applicable
  email: clerk@city.gov
  address: Full mailing address

# =============================================================================
# PUBLIC COMMENT
# =============================================================================
public_comment:
  in_person: true | false
  remote_live: true | false          # Can speak via Zoom/phone
  ecomment: true | false             # Written comments via portal
  written_email: true | false        # Email comments accepted
  time_limit: "3 minutes per speaker"
  deadline: "X hours prior to meeting"
  email: publiccomment@city.gov      # Email for written comments
  notes: |                           # Any special procedures
    Additional notes here...

# =============================================================================
# COUNCIL COMPOSITION
# =============================================================================
council:
  size: 5 | 7                        # Total council members
  districts: N                       # Number of district seats
  at_large: N                        # Number of at-large seats (including mayor if applicable)
  mayor_elected: true | false        # Separately elected mayor?
  expanded_date: null | "YYYY-MM-DD" # If council size changed
  transition_date: null | "YYYY-MM-DD" # If election system changed
  notes: null | "Explanation"        # Any special circumstances

# =============================================================================
# ELECTIONS
# =============================================================================
elections:
  next_election: 'YYYY-MM-DD'        # Next election date
  election_system: by-district | at-large | mixed | by-ward
  term_length: 4                     # Years per term (usually 4)
  mayor_term_length: 2 | null        # If mayor has different term (e.g., Costa Mesa, Santa Ana)

  # Seats up in next election
  seats_up:
    - district: "District 1" | "Mayor" | "At-Large"
      incumbent: "Current Holder Name"
      term_length: 4                 # If different from default

  # ----- TERM LIMITS (ALL FIELDS REQUIRED) -----
  term_limit: N | null               # Max consecutive terms/years
  term_limit_type: terms | years | null  # What the number represents
  term_limit_cooldown: N | null      # Break period before eligible again
  term_limit_cooldown_unit: cycles | years | null  # What cooldown represents
  term_limit_effective: "YYYY-MM-DD" | null  # When limit took effect
  term_limit_notes: "Explanation" | null     # Human-readable with ordinance ref
  term_limit_source: https://... | null      # Municipal code URL

  # ----- ELECTION CYCLE PATTERN -----
  cycle_pattern:
    group_a:
      years: "2024, 2028, 2032..."
      seats: ["District 1", "District 2"]
    group_b:
      years: "2026, 2030, 2034..."
      seats: ["District 3", "District 4"]
    notes: null | "Mayor up every election due to 2-year term"

  # ----- CANDIDATE FILING INFO -----
  nomination_period: "Month DD - Month DD, YYYY" | null
  candidate_info:
    contact_email: clerk@city.gov
    contact_phone: "(XXX) XXX-XXXX"
    location: "Filing address"
    candidate_guide: https://...     # If available
  contribution_limit: "$X,XXX (YYYY-YY)" | null

  # ----- DATA SOURCES -----
  results_source: https://ocvote.gov/results
  past_results: https://...          # City's election history page
  candidate_resources: https://...   # City's candidate info page
  districting_info: https://...      # District maps
  fppc_filings: https://...          # Campaign finance
  source: https://...                # Primary source for this section
  transition_note: null | "Explanation of system change"

  # ----- ELECTION HISTORY -----
  history:
    - year: 2024
      type: by-district | at-large | general
      seats: ["District 1", "District 2"]
      nomination_period: "Month DD - Month DD, YYYY"
      notes: "Any special circumstances"
      certified: "YYYY-MM-DD"        # Certification date
      resolution: "YYYY-NN"          # City resolution number
      results_url: https://...       # Link to official results
      source: https://...            # Link to certification doc

      # Winners (from city records + OC Registrar for votes)
      winners:
        - district: "District 1"
          winner: "Winner Name"
          votes: NNNNN               # From OC Registrar SOV
          runner_up: "Second Place"  # Optional
          runner_up_votes: NNNN      # Optional
          notes: "re-elected"        # Optional

      # Full candidate list (from OC Registrar)
      candidates:
        - district: "District 1"
          candidates:
            - name: "Winner Name"
              votes: NNNNN
              outcome: won
            - name: "Runner Up"
              votes: NNNN
              outcome: lost
            - name: "Third Place"
              votes: NNN
              outcome: lost
```

---

## Field Notes

### Term Limits

**Why exact dates matter:**
Term limits often apply only to members "elected on or after" a specific date. For example, Aliso Viejo's limit applies to terms starting on/after Nov 8, 2022. A member elected Nov 8, 2022 (sworn in Dec 2022) IS subject to limits. A member elected in 2020 (already serving) is NOT.

The `term_start_date` field captures the exact swearing-in date for accurate term limit calculation. If not provided, the system defaults to December 1st of the `term_start` year.

**term_limit_type**:
- `terms` = Limit is number of consecutive terms (most common)
- `years` = Limit is number of consecutive years (Anaheim uses this)

**term_limit_cooldown_unit**:
- `cycles` = Number of election cycles to sit out
- `years` = Number of years to sit out

### Election History

**type**:
- `by-district` = District-based election
- `at-large` = Citywide election
- `general` = Default if not specified

**candidates** section:
- Sourced from OC Registrar Statement of Vote
- Includes ALL candidates, not just winners
- `outcome: won` or `outcome: lost`

### Unopposed Races

When a candidate runs unopposed (per CA Elections Code § 10229):
```yaml
winners:
  - district: "District 3"
    winner: "Unopposed Winner"
    votes: null                      # No election held
    notes: "Appointed - unopposed per EC § 10229"
```

---

## Common Mistakes to Avoid

1. **Don't leave term limit fields undefined** - use explicit `null`
2. **Don't assume term limits are in "terms"** - check municipal code
3. **Don't mix up cooldown units** - cycles vs years
4. **Don't forget to add vote counts** - run enrichment script
5. **Don't delete existing data** - enrichment adds, doesn't replace

---

*Last updated: 2026-01-29*
