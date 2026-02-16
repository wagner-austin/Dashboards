# VERIFIED EVIDENCE: ICE → Thomson Reuters → Vigilant Solutions Data Chain

**Last Updated:** February 15, 2026
**Status:** VERIFIED with primary sources

---

## SUMMARY

The following evidence chain has been verified through official government documents, FOIA releases, and federal procurement records:

```
Local Police Agencies (like Irvine PD)
       ↓ (share plate scans to)
Vigilant Solutions LEARN Database (7+ billion detections)
       ↓ (data accessed via)
Thomson Reuters CLEAR Platform
       ↓ (contracted by)
ICE ($6-20M+ contracts since 2017)
       ↓
9,000+ ICE officers can query plate locations
```

---

## EVIDENCE TIER 1: OFFICIAL GOVERNMENT DOCUMENTS

### DHS Privacy Impact Assessment (PIA-039)

| Field | Value |
|-------|-------|
| **Document** | DHS/ICE/PIA-039(a) |
| **Date** | December 27, 2017 |
| **Source** | [DHS.gov](https://www.dhs.gov/publication/dhs-ice-pia-039-acquisition-and-use-license-plate-reader-data-commercial-service) |
| **Local Copy** | `dhs_pia_039_jan2018.pdf` |

**Key Quotes:**
> "ICE has now entered into a contract with a vendor to provide ERO and HSI with access to a commercial LPR database operated by a commercial partner."

> "The commercial LPR vendor is not permitted to use any of ICE's query data..."

**Note:** The official DHS document deliberately does NOT name the vendor or commercial partner. The structure described (vendor + commercial partner) matches Thomson Reuters + Vigilant.

---

### USAspending.gov Federal Contract Data

| Field | Value |
|-------|-------|
| **Recipient** | Thomson Reuters Special Services LLC |
| **Total Federal Contracts** | $13.3 million (trailing 12 months) |
| **ICE Specifically** | **$7.54 million (56.82%)** |
| **Source** | [USAspending.gov](https://www.usaspending.gov/recipient/65494435-f70c-9a3e-15e0-474723c82d88-C/latest) |
| **Local Copy** | `thomson_reuters_contracts.html`, `thomson_reuters_contracts.png` |

**Verified:** ICE is the largest customer of Thomson Reuters Special Services.

---

## EVIDENCE TIER 2: FOIA RELEASES

### ACLU of Northern California v. ICE (License Plate Readers)

| Field | Value |
|-------|-------|
| **Case Filed** | May 23, 2018 |
| **Documents Released** | 1,800+ pages (July-December 2018) |
| **Source** | [ACLU NorCal](https://www.aclunorcal.org/our-work/legal-docket/aclu-northern-california-v-ice-license-plate-readers) |
| **Local Copy** | `aclu_blog_post.txt`, `aclu_case_page.html` |

**Key Findings from FOIA Documents:**

1. **Vendors Named:**
   - Primary vendor: **Thomson Reuters**
   - Database operator: **Vigilant Solutions**
   - Database name: **LEARN**

2. **Contract Details:**
   - Value: **$6.1 million**
   - Term: Through September 2020
   - Finalized: December 2017

3. **Access Scope:**
   - **9,000+ ICE officers** have Vigilant database accounts
   - **5 billion+ license plate scans** from commercial sources
   - **500 million additional** from law enforcement
   - **80+ local agencies** sharing data with ICE

4. **Orange County Specific:**
   - Emails show Orange County fusion center detective searching Vigilant database for ICE
   - La Habra Police Department involved in informal ICE queries

**Source Quote (ACLU Blog, March 13, 2019):**
> "ICE rushed to finalize a 2017 contract with Thomson Reuters for access to the Vigilant database."

---

## EVIDENCE TIER 3: CIVIL SOCIETY INVESTIGATIONS

### Privacy International Letter to Thomson Reuters CEO

| Field | Value |
|-------|-------|
| **Date** | June 21, 2018 |
| **Recipient** | James C. Smith, CEO Thomson Reuters |
| **Source** | [DocumentCloud](https://s3.documentcloud.org/documents/4546858/PI-Letter-TR-21-06.pdf) |
| **Local Copy** | `privacy_international_thomson_reuters_letter.pdf` |

**Key Contract Information (cited from federal procurement docs):**

| Contract | Value | Purpose |
|----------|-------|---------|
| Thomson Reuters Special Services | $6.7 million (Feb 2018) | "Continuous monitoring to track 500,000 identities per month" |
| West Publishing (TR subsidiary) | $20+ million | CLEAR system with "live access to more than **7 billion license plate detections**" |
| West Publishing | $6 million (Dec 2017) | "Access to license plate reader database" |

---

### AFSC Investigate Database

| Field | Value |
|-------|-------|
| **Source** | [investigate.afsc.org](https://investigate.afsc.org/company/thomson-reuters) |
| **Local Copy** | `afsc_thomson_reuters.html` |

**Key Information:**
> "Thomson Reuters products are also provided to government agencies through third-party vendors like Thundercat Technology and **Motorola Solutions subsidiary Vigilant Solutions**."

> "Between 2003 and 2021, these contracts amounted to at least **$161 million**"

> "CLEAR provides the agency with... license plate data, real-time incarceration data, cell phone and address records..."

---

## WHAT IS PROVEN vs. INFERRED

| Claim | Status | Evidence |
|-------|--------|----------|
| ICE has contracts with Thomson Reuters | **PROVEN** | USAspending.gov, DHS PIA, Privacy International letter |
| Thomson Reuters CLEAR has license plate data | **PROVEN** | Privacy International letter ("7 billion detections") |
| Vigilant Solutions operates the LPR database | **PROVEN** | ACLU FOIA, AFSC database |
| Thomson Reuters accesses Vigilant data | **PROVEN** | AFSC database, ACLU FOIA |
| 9,000+ ICE officers have access | **PROVEN** | ACLU FOIA documents |
| ICE can query local agency LPR data | **PROVEN** | ACLU FOIA (80+ agencies confirmed sharing) |
| Orange County agencies in the network | **PROVEN** | ACLU mentions OC fusion center, EFF 2016-2017 data |

---

## LOCAL FILES DOWNLOADED

```
data/ice_evidence/
├── dhs_pia_039_jan2018.pdf          # Official DHS Privacy Impact Assessment
├── dhs_pia_039_jan2018.txt          # Text extraction
├── dhs_pia_039_june2021.pdf         # Updated PIA
├── thomson_reuters_contracts.html    # USAspending.gov page
├── thomson_reuters_contracts.png     # Screenshot
├── aclu_case_page.html              # ACLU legal docket
├── aclu_blog_post.txt               # ACLU March 2019 analysis
├── afsc_thomson_reuters.html        # AFSC Investigate page
├── scrape_results.json              # All scrape metadata
└── documentcloud/
    ├── privacy_international_thomson_reuters_letter.pdf  # KEY EVIDENCE
    └── vigilant_learn_user_guide.pdf
```

---

## REMAINING QUESTIONS

To make claims about **specific local agencies** (like Irvine PD), additional verification needed:

1. **Current NVLS participation** - EFF data is from 2016-2017
2. **Current Vigilant contract** - Irvine may have switched to Flock
3. **Audit logs** - Whether ICE has actually queried Irvine plates

**Recommended:** File CPRA request to Irvine PD for current data sharing agreements.

---

## PRIMARY SOURCE LINKS

1. **DHS PIA-039:** https://www.dhs.gov/publication/dhs-ice-pia-039-acquisition-and-use-license-plate-reader-data-commercial-service
2. **USAspending Thomson Reuters:** https://www.usaspending.gov/recipient/65494435-f70c-9a3e-15e0-474723c82d88-C/latest
3. **ACLU v. ICE Case:** https://www.aclunorcal.org/our-work/legal-docket/aclu-northern-california-v-ice-license-plate-readers
4. **ACLU Blog (March 2019):** https://www.aclunorcal.org/blog/documents-reveal-ice-using-driver-location-data-local-police-deportations
5. **Privacy International Letter:** https://s3.documentcloud.org/documents/4546858/PI-Letter-TR-21-06.pdf
6. **AFSC Investigate:** https://investigate.afsc.org/company/thomson-reuters
