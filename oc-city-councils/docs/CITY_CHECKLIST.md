# City Data Checklist

Coverage status for all 34 OC cities. Auto-generated from current YAML data.

**To regenerate:** `python scripts/validate_schema.py --coverage`

**Last updated:** 2026-01-29

---

## Coverage Summary

| City | History | Votes | Candidates | Term Limits | Doc Center | Municipal Code |
|------|:-------:|:-----:|:----------:|:-----------:|:----------:|:--------------:|
| Aliso Viejo | 7 | ✓ | ✓ | ✓ | ✓ | ? |
| Anaheim | 7 | ✓ | ✓ | ✓ | ✓ | ? |
| Brea | 7 | ✓ | ✓ | - | - | - |
| Buena Park | 7 | ✓ | ✓ | - | ✓ | ? |
| Costa Mesa | 7 | ✓ | ✓ | - | ✓ | ? |
| Cypress | 7 | ✓ | ✓ | - | ✓ | ? |
| Dana Point | 7 | ✓ | ✓ | ✓ | ✓ | ? |
| Fountain Valley | 7 | ✓ | ✓ | ✓ | ✓ | ? |
| Fullerton | 7 | ✓ | ✓ | - | - | - |
| Garden Grove | 7 | ✓ | ✓ | - | - | - |
| Huntington Beach | 7 | ✓ | ✓ | - | - | - |
| Irvine | 7 | ✓ | ✓ | - | - | - |
| La Habra | 5 | ✓ | ✓ | - | - | - |
| La Palma | 7 | ✓ | ✓ | - | - | - |
| Laguna Beach | 7 | ✓ | ✓ | - | - | - |
| Laguna Hills | 6 | ✓ | ✓ | - | - | - |
| Laguna Niguel | 6 | ✓ | ✓ | - | - | - |
| Laguna Woods | 6 | ✓ | ✓ | - | - | - |
| Lake Forest | 7 | ✓ | ✓ | - | - | - |
| Los Alamitos | 6 | ✓ | ✓ | - | - | - |
| Mission Viejo | 6 | ✓ | ✓ | - | - | - |
| Newport Beach | 7 | ✓ | ✓ | - | - | - |
| Orange | 6 | ✓ | ✓ | - | - | - |
| Placentia | 7 | ✓ | ✓ | - | - | - |
| Rancho Santa Margarita | 1 | ✓ | ✓ | - | - | - |
| San Clemente | 7 | ✓ | ✓ | - | - | - |
| San Juan Capistrano | 7 | ✓ | ✓ | - | - | - |
| Santa Ana | 7 | ✓ | ✓ | - | - | - |
| Seal Beach | 6 | ✓ | ✓ | - | - | - |
| Stanton | 7 | ✓ | ✓ | ✓ | - | - |
| Tustin | 7 | ✓ | ✓ | - | - | - |
| Villa Park | 5 | ✓ | ✓ | ✓ | - | - |
| Westminster | 7 | ✓ | ✓ | - | - | - |
| Yorba Linda | 6 | ✓ | ✓ | ✓ | - | - |

### Legend

- **History**: Number of election years with data (max 7: 2012-2024)
- **Votes**: Has vote counts for winners
- **Candidates**: Has full candidate lists (winners + losers)
- **Term Limits**: Has term limit data documented (or confirmed no limits)
- **Doc Center**: Has document_center URL (Laserfiche, etc.)
- **Municipal Code**: Has municipal_code URL

---

## What's Complete ✓

- **All 34 cities** have YAML files with basic data
- **All 34 cities** have election history with vote counts and candidate lists
- **All 34 cities** have members, meetings, portals, clerk, public_comment, council sections

---

## What Needs Research

### Term Limits (26 cities need research)

Need to check municipal code for term limit ordinances:

| City | Research Link |
|------|---------------|
| Brea | https://www.codepublishing.com/CA/Brea/ |
| Buena Park | https://www.codepublishing.com/CA/BuenaPark/ |
| Costa Mesa | https://www.codepublishing.com/CA/CostaMesa/ |
| Cypress | https://www.codepublishing.com/CA/Cypress/ |
| Fullerton | https://www.codepublishing.com/CA/Fullerton/ |
| Garden Grove | https://www.qcode.us/codes/gardengrove/ |
| Huntington Beach | https://www.qcode.us/codes/huntingtonbeach/ |
| Irvine | https://www.codepublishing.com/CA/Irvine/ |
| La Habra | https://www.codepublishing.com/CA/LaHabra/ |
| La Palma | https://www.codepublishing.com/CA/LaPalma/ |
| Laguna Beach | https://www.codepublishing.com/CA/LagunaBeach/ |
| Laguna Hills | https://www.codepublishing.com/CA/LagunaHills/ |
| Laguna Niguel | https://www.codepublishing.com/CA/LagunaNiguel/ |
| Laguna Woods | https://www.codepublishing.com/CA/LagunaWoods/ |
| Lake Forest | https://www.codepublishing.com/CA/LakeForest/ |
| Los Alamitos | https://www.codepublishing.com/CA/LosAlamitos/ |
| Mission Viejo | https://www.codepublishing.com/CA/MissionViejo/ |
| Newport Beach | https://www.codepublishing.com/CA/NewportBeach/ |
| Orange | https://www.codepublishing.com/CA/Orange/ |
| Placentia | https://www.codepublishing.com/CA/Placentia/ |
| Rancho Santa Margarita | https://www.codepublishing.com/CA/RanchoSantaMargarita/ |
| San Clemente | https://www.codepublishing.com/CA/SanClemente/ |
| San Juan Capistrano | https://www.codepublishing.com/CA/SanJuanCapistrano/ |
| Santa Ana | https://www.qcode.us/codes/santaana/ |
| Seal Beach | https://www.codepublishing.com/CA/SealBeach/ |
| Tustin | https://www.codepublishing.com/CA/Tustin/ |
| Westminster | https://www.codepublishing.com/CA/Westminster/ |

### Document Center & Municipal Code URLs (27 cities need URLs)

Most cities have online document centers (Laserfiche, Granicus, etc.) and municipal code sites that need to be added to the YAML files.

---

## Election History Gaps

Some cities have fewer than 7 years of history:

| City | Years | Possible Reason |
|------|-------|-----------------|
| Rancho Santa Margarita | 1 | Only 2024 data found - may have odd-year elections |
| La Habra | 5 | Missing 2012, 2014 |
| Villa Park | 5 | Missing 2012, 2020 |
| Laguna Hills | 6 | Missing one year |
| Laguna Niguel | 6 | Missing one year |
| Laguna Woods | 6 | Missing one year |
| Los Alamitos | 6 | Missing one year |
| Mission Viejo | 6 | Missing one year |
| Orange | 6 | Missing one year |
| Seal Beach | 6 | Missing one year |
| Yorba Linda | 6 | Missing 2020 (odd year transition?) |

---

## Validation Commands

```bash
# Check schema coverage
python scripts/validate_schema.py --coverage

# Validate all YAML files
python scripts/validate_schema.py

# Check schema drift from reference (Aliso Viejo)
python scripts/check_schema_drift.py

# Verify election data against OC Registrar
python election_data/validate_against_yaml.py
```

---

## How to Update

1. Make changes to YAML file in `_council_data/`
2. Run `python scripts/validate_schema.py` to check for errors
3. Update this checklist if needed
4. Commit both files
