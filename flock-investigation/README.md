# Orange County Flock Safety ALPR Investigation

Last Updated: February 22, 2026

## The Core Question

**Can ICE/federal immigration agencies access Irvine PD's license plate reader data?**

**Answer: Yes, and it's getting worse.** Flock's CEO admitted in August 2025 that CBP had direct access to 80,000+ Flock cameras nationwide via an undisclosed pilot. OC Sheriff was caught running 100+ ALPR searches for ICE/CBP in a single month (CalMatters, June 2025). ICE opened a new office in Irvine in February 2026. Irvine PD has zero public oversight of its ALPR program -- no transparency portal, no city council discussion, and nobody has filed the CPRA that would expose the audit logs.

## What's Happening Right Now (2025-2026)

### The Flock-ICE connection is confirmed nationally

| Date | Event | Source |
|------|-------|--------|
| **Jun 2025** | CalMatters reveals LAPD, OC Sheriff, SD Sheriff ran 100+ ALPR searches for ICE/CBP in one month. OC Sheriff specifically searched for Border Patrol. | [CalMatters](https://calmatters.org/economy/technology/2025/06/california-police-sharing-license-plate-reader-data/) |
| **Aug 2025** | Flock CEO admits CBP had **direct access to 80,000+ Flock cameras** via undisclosed pilot. Flock pauses all federal pilot programs. | [9News](https://www.9news.com/article/news/local/flock-federal-immigration-agents-access-tracking-data/73-a8aee742-56d4-4a57-b5bb-0373286dfef8) |
| **Sep 2025** | SFPD's Flock database had **1.6M+ illegal out-of-state searches**, including 19+ marked as ICE-related. | [SF Standard](https://sfstandard.com/2025/09/08/sfpd-flock-alpr-ice-data-sharing/) |
| **Oct 2025** | AG Bonta **sues El Cajon** for sharing ALPR data with 100+ out-of-state agencies. UW report proves Flock's "National Lookup" backdoor in WA state. **SB 274** (ALPR reform bill) **vetoed by Newsom**. | [CalMatters](https://calmatters.org/justice/2025/10/el-cajon-police-license-plate-data/), [CalMatters](https://calmatters.org/economy/technology/2025/10/newsom-vetoes-license-plate-reader-regulations/) |
| **Nov 2025** | Capitola PD admits ICE accessed their plate data ("a mistake"). Oakland PD sued for sharing Flock data with feds. | [Santa Cruz Local](https://santacruzlocal.org/2025/11/07/ice-accessed-capitola-license-plate-data-police-say-it-was-a-mistake/) |
| **Feb 2026** | ICE **opens offices in Irvine** (2020 Main St) and Santa Ana. 3 women detained at Irvine business. Mountain View disables all 30 Flock cameras after discovering unauthorized ATF/Air Force access. **~30 cities** have deactivated or canceled Flock contracts. Amazon Ring terminates Flock integration. | [OC Register](https://www.ocregister.com/2026/02/10/ice-reportedly-leases-office-spaces-in-irvine-and-santa-ana/), [NPR](https://www.npr.org/2026/02/17/nx-s1-5612825/flock-contracts-canceled-immigration-survillance-concerns) |

### Irvine PD's current setup

- **Vendor:** Flock Safety (confirmed Feb 2025; fully transitioned from Vigilant)
- **Cameras:** ~30 stationary ALPR cameras ($112,500/yr via BSCC grant, contract since Oct 2023)
- **Detections:** 107,472,041 plate scans (2019-2025)
- **Real-Time Crime Center:** $2M facility opened Dec 2024, monitors 1,000+ camera feeds including LPRs, drones
- **Transparency portal:** None. (Costa Mesa, Buena Park, Newport Beach, Fountain Valley, Westminster all have one.)
- **City council oversight:** None found in 2025-2026
- **CalMatters investigation:** Irvine PD was **not named** as a violator (OC Sheriff was). But nobody has checked Irvine's logs.

## What We Know From FOIA Data

### Flock system (2025): No direct ICE sharing, but four indirect pathways

Irvine's A1/A3 lists (316 + 156 agencies) do NOT include ICE/CBP/HSI. But:

| Pathway | Evidence | Why it matters |
|---------|----------|----------------|
| **HSI hot list** | HSI MASTER on A4 (hot lists received) | HSI pushes target plates; Irvine's cameras auto-alert when detected |
| **OCSD relay** | CalMatters confirmed OCSD ran searches for ICE/CBP | Irvine shares data with OCSD; OCSD is a confirmed SB 34 violator |
| **Fusion centers** | NCRIC on A1, JRIC on A3 | Fusion centers share with federal participants by design |
| **Flock back door** | CEO admitted CBP had access to 80K cameras via pilot | Paused Aug 2025, but was it active for Irvine before that? **Unknown.** |

### Vigilant system (2020): DIRECT federal sharing (historical)

Before switching to Flock, the 2020 Vigilant LEARN report (`data/muckrock/*86954_doc0.pdf`) proves Irvine was **directly sharing plate data** with DHS-HSI (Newark NJ), CBP-NTC, San Diego Sector Border Patrol, FBI, DEA, and ATF. This is no longer active -- Irvine has fully transitioned to Flock -- but demonstrates the relationship existed.

## What We Don't Know (The Gaps)

| Gap | Why it matters | What would answer it |
|-----|---------------|---------------------|
| Who queries Irvine's Flock system? | 350K+ outside queries/month, no agency breakdown | **Network Audit** export from Flock |
| How many hits came from HSI's hot list? | 31,278 total hits, no source breakdown | **Hot list action log** + hit reports |
| Was CBP's 80K-camera pilot active for Irvine? | Would mean CBP had direct access without any sharing agreement | Flock platform settings history (National Lookup) |
| Does Irvine's Real-Time Crime Center feed to anyone? | 1,000+ cameras monitored centrally, no public policy | CPRA for RTCC policies and data sharing agreements |

**Nobody has filed a CPRA asking Irvine PD for the Network Audit or hot list logs.** Other agencies (Aurora PD, Spokane County, Riverside County SO) have provided these. The CalMatters investigation used exactly these logs to catch OC Sheriff. See [docs/cpra-template.md](docs/cpra-template.md) for the request template.

## Data Sources

### FOIA Documents (in `data/`)

| File | What it contains | Source |
|------|-----------------|--------|
| `muckrock/*86954_doc0.pdf` | Irvine PD: 2020 Vigilant LEARN report -- direct HSI/CBP/BP sharing | [MuckRock #86954](https://www.muckrock.com/foi/irvine-3262/2020-vigilant-data-sharing-information-automated-license-plate-reader-alpr-irvine-police-department-86954/) |
| `muckrock/alpr-audits-*_doc5.xlsx` | Irvine PD: A1-A4 Flock sharing lists, 107M detections, 31K hits, 199 users, 44K audit entries | [MuckRock #181267](https://www.muckrock.com/foi/irvine-3262/) |
| `A1-A4_Data_Sharing.pdf` | OCSD: Full data sharing report (IRS, JRIC, 150+ agencies) | [MuckRock OCIAC](https://cdn.muckrock.com/foia_files/2025/03/20/A1-_A4__XBKg6U3.pdf) |
| `SharedNetworks_2025_December.xlsx` | OCSD: 391 network organizations | MuckRock CPRA |

### Reference Documents

| Document | Description |
|----------|-------------|
| [docs/cpra-template.md](docs/cpra-template.md) | CPRA request template (Flock audit exports + Vigilant status) |
| [docs/flock-audit-features.md](docs/flock-audit-features.md) | Flock platform feature documentation |
| [docs/oc-cities.md](docs/oc-cities.md) | All OC cities with Flock contracts, cameras, costs |
| [docs/federal-access.md](docs/federal-access.md) | Federal agency access pathways (all documented routes) |

## Filing the CPRA

**Submit to:** Irvine Police Department, Public Safety Records
- Email: kloza@cityofirvine.org (Kailene Loza, Lead Records Specialist)
- Address: 1 Civic Center Plaza, Irvine, CA 92606
- Or file via [MuckRock](https://www.muckrock.com/agency/irvine-3262/irvine-police-department-5232/)

**Timeline:** Joey Scott's similar request took 29 days (Feb 10 -> Mar 11, 2025). The immigration request (#184958) took 3 months with multiple 14-day extensions.

**Legal basis:** CPRA (Gov Code § 7920 et seq.) + SB 34 (Civil Code § 1798.90.5). AG Bonta's October 2025 lawsuit against El Cajon establishes that these violations are being enforced.

**Context for urgency:** ICE opened an Irvine office in Feb 2026. OC Sheriff is a confirmed SB 34 violator. Flock admitted CBP had access to 80K+ cameras. ~30 cities are canceling Flock contracts. Irvine has done nothing publicly.

See [docs/cpra-template.md](docs/cpra-template.md) for the full request letter.
