# Federal Agency Access Pathways to Orange County ALPR Data

This document maps every documented pathway through which federal agencies -- principally ICE (ERO and HSI), CBP, and Border Patrol -- can access license plate reader data collected by Irvine PD and other Orange County law enforcement agencies. Each pathway is grounded in primary sources: FOIA/CPRA responses, federal contracts, privacy impact assessments, and investigative journalism.

---

## Two Systems, Two Pathways

Irvine PD operates **two separate ALPR platforms**, each with distinct federal access vectors:

1. **Vigilant/Motorola (LEARN + NVLS)** -- Irvine's legacy system, confirmed in use from at least 2016 through 2022 (504,494 detections in 2022). Vigilant data flows into the **National Vehicle Location Service (NVLS)**, which is commercially resold to Thomson Reuters and from there to ICE.

2. **Flock Safety** -- Irvine's current system, confirmed active by 2025. Flock operates a separate sharing network controlled by bilateral agency agreements, hot list exchanges, and (until October 2025) a "National Lookup" feature that bypassed bilateral agreements entirely.

Whether Irvine still contributes data to NVLS after switching to Flock is **unknown**. The two systems create independent, parallel pipelines to federal agencies. Even if one is shut down, the other may remain open.

---

## Pathway 1: Vigilant NVLS --> Thomson Reuters CLEAR --> ICE

This is the oldest and most thoroughly documented pathway. It does not require any direct relationship between Irvine PD and ICE. The data flows through a commercial intermediary.

### How It Works

```
Irvine PD ALPR cameras
        |
        v
Vigilant LEARN (local database)
        |
        v
Vigilant NVLS (national shared pool)
        |
        v
Thomson Reuters CLEAR (commercial product)
        |
        v
9,000+ ICE officers with CLEAR accounts
```

### Evidence Chain

**Irvine PD confirmed in NVLS (2016-2017)**
- The EFF's ALPR dataset (covering 2016-2017 survey responses) confirms Irvine PD participated in NVLS, contributing approximately 1,000,000 plate detections during that period.
- Source: EFF, "Street-Level Surveillance: Who's Got Your ALPR Data?"

