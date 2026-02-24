# Flock Safety Built-In Audit Features

Reference documentation proving the existence of audit and transparency features within the Flock Safety platform. These features are available to all subscribing agencies and produce exportable records. Irvine PD cannot credibly claim these records do not exist or are inaccessible.

---

## Organization Audit

- **Location:** Insights tab within the Flock web portal
- **Definition:** A log of all searches conducted by users *within* the agency. This captures internal search activity only.
- **Export fields:**
  - Name (user who performed the search)
  - Total Networks Searched
  - Time Frame
  - License Plate
  - Case #
  - Filters
  - Reason
  - Offense Type
  - Search Date/Time
- **Export format:** CSV or XLSX
- **Source:** Flock Safety blog, "Offense Type Dropdown: A Simpler, More Accurate Audit"
  - https://www.flocksafety.com/blog/offense-type-dropdown-a-simpler-more-accurate-audit

---

## Network Audit

- **Location:** Insights tab within the Flock web portal
- **Definition:** A log of searches performed against the organization's network by **ANY agency** in the Flock System -- not just the owning agency. This is the inverse of the Organization Audit: it shows who is looking at *your* data, regardless of which agency they belong to.
- **Export fields:**
  - Name (user who performed the search)
  - Org Name (the agency that user belongs to)
  - Total Networks Searched
  - Total Devices Searched
  - Time Frame
  - License Plate
  - Case #
  - Filters
  - Reason
  - Search Date/Time
- **Export format:** CSV or XLSX
- **THIS IS THE KEY RECORD for identifying federal agency access.** If CBP, HSI, or any other federal entity searched Irvine's Flock network, it will appear here with the searching agency's Org Name.
- **Volume precedent:** Largo PD (FL) estimated approximately 600,000+ entries per month in their Network Audit, which they cited as a basis for redaction burden and fee charges in response to public records requests.

---

## Hot List Action Log

- **Definition:** A log of all create, update, and delete actions performed on hot list entries within the agency's Flock account.
- **Name note:** "Hot List Action Log" is a descriptive term used in CPRA requests, not necessarily the exact Flock UI label. The underlying export capability is verified real.
- **Verified export fields** (from Riverside County SO CPRA C001586):
  - Timestamp (Excel serial date format)
  - User (who performed the action)
  - Event Type (create, update, delete)
  - Entity Type (e.g., "Custom Hotlist Entry", "customHotlist")
  - Entity Details (free-text blob containing sub-fields: hotlist name, license plate, state, reason, case number, expiry date, audience/roles for hotlist-level entries)
  - Event Id (present in original Flock export but stripped from the public release)
- **Precedent:** Riverside County Sheriff's Office (CA) produced this export in response to CPRA request C001586. The export contained **3,753 entries** covering a 30-day period, delivered as an XLSX file. Publicly available at: https://cdn.muckrock.com/foia_files/2025/08/23/CPRA_C001586_Hotlist.xlsx

---

## Network Share Settings

- **Definition:** The configuration screens showing:
  - **"Networks I'm sharing"** -- which agencies Irvine PD has granted access to its camera network
  - **"Networks shared with me"** -- which agencies have granted Irvine PD access to their camera networks
  - Hot list sharing configuration between agencies
- **Relevance:** This is the source of the A1-A4 data already obtained in this investigation (the network sharing topology between Irvine PD and other agencies, including federal entities).

---

## National Lookup / Statewide Search

- **Definition:** A pilot program that allowed participating agencies to search across **all** Flock camera networks nationally, bypassing the normal bilateral network-sharing agreements.
- **Impact:** This feature allowed federal agencies such as CBP and HSI to access local agency camera data **without explicit sharing agreements** being in place. An agency did not need to appear in Irvine PD's "Networks I'm sharing" list to have searched Irvine's data through this pathway.
- **Status:** Paused by Flock Safety in **October 2025** following reporting by the University of Washington Center for Human Rights that documented how the feature was being used for immigration enforcement.
- **Source:** SeaTac Blog, "Back Door Loophole Closed for SeaTac's Flock Cameras Amid Growing Concern of Immigration Enforcement" (October 29, 2025)
  - https://seatacblog.com/2025/10/29/back-door-loophole-closed-for-seatacs-flock-cameras-amid-growing-concern-of-immigration-enforcement/

---

## Transparency Portal

- **Definition:** A public-facing portal that provides automated exports of search audit data. Designed to allow agencies to demonstrate compliance and transparency without requiring manual CPRA/FOIA processing.
- **Agency control:** Agencies configure which fields are included in the public-facing exports. This means an agency can selectively limit what the public sees, but the underlying data still exists in the full Organization and Network Audit logs.
- **Source:** Flock Safety blog, "Policy Pulse: Transparency, Control, and the Path Forward"
  - https://www.flocksafety.com/blog/policy-pulse-transparency-control-and-the-path-forward

---

## Offense Type Dropdown (Newer Feature)

- **Definition:** A required field added to the Flock search interface that forces users to select an offense type from a NIBRS-based (National Incident-Based Reporting System) dropdown before executing any search.
- **Behavior:**
  - The selected offense type is recorded in both the Organization Audit and Network Audit logs.
  - If the user selects **"Other"** as the offense type, the **Search Reason** field becomes mandatory -- the user must type a free-text justification before the search will execute.
- **Significance:** This feature eliminates the excuse that search purpose was not tracked. Every search performed after this feature's deployment has a categorized offense type attached to it.

---

## Precedent: Agencies That Successfully Provided These Exports

The following agencies have produced Flock audit exports in response to public records requests, proving these records are accessible and exportable:

| Agency | State | Format | Audit Type | Period | Volume | Source |
|---|---|---|---|---|---|---|
| Aurora PD | IL | 18 XLSX files | Organization Audit + Network Audit | Jun 2025 - Feb 2026 | Multiple files | MuckRock #203951 |
| Lodi PD | CA | XLSX | Organization Audit only | 30 days | Single file | MuckRock #173098 |
| Spokane County | WA | CSV | Network Audit | Jan - Jun 2025 | 2,000,000+ records | RANGE Media |
| Riverside County SO | CA | XLSX | Hot List Action Log | 30 days | 3,753 entries | CPRA C001586 |

**Note on Lodi PD:** Their export covered only 30 days, consistent with Flock's reported 30-day data purge cycle for certain audit logs. This makes timely records requests critical -- delayed requests may result in permanent data loss.

---

## Agencies That Pushed Back (and Their Arguments)

These agencies resisted producing Flock audit records. Their arguments are documented here to anticipate and counter similar objections from Irvine PD:

### Largo PD (FL)
- **Argument:** Cited the redaction burden created by approximately 600,000 entries per month in the Network Audit. Charged fees for processing.
- **Outcome:** Eventually cancelled their Flock contract (though the cancellation may have been motivated by factors beyond the records dispute).
- **Counter:** The volume confirms the records exist and are exportable. Redaction burden is a processing argument, not a basis for claiming the records do not exist.

### Palo Alto PD (CA)
- **Argument:** Cited California Government Code section 7923.600 (investigative records exemption) to refuse production. Directed the requester to the Transparency Portal instead.
- **Counter:** Section 7923.600 exempts records of investigations, not system-generated audit logs of platform usage. The Transparency Portal is agency-controlled and may omit fields present in the full audit exports. The full Organization and Network Audit exports remain producible records.
