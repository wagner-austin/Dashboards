# OC City Council Data Collection Checklist

Generated: 2026-01-26

## Summary

- **34 cities** total
- **9 cities** fully complete
- **25 cities** need some data

---

## HIGH PRIORITY: Broadcast Cable Channels

Most cities broadcast meetings on local cable. Need to find channel numbers.

| City | Live Stream Available | Cable Channels Needed |
|------|----------------------|----------------------|
| costa-mesa | ❌ Need to find | ✅ Yes |
| la-palma | Audio only (no video) | May not have cable |
| laguna-beach | ✅ Granicus | ✅ Yes |
| laguna-hills | ✅ CivicClerk | ✅ Yes |
| lake-forest | ✅ Facebook Live | ✅ Yes |
| rancho-santa-margarita | ✅ Granicus | ✅ Yes |
| san-juan-capistrano | ✅ City website | ✅ Yes |
| stanton | ❌ Need to find | ✅ Yes |

**Where to find:** Usually listed on city's "Watch Meetings" or "City TV" page. Common providers: Spectrum, Cox, AT&T U-verse.

---

## HIGH PRIORITY: Clerk Names

These cities have clerk contact info but not the clerk's name:

| City | Current Title | Email | Need |
|------|---------------|-------|------|
| aliso-viejo | City Clerk's Office | city-clerk@avcity.org | Clerk name |
| cypress | City Clerk | cityclerk@cypressca.org | Clerk name |
| fullerton | City Clerk's Office | cityclerksoffice@cityoffullerton.com | Clerk name |
| laguna-beach | City Clerk's Office | cityclerk@lagunabeachcity.net | Clerk name |
| laguna-niguel | City Clerk's Office | cityclerk@cityoflagunaniguel.org | Clerk name |
| laguna-woods | City Clerk's Office | cityhall@cityoflagunawoods.org | Clerk name |
| mission-viejo | City Clerk's Office | cityclerk@cityofmissionviejo.org | Clerk name |
| newport-beach | City Clerk's Office | cityclerk@newportbeachca.gov | Clerk name |

**Where to find:** City staff directory, or "City Clerk" page.

---

## MEDIUM PRIORITY: Portals

Some cities missing agenda URLs or live stream links in the portals section:

### Missing portals.agendas (10 cities)
- Check city website for "Agendas & Minutes" page

### Missing portals.live_stream (6 cities)
- costa-mesa, la-palma, stanton need live stream URLs
- Others may have it in broadcast section but not portals

---

## LOW PRIORITY: Member Bios

Many council members have empty bios. These can be populated from:
- City council profile pages
- Campaign websites
- News articles

**Cities with empty bios:**
- orange (all 7 members)
- Several other cities have partial coverage

---

## Schema Reference

### Required Fields (must have)

**Top-level:**
- city, city_name, website, council_url, last_updated
- members, meetings, portals, broadcast, clerk
- public_comment, council, elections

**Each member:**
- name, position, district, email, phone
- city_page, photo_url, bio, term_start, term_end

**Meetings:**
- schedule, time, location (name, address, city_state_zip)

**Broadcast:**
- cable_channels (array of {provider, channel})
- live_stream (URL)

**Clerk:**
- name, title, phone, email

---

## Validation Command

Run this to check current status:
```bash
python validate_yaml.py --summary
```

Run this to see all issues:
```bash
python validate_yaml.py
```

Check a specific city:
```bash
python validate_yaml.py --file fountain-valley.yaml
```
