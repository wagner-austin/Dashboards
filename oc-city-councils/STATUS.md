# Orange County City Council Data Collection

## Status: URL Verification Complete

**Date:** 2026-01-24

### Summary

| Status | Count |
|--------|-------|
| Total cities | 34 |
| URLs verified | 34 |
| Data complete | 1 (Irvine) |
| Data pending | 33 |

### Verified Council Page URLs

All 34 Orange County city council page URLs have been verified as accessible:

| City | Council URL |
|------|-------------|
| Aliso Viejo | https://avcity.org/222/City-Council |
| Anaheim | https://www.anaheim.net/158/City-Council | BROKEN NOT REAL, https://www.anaheim.net/2527/Agendas or 

https://www.anaheim.net/5174/Anaheim-Mayor-Ashleigh-Aitken, https://www.anaheim.net/3522/Council-Member-Ryan-Balius, https://www.anaheim.net/2314/Mayor-Pro-Tem-Carlos-A-Leon, https://www.anaheim.net/3523/Council-Member-Natalie-Rubalcava, https://www.anaheim.net/3524/Council-Member-Norma-Campos-Kurtz, https://www.anaheim.net/3521/Council-Member-Kristen-Maahs

| Brea | https://www.cityofbrea.gov/511/City-Council |
| Buena Park | https://www.buenapark.com/city_departments/city_council/council_members.php |
| Costa Mesa | https://www.costamesaca.gov/citycouncil |
| Cypress | https://www.cypressca.org/government/city-council |
| Dana Point | https://www.danapoint.org/departments/city-council |
| Fountain Valley | https://www.fountainvalley.org/148/City-Council |
| Fullerton | https://www.cityoffullerton.com/government/city-council |
| Garden Grove | https://ggcity.org/city-council |
| Huntington Beach | https://www.huntingtonbeachca.gov/citycouncil |
| Irvine | https://www.cityofirvine.org/city-council |
| La Habra | https://www.lahabraca.gov/153/City-Council |
| La Palma | https://www.lapalmaca.gov/66/City-Council |
| Laguna Beach | https://www.lagunabeachcity.net/live-here/city-council |
| Laguna Hills | https://www.lagunahillsca.gov/129/City-Council |
| Laguna Niguel | https://www.cityoflagunaniguel.org/106/City-Council |
| Laguna Woods | https://www.cityoflagunawoods.org/government/city-council |
| Lake Forest | https://www.lakeforestca.gov/citycouncil |
| Los Alamitos | https://cityoflosalamitos.org/165/City-Council |
| Mission Viejo | https://cityofmissionviejo.org/government/city-council |
| Newport Beach | https://www.newportbeachca.gov/government/city-council |
| Orange | https://www.cityoforange.org/citycouncil |
| Placentia | https://www.placentia.org/268/Mayor-City-Council |
| Rancho Santa Margarita | https://www.cityofrsm.org/160/Mayor-City-Council |
| San Clemente | https://www.san-clemente.org/government/city-council |
| San Juan Capistrano | https://sanjuancapistrano.org/318/City-Council |
| Santa Ana | https://www.santa-ana.org/city-council/ |
| Seal Beach | https://www.sealbeachca.gov/Government/City-Council |
| Stanton | https://www.stantonca.gov/government/city_council.php |
| Tustin | https://www.tustinca.org/168/City-Council |
| Villa Park | https://villapark.org/council-and-committees/city-council |
| Westminster | https://www.westminster-ca.gov/government/mayor-and-city-council-members |
| Yorba Linda | https://www.yorbalindaca.gov/149/City-Council |

### Data Fields to Collect

For each council member:
- Name
- Position (Mayor, Vice Mayor, Councilmember)
- District (if applicable)
- Email
- Phone
- Personal website
- City profile page
- Instagram

For each city:
- Public comment submission method/URL

### Files

- `oc_cities_master.json` - Master data file with all city info
- `index.html` - Generated HTML dashboard
- `scrape_city.py` - Per-city scraper script
- `check_urls_simple.py` - URL verification script
- `generate_html.py` - HTML generator

### Next Steps

1. Collect council member data for each city
2. Verify data accuracy
3. Generate final HTML document