**Irvine PD directly sharing with federal agencies (March 2020)**
- The 2020 Vigilant LEARN Agency Data Sharing Report (MuckRock #86954, `data/muckrock/*86954_doc0.pdf`, 17 pages, dated 03-02-20) confirms Irvine PD was directly sharing plate detections with:
  - **DHS - HSI (Newark NJ)** -- listed under "Detections Shared" (outbound)
  - **CBP - NTC** (National Targeting Center) -- listed under both "Detections Shared" and "Detections Received" (bidirectional)
  - **San Diego Sector Border Patrol (CA)** -- bidirectional (Detections Shared + Received + Hot List Sharing)
  - **Federal Bureau of Investigation** -- listed under "Detections Shared"
  - **Drug Enforcement Agency (NATL)** -- listed under "Detections Shared"
  - **ATF National Account** -- bidirectional
  - **Joint Regional Intelligence Center (CA)** -- listed under "Detections Shared" and "Hot List Sharing"
  - **HIDTA - Central Valley California** -- listed under "Detections Shared"
- Irvine also received the **HSI MASTER** hot list (under "Hot-List Received", associated with Montgomery Police Department)
- This report proves that Irvine PD had **direct, bilateral data sharing with DHS-HSI and CBP** in the Vigilant era, not just indirect access through NVLS/Thomson Reuters.
- Source: MuckRock FOIA #86954, filed by Dave Maass (EFF)

**Thomson Reuters accesses NVLS data via Vigilant partnership**
- Thomson Reuters (via its subsidiary West Publishing / Thomson Reuters Special Services) has a commercial data-sharing agreement with Vigilant Solutions (now Motorola Solutions). NVLS data is incorporated into the CLEAR investigative platform.
- Source: AFSC Investigate, Thomson Reuters company profile (https://investigate.afsc.org/company/thomson-reuters)
- Source: Privacy International letter to Thomson Reuters, Ref PI-Letter-TR-21-06 (https://s3.documentcloud.org/documents/4546858/PI-Letter-TR-21-06.pdf)

**Thomson Reuters CLEAR contains "7+ billion plate detections"**
- Privacy International's 2021 letter to Thomson Reuters documents that CLEAR provides "live access to more than 7 billion license plate detections" sourced from Vigilant's NVLS network.
- Source: Privacy International letter, cited above

**ICE has $54M+ in contracts with Thomson Reuters for CLEAR access**
- Federal procurement records show cumulative ICE spending on Thomson Reuters Special Services exceeding $54 million. The initial contract with West Publishing (Thomson Reuters) was approximately $6-7 million, executed in December 2017.
- Source: USAspending.gov, recipient ID 65494435-f70c-9a3e-15e0-474723c82d88-C

**DHS Privacy Impact Assessment PIA-039 confirms**
- DHS published PIA-039, "Acquisition and Use of License Plate Reader Data from a Commercial Service," in December 2017. This assessment formally acknowledges ICE's use of commercially aggregated LPR data (i.e., Thomson Reuters CLEAR) and establishes the legal framework under which ICE claims authority to access it.
- Source: https://www.dhs.gov/publication/dhs-ice-pia-039-acquisition-and-use-license-plate-reader-data-commercial-service

**9,000+ ICE officers have CLEAR accounts**
- ACLU of Northern California obtained approximately 1,800 pages of documents through FOIA litigation (2018-2019) revealing that more than 9,000 ICE officers held active CLEAR accounts with access to LPR data. The same documents identified 80+ local law enforcement agencies whose data was accessible to ICE through this pipeline.
- Source: ACLU NorCal, "Documents Reveal ICE Using Driver Location Data From Local Police for Deportations" (https://www.aclunorcal.org/blog/documents-reveal-ice-using-driver-location-data-local-police-deportations)

### Key Unknown

**Whether Irvine PD still uses Vigilant is UNKNOWN.** The timeline:
- **2016-2017:** EFF confirms Irvine in NVLS (~1M detections)
- **March 2020:** LEARN report confirms Vigilant active with direct HSI/CBP/BP sharing
- **Sept 2024:** BSCC grant application says "Flock **or** Vigilant" for 104 planned cameras
- **Feb 2025:** CPRA response is clearly a Flock export (A1-A4 format, not LEARN format)

The most likely scenario is that Irvine switched from Vigilant to Flock between 2020 and 2024. But:
1. If Vigilant is still active in any capacity, NVLS data sharing may continue automatically
2. Even if Vigilant is discontinued, historical scans likely remain in Thomson Reuters' CLEAR database
3. The switch from Vigilant to Flock **removed direct federal sharing** (HSI, CBP, BP are not on the Flock A1/A3 lists), raising the question of whether this was intentional or incidental

---

## Pathway 2: Flock Safety System

Flock operates differently from Vigilant. There is no centralized national pool equivalent to NVLS. Instead, sharing is controlled through bilateral network agreements (visible in Flock's "Networks I'm sharing" and "Networks shared with me" configuration screens) and hot list exchanges. The data obtained in the March 2025 MuckRock CPRA response (spreadsheet tabs A1 through A4) maps Irvine's Flock sharing topology.

### Direct Sharing: NO

Neither of Irvine PD's outbound sharing lists includes ICE, CBP, HSI, or any other federal immigration enforcement agency:

- **A1 (316 agencies):** Agencies that Irvine PD shares camera network data with. Does NOT include ICE, CBP, HSI, ERO, or Border Patrol.
- **A3 (156 agencies):** Agencies that share hot lists with Irvine PD (bidirectional). Does NOT include ICE, CBP, HSI, ERO, or Border Patrol.

This means federal immigration agencies cannot directly query Irvine's Flock camera data through the standard bilateral sharing mechanism.

### Indirect Pathways

Despite the absence of direct sharing, multiple indirect routes exist through which federal agencies can access or benefit from Irvine's Flock data:

#### 1. HSI Hot List Ingestion (A4)

Irvine PD's A4 data (hot list sources) confirms that **"HSI MASTER"** sends hot lists to Irvine. This means ICE/HSI pushes lists of target plates into Irvine's Flock system. When a plate on that list is detected by an Irvine camera, the system generates a real-time alert. The alert goes to Irvine PD officers, but the practical effect is that HSI's surveillance targets are being tracked by Irvine's cameras.

- **Direction:** Federal --> Irvine (inbound)
- **Effect:** Irvine's cameras become a detection network for HSI targets
- **Source:** MuckRock CPRA (March 2025), A4 tab

#### 2. Border Patrol Inbound Data (A2)

Irvine PD's A2 data (data sources shared with Irvine) confirms that **"SAN DIEGO SECTOR BORDER PATROL"** sends data to Irvine. The nature of this data (camera feeds, hot lists, or other intelligence) is not specified in the spreadsheet.

- **Direction:** Federal --> Irvine (inbound)
- **Source:** MuckRock CPRA (March 2025), A2 tab

#### 3. Fusion Center Relay

Irvine PD shares data with at least two fusion centers that have documented relationships with federal agencies:

- **NCRIC** (Northern California Regional Intelligence Center) -- listed in A1
- **JRIC** (Joint Regional Intelligence Center, Los Angeles) -- listed in A3

Fusion centers are explicitly designed to facilitate information sharing between local, state, and federal law enforcement. Any data Irvine shares with JRIC or NCRIC is accessible to the federal agencies that participate in those centers, including DHS components.

#### 4. OCSD Relay

Irvine PD shares Flock data with the **Orange County Sheriff's Department (OCSD)**. OCSD has been independently documented conducting searches on behalf of federal agencies:

- CalMatters (June 2025) reported that Oakland Privacy obtained Flock audit logs showing OCSD conducted 100+ searches in May 2025 on behalf of ICE and CBP, in violation of SB 34.
- OCSD's own sharing lists include **IRS Criminal Investigations** and **JRIC**.

The relay path: Irvine PD --> OCSD --> ICE/CBP (via OCSD officers running searches on federal behalf).

#### 5. Flock National Lookup / Back Door

Flock Safety operated a **"National Lookup"** pilot feature that allowed participating agencies to search across all Flock camera networks nationally, bypassing bilateral sharing agreements entirely. Under this feature, a federal agency did not need to appear in Irvine's "Networks I'm sharing" list to query Irvine's data.

- **Proven in Washington State:** The University of Washington Center for Human Rights (October 2025) documented that at least 10 agencies accessed other agencies' Flock data through National Lookup without explicit sharing agreements.
- **Status:** Flock paused the National Lookup pilot in October 2025 following the UW report and public backlash.
- **Unknown for Irvine:** Whether Irvine's data was accessed through National Lookup before it was paused has not been confirmed or denied. This would only be visible in Irvine's **Network Audit** logs, which have not been obtained.

---

## Pathway 3: Side Door Searches

This pathway does not involve any data-sharing agreement or technical access. Instead, local officers manually run ALPR searches on behalf of federal agents using their own credentials.

### How It Works

A federal agent (ICE, CBP, HSI) contacts a local officer and asks them to look up a plate in the local ALPR system. The local officer runs the search and relays the results to the federal agent. The search appears in audit logs under the local officer's name and agency, not the federal agency's. From the Flock platform's perspective, it looks like a routine local search.

### Evidence

**VPM Investigation (Virginia Public Media)**
- VPM's investigation identified **4,000+ immigration-related ALPR lookups** conducted by local law enforcement agencies nationwide on behalf of federal immigration agents.
- **Warren County, Virginia:** The sheriff publicly confirmed that his deputies ran ALPR searches at the request of federal immigration agents.

**CalMatters / OCSD**
- CalMatters documented that OCSD officers conducted searches on behalf of CBP and Border Patrol, which constituted SB 34 violations because immigration enforcement is not a permissible use under California law.

### Why This Is Hard to Detect

Side door searches are invisible in network-level sharing configurations (A1-A4). They only appear in the **Organization Audit** (which logs the searching officer's name and stated reason) or the **Network Audit** (which logs cross-network queries). If the searching officer enters a generic reason (e.g., "suspicious vehicle") rather than disclosing the federal nexus, the search purpose is effectively laundered.

---

## UW Center for Human Rights Report Findings (October 2025)

The University of Washington Center for Human Rights published a detailed investigation in October 2025 documenting three categories of federal access to Flock data in Washington State:

### Front Door
- **8 Washington agencies** had direct, bilateral Flock sharing agreements with federal agencies (ICE, CBP, HSI).
- These agreements were visible in the agencies' Flock network sharing configurations.

### Back Door
- **10+ agencies** had their data accessed by federal agencies through **Flock's National Lookup** feature, without any bilateral sharing agreement in place.
- The agencies whose data was accessed were not aware it was being queried by federal users.

### Side Door
- Local officers running manual searches on behalf of federal agents, as described in Pathway 3 above.

### Outcome
- Flock Safety **paused the National Lookup pilot** in response to the UW report and related media coverage.
- Source: SeaTac Blog, "Back Door Loophole Closed for SeaTac's Flock Cameras Amid Growing Concern of Immigration Enforcement" (October 29, 2025)

---

## OC-Specific Evidence

### OCSD Searched on Behalf of Federal Agencies
- CalMatters (June 13, 2025) reported that Oakland Privacy obtained OCSD's Flock audit logs showing more than 100 searches conducted on behalf of CBP and Border Patrol in May 2025 alone.
- These searches violated SB 34 (Civil Code Section 1798.90.5), which prohibits sharing ALPR data for immigration enforcement purposes.
- Source: https://calmatters.org/economy/technology/2025/06/california-police-sharing-license-plate-reader-data/

### Anaheim PD Collaborates with HSI
- Anaheim PD's BSCC (Board of State and Community Corrections) grant application documents collaboration with HSI on major investigations.
- Anaheim uses Vigilant (not Flock), but the collaboration establishes a pattern of OC agencies working directly with federal immigration enforcement components.

### SFPD Precedent: 1.6 Million Illegal Searches
- In 2025, the San Francisco Police Department was found to have conducted approximately 1.6 million out-of-state ALPR searches in violation of California law, demonstrating that audit log violations at massive scale can go undetected for extended periods.

### All OC Flock Transparency Portals List Immigration Enforcement as "Prohibited Use"
The following OC agencies maintain Flock transparency portals that explicitly list immigration enforcement as a prohibited use of ALPR data:

- Buena Park PD (https://transparency.flocksafety.com/buena-park-ca-pd)
- Costa Mesa PD (https://transparency.flocksafety.com/costa-mesa-ca-pd)
- Newport Beach PD (https://transparency.flocksafety.com/newport-beach-ca-pd)
- Fountain Valley PD (https://transparency.flocksafety.com/fountain-valley-ca-pd)
- Westminster PD (https://transparency.flocksafety.com/westminster-ca-pd)

**However:** Policy prohibitions do not prevent indirect access through fusion centers, OCSD relay, side door searches, or (before October 2025) National Lookup. The OCSD violations demonstrate that written policies are not enforced absent independent audit review.

---

## Cities That Canceled or Restricted ALPR Over ICE Concerns

### Nationwide
| City | State | Action |
|------|-------|--------|
| Chicago | IL | Cut off federal access to ALPR data |
| Richmond | VA | Cancelled Flock contract |
| Charlottesville | VA | Cut off federal access |

### California
| City | Action |
|------|--------|
| Richmond | Cancelled Flock contract over immigration enforcement concerns |
| Alameda | Restricted ALPR data sharing |
| San Pablo | Restricted ALPR data sharing |

These cancellations and restrictions demonstrate that the concern over federal immigration access to local ALPR data is not hypothetical -- it is the specific, documented reason multiple jurisdictions have terminated their ALPR programs.

---

## Key Legal Context

### SB 34 (Civil Code Section 1798.90.5 et seq.)
- Requires ALPR operators to maintain **usage and access audit logs**.
- Requires audit logs to be **available upon request by the public**.
- **Restricts sharing** of ALPR data and requires documentation of all access.
- Prohibits use of ALPR data for immigration enforcement purposes.

### Documented SB 34 Violations in 2025
| Agency | Violation | Source |
|--------|-----------|--------|
| OCSD | 100+ searches on behalf of ICE/CBP in May 2025 | CalMatters |
| SFPD | ~1.6 million illegal out-of-state searches | CalMatters |
| Santa Cruz PD | SB 34 audit log violations | CalMatters |

### Enforcement Gap
SB 34 has no designated enforcement agency. Violations are identified through public records requests and investigative journalism, not systematic audits. The OCSD violations were discovered by Oakland Privacy (a community organization) filing a CPRA request, not by any government oversight body.

---

## Summary: Access Pathway Matrix

| Pathway | Mechanism | Federal Agency | Confirmed? | Source |
|---------|-----------|---------------|------------|--------|
| 1a. NVLS/CLEAR | Vigilant --> Thomson Reuters --> ICE | ICE (9,000+ officers) | Irvine in NVLS confirmed (2016-2017); current status UNKNOWN | EFF, DHS PIA-039, ACLU NorCal |
| 1b. Direct Vigilant sharing | Irvine LEARN --> DHS-HSI, CBP-NTC, Border Patrol | HSI, CBP, BP, FBI, DEA, ATF | **YES** (2020 LEARN report, 17 pages) | MuckRock #86954, Dave Maass (EFF) |
| 2a. HSI hot list | HSI pushes target plates to Irvine Flock | HSI/ICE | YES (A4 data) | MuckRock CPRA March 2025 |
| 2b. BP inbound | Border Patrol sends data to Irvine Flock | CBP/BP | YES (A2 data) | MuckRock CPRA March 2025 |
| 2c. Fusion center | Irvine --> NCRIC/JRIC --> federal participants | DHS components | CONFIRMED (sharing exists); access NOT directly observed | MuckRock CPRA March 2025 |
| 2d. OCSD relay | Irvine --> OCSD --> ICE/CBP | ICE, CBP | CONFIRMED (OCSD violations documented) | CalMatters June 2025 |
| 2e. National Lookup | Flock back door (bypasses sharing agreements) | Any Flock user | CONFIRMED in WA; UNKNOWN for Irvine; PAUSED Oct 2025 | UW Center for Human Rights |
| 3. Side door | Local officer runs search for federal agent | Any federal agency | CONFIRMED nationally; CONFIRMED for OCSD; UNKNOWN for Irvine PD | VPM, CalMatters |

---

## Sources

- **DHS PIA-039:** https://www.dhs.gov/publication/dhs-ice-pia-039-acquisition-and-use-license-plate-reader-data-commercial-service
- **ACLU NorCal FOIA:** https://www.aclunorcal.org/blog/documents-reveal-ice-using-driver-location-data-local-police-deportations
- **EFF ALPR Dataset:** https://www.eff.org/pages/what-we-know-about-automated-license-plate-readers
- **CalMatters (June 2025):** https://calmatters.org/economy/technology/2025/06/california-police-sharing-license-plate-reader-data/
- **VPM Investigation:** https://www.vpm.org/news/2025-01-27/license-plate-readers-police-ice-immigration
- **UW Center for Human Rights (Oct 2025):** https://jsis.washington.edu/humanrights/2025/10/28/flock-safety-ice-cbp/
- **Privacy International:** https://s3.documentcloud.org/documents/4546858/PI-Letter-TR-21-06.pdf
- **AFSC Investigate:** https://investigate.afsc.org/company/thomson-reuters
- **USAspending.gov (Thomson Reuters):** https://www.usaspending.gov/recipient/65494435-f70c-9a3e-15e0-474723c82d88-C/latest
- **Flock Official Statement (Aug 2025):** https://www.flocksafety.com/blog/statement-network-sharing-use-cases-federal-cooperation
- **SeaTac Blog (Oct 2025):** https://seatacblog.com/2025/10/29/back-door-loophole-closed-for-seatacs-flock-cameras-amid-growing-concern-of-immigration-enforcement/
- **MuckRock FOIA (Irvine PD, 2020):** https://www.muckrock.com/foi/irvine-3262/2020-vigilant-data-sharing-information-automated-license-plate-reader-alpr-irvine-police-department-86954/
- **MuckRock CPRA (Irvine PD, March 2025):** https://www.muckrock.com/foi/irvine-3262/alpr-audits-irvine-police-department-181267/
- **EFF Investigation (Nov 2025):** https://www.eff.org/deeplinks/2025/11/license-plate-surveillance-logs-reveal-racist-policing-against-romani-people
