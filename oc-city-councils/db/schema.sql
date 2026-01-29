-- OC City Councils Database Schema - COMPLETE
-- Captures ALL fields from YAML files plus additional tracking

-- ============================================================================
-- CITIES
-- ============================================================================

CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    website TEXT,
    council_url TEXT,

    -- Meeting info
    meeting_schedule TEXT,
    meeting_time TEXT,
    meeting_location_name TEXT,
    meeting_address TEXT,
    meeting_city_state_zip TEXT,

    -- Remote meeting access
    zoom_url TEXT,
    zoom_id TEXT,
    zoom_passcode TEXT,
    zoom_phone_numbers TEXT,  -- JSON array or comma-separated
    webex_url TEXT,

    -- Clerk info
    clerk_name TEXT,
    clerk_title TEXT,
    clerk_phone TEXT,
    clerk_fax TEXT,
    clerk_email TEXT,
    clerk_address TEXT,

    -- Council composition
    council_size INTEGER,
    council_districts INTEGER,
    council_at_large INTEGER,
    mayor_elected BOOLEAN,
    mayor_rotation BOOLEAN,
    council_expanded_date TEXT,
    council_transition_date TEXT,
    council_notes TEXT,

    -- Portals & URLs
    document_center TEXT,
    municipal_code TEXT,
    agendas_url TEXT,
    live_stream_url TEXT,
    video_archive_url TEXT,
    granicus_url TEXT,
    legistar_url TEXT,
    youtube_url TEXT,
    cablecast_url TEXT,
    ecomment_url TEXT,
    district_map_url TEXT,
    invite_form_url TEXT,
    public_comment_form_url TEXT,

    -- Broadcast
    broadcast_live_stream TEXT,
    -- cable_channels stored in separate table

    -- Public comment rules
    public_comment_in_person BOOLEAN,
    public_comment_remote_live BOOLEAN,
    public_comment_ecomment BOOLEAN,
    public_comment_written_email BOOLEAN,
    public_comment_written_form BOOLEAN,
    public_comment_time_limit TEXT,
    public_comment_total_time_limit TEXT,
    public_comment_deadline TEXT,
    public_comment_email TEXT,
    public_comment_instructions_url TEXT,
    public_comment_notes TEXT,

    -- Term limits
    term_limit INTEGER,
    term_limit_type TEXT DEFAULT 'terms',  -- 'terms' or 'years'
    term_limit_cooldown INTEGER,
    term_limit_cooldown_unit TEXT DEFAULT 'cycles',  -- 'cycles' or 'years'
    term_limit_effective TEXT,
    term_limit_notes TEXT,
    term_limit_source TEXT,
    term_length INTEGER DEFAULT 4,

    -- Elections
    election_system TEXT,  -- by-district, at-large, mixed
    next_election TEXT,
    nomination_period TEXT,
    transition_note TEXT,
    results_source TEXT,
    past_results_url TEXT,
    districting_info_url TEXT,
    fppc_filings_url TEXT,
    candidate_resources_url TEXT,
    contribution_limit TEXT,

    -- Candidate filing info
    candidate_contact_email TEXT,
    candidate_contact_phone TEXT,
    candidate_filing_location TEXT,

    -- Meta
    last_updated TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Cable channels (many per city)
CREATE TABLE IF NOT EXISTS cable_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    channel TEXT NOT NULL,
    FOREIGN KEY (city_id) REFERENCES cities(id)
);

-- ============================================================================
-- PEOPLE (anyone who runs for office or serves)
-- ============================================================================

CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,

    -- Contact
    email TEXT,
    phone TEXT,

    -- Bio & photo
    bio TEXT,
    photo_url TEXT,

    -- Online presence
    city_page TEXT,  -- Official city profile
    website TEXT,    -- Personal/campaign site
    facebook TEXT,
    twitter TEXT,
    instagram TEXT,
    linkedin TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TERMS (service on council)
-- ============================================================================

CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    city_id INTEGER NOT NULL,

    -- Position
    district TEXT,
    position TEXT,  -- Mayor, Vice Mayor, Mayor Pro Tem, Councilmember

    -- Start
    start_date TEXT,
    start_year INTEGER,
    start_type TEXT,  -- elected, appointed, succeeded
    election_id INTEGER,
    appointed_by TEXT,
    appointment_reason TEXT,

    -- End
    end_date TEXT,
    end_year INTEGER,
    end_type TEXT,  -- completed, resigned, recalled, died, removed, ongoing
    end_reason TEXT,

    notes TEXT,
    source_url TEXT,

    FOREIGN KEY (person_id) REFERENCES people(id),
    FOREIGN KEY (city_id) REFERENCES cities(id),
    FOREIGN KEY (election_id) REFERENCES elections(id)
);

-- Position changes within a term (mayor rotation)
CREATE TABLE IF NOT EXISTS position_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL,
    position TEXT NOT NULL,
    start_date TEXT,
    start_year INTEGER,
    end_date TEXT,
    end_year INTEGER,
    notes TEXT,
    FOREIGN KEY (term_id) REFERENCES terms(id)
);

-- ============================================================================
-- ELECTIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS elections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER NOT NULL,

    -- When
    date TEXT NOT NULL,
    year INTEGER,

    -- Type
    type TEXT,  -- general, special, recall, runoff
    election_system TEXT,  -- by-district, at-large, mixed

    -- Admin
    nomination_period TEXT,
    resolution_number TEXT,
    certified_date TEXT,

    -- Links
    source_url TEXT,
    results_url TEXT,

    -- If special election
    triggered_by_vacancy_id INTEGER,

    notes TEXT,

    FOREIGN KEY (city_id) REFERENCES cities(id),
    FOREIGN KEY (triggered_by_vacancy_id) REFERENCES vacancies(id)
);

-- Seats on the ballot
CREATE TABLE IF NOT EXISTS election_seats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    election_id INTEGER NOT NULL,
    district TEXT,  -- District 1, At-Large, Mayor
    seat_type TEXT,  -- full_term, unexpired_term
    term_years INTEGER,
    incumbent_id INTEGER,

    FOREIGN KEY (election_id) REFERENCES elections(id),
    FOREIGN KEY (incumbent_id) REFERENCES people(id)
);

-- Election cycles (which districts up when)
CREATE TABLE IF NOT EXISTS election_cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER NOT NULL,
    group_name TEXT,  -- group_a, group_b
    district TEXT NOT NULL,
    cycle_years TEXT,  -- "2024, 2028, 2032..."

    FOREIGN KEY (city_id) REFERENCES cities(id)
);

-- Upcoming seats (next election)
CREATE TABLE IF NOT EXISTS upcoming_seats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER NOT NULL,
    election_date TEXT,
    district TEXT,
    incumbent_id INTEGER,
    notes TEXT,

    FOREIGN KEY (city_id) REFERENCES cities(id),
    FOREIGN KEY (incumbent_id) REFERENCES people(id)
);

-- ============================================================================
-- CANDIDATES
-- ============================================================================

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    election_id INTEGER NOT NULL,
    seat_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,

    -- Filing
    status TEXT,  -- filed, qualified, withdrew, disqualified, on_ballot
    filing_date TEXT,

    -- Results
    votes INTEGER,
    vote_percentage REAL,
    outcome TEXT,  -- won, lost, runoff, withdrew

    -- Campaign
    campaign_website TEXT,
    campaign_email TEXT,

    notes TEXT,
    source_url TEXT,

    FOREIGN KEY (election_id) REFERENCES elections(id),
    FOREIGN KEY (seat_id) REFERENCES election_seats(id),
    FOREIGN KEY (person_id) REFERENCES people(id)
);

-- ============================================================================
-- VACANCIES
-- ============================================================================

CREATE TABLE IF NOT EXISTS vacancies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER NOT NULL,
    district TEXT,

    -- When and why
    vacancy_date TEXT,
    reason TEXT,  -- resignation, death, recall, removal, relocation
    previous_holder_id INTEGER,
    previous_term_id INTEGER,

    -- How filled
    filled_date TEXT,
    filled_by TEXT,  -- appointment, special_election, next_general
    filled_term_id INTEGER,

    notes TEXT,
    source_url TEXT,

    FOREIGN KEY (city_id) REFERENCES cities(id),
    FOREIGN KEY (previous_holder_id) REFERENCES people(id)
);

-- ============================================================================
-- SOURCES (provenance tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER,
    url TEXT NOT NULL,
    title TEXT,
    document_type TEXT,  -- resolution, minutes, ordinance, webpage, pdf, news
    accessed_date TEXT,
    notes TEXT,

    FOREIGN KEY (city_id) REFERENCES cities(id)
);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Current council members
CREATE VIEW IF NOT EXISTS v_current_council AS
SELECT
    c.slug as city_slug,
    c.name as city,
    p.name as member,
    p.email,
    p.phone,
    p.city_page,
    p.photo_url,
    t.position,
    t.district,
    t.start_year,
    t.end_year,
    t.start_type
FROM terms t
JOIN cities c ON t.city_id = c.id
JOIN people p ON t.person_id = p.id
WHERE t.end_type IS NULL OR t.end_type = 'ongoing' OR t.end_year >= strftime('%Y', 'now')
ORDER BY c.name,
    CASE t.position
        WHEN 'Mayor' THEN 1
        WHEN 'Vice Mayor' THEN 2
        WHEN 'Mayor Pro Tem' THEN 2
        ELSE 3
    END;

-- Cities missing key data
CREATE VIEW IF NOT EXISTS v_missing_data AS
SELECT
    name,
    CASE WHEN document_center IS NULL THEN 1 ELSE 0 END as missing_doc_center,
    CASE WHEN municipal_code IS NULL THEN 1 ELSE 0 END as missing_muni_code,
    CASE WHEN term_limit IS NULL THEN 1 ELSE 0 END as missing_term_limit
FROM cities
ORDER BY name;

-- Term limit tracking
CREATE VIEW IF NOT EXISTS v_term_limits AS
SELECT
    c.name as city,
    p.name as member,
    t.district,
    t.start_year,
    t.end_year,
    c.term_limit as max_terms,
    c.term_limit_effective,
    c.term_limit_cooldown
FROM terms t
JOIN cities c ON t.city_id = c.id
JOIN people p ON t.person_id = p.id
WHERE c.term_limit IS NOT NULL
AND (t.end_type IS NULL OR t.end_type = 'ongoing' OR t.end_year >= strftime('%Y', 'now'))
ORDER BY c.name, p.name;

-- Election history
CREATE VIEW IF NOT EXISTS v_election_history AS
SELECT
    c.name as city,
    e.year,
    e.type,
    e.election_system,
    es.district,
    p.name as winner,
    ca.votes,
    e.resolution_number,
    e.source_url
FROM elections e
JOIN cities c ON e.city_id = c.id
JOIN election_seats es ON es.election_id = e.id
LEFT JOIN candidates ca ON ca.seat_id = es.id AND ca.outcome = 'won'
LEFT JOIN people p ON ca.person_id = p.id
ORDER BY c.name, e.year DESC, es.district;

-- ============================================================================
-- TERM LIMIT CALCULATIONS (computed fields)
-- ============================================================================

-- Term limit status for current members
-- Calculates: terms served since cutoff, terms remaining, term-out year, eligible-again year
-- Uses exact dates (start_date vs term_limit_effective) for accurate cutoff comparison
CREATE VIEW IF NOT EXISTS v_term_limit_status AS
SELECT
    c.name as city,
    c.slug as city_slug,
    p.name as member,
    t.district,
    t.position,
    t.start_date,
    t.start_year,
    t.end_date,
    t.end_year,
    c.term_limit as max_terms,
    c.term_limit_type,  -- 'terms' or 'years'
    c.term_length,
    c.term_limit_effective as cutoff_date,
    c.term_limit_cooldown,
    c.term_limit_cooldown_unit,
    -- Count terms elected since cutoff using EXACT DATES
    -- A term counts if start_date >= term_limit_effective
    (SELECT COUNT(*) FROM terms t2
     WHERE t2.person_id = t.person_id
     AND t2.city_id = t.city_id
     AND t2.start_type = 'elected'
     AND t2.start_date >= c.term_limit_effective
    ) as terms_since_cutoff,
    -- Terms remaining before term-limited
    c.term_limit - (SELECT COUNT(*) FROM terms t2
     WHERE t2.person_id = t.person_id
     AND t2.city_id = t.city_id
     AND t2.start_type = 'elected'
     AND t2.start_date >= c.term_limit_effective
    ) as terms_remaining,
    -- When they will term out (last term end year)
    CASE
        WHEN (SELECT COUNT(*) FROM terms t2
              WHERE t2.person_id = t.person_id
              AND t2.city_id = t.city_id
              AND t2.start_type = 'elected'
              AND t2.start_date >= c.term_limit_effective
             ) >= c.term_limit
        THEN t.end_year
        ELSE t.end_year + ((c.term_limit - (SELECT COUNT(*) FROM terms t2
              WHERE t2.person_id = t.person_id
              AND t2.city_id = t.city_id
              AND t2.start_type = 'elected'
              AND t2.start_date >= c.term_limit_effective
             )) * c.term_length)
    END as term_out_year,
    -- When eligible again after cooldown
    CASE
        WHEN c.term_limit_cooldown IS NOT NULL THEN
            CASE
                WHEN (SELECT COUNT(*) FROM terms t2
                      WHERE t2.person_id = t.person_id
                      AND t2.city_id = t.city_id
                      AND t2.start_type = 'elected'
                      AND t2.start_date >= c.term_limit_effective
                     ) >= c.term_limit
                THEN t.end_year + (c.term_limit_cooldown *
                    CASE c.term_limit_cooldown_unit
                        WHEN 'years' THEN 1
                        WHEN 'cycles' THEN 2  -- Assume 2 years per cycle
                        ELSE 2
                    END)
                ELSE t.end_year + ((c.term_limit - (SELECT COUNT(*) FROM terms t2
                      WHERE t2.person_id = t.person_id
                      AND t2.city_id = t.city_id
                      AND t2.start_type = 'elected'
                      AND t2.start_date >= c.term_limit_effective
                     )) * c.term_length) + (c.term_limit_cooldown *
                    CASE c.term_limit_cooldown_unit
                        WHEN 'years' THEN 1
                        WHEN 'cycles' THEN 2
                        ELSE 2
                    END)
            END
        ELSE NULL
    END as eligible_again_year,
    -- Is this term subject to term limits? (started on or after effective date)
    CASE
        WHEN t.start_date >= c.term_limit_effective THEN 'yes'
        ELSE 'no (grandfathered)'
    END as subject_to_limit,
    -- District election cycle
    (SELECT ec.cycle_years FROM election_cycles ec
     WHERE ec.city_id = c.id AND ec.district = t.district
     LIMIT 1) as district_cycle
FROM terms t
JOIN cities c ON t.city_id = c.id
JOIN people p ON t.person_id = p.id
WHERE c.term_limit IS NOT NULL
AND (t.end_type IS NULL OR t.end_type = 'ongoing' OR t.end_year >= strftime('%Y', 'now'))
ORDER BY c.name, p.name;

-- Summary of cities with term limits
CREATE VIEW IF NOT EXISTS v_term_limit_cities AS
SELECT
    name as city,
    slug,
    term_limit as max_value,
    term_limit_type as limit_type,  -- 'terms' or 'years'
    term_length,
    term_limit_cooldown as cooldown_value,
    term_limit_cooldown_unit as cooldown_unit,  -- 'cycles' or 'years'
    term_limit_effective as effective_date,
    CAST(SUBSTR(term_limit_effective, 1, 4) AS INTEGER) as effective_year,
    term_limit_notes as notes,
    term_limit_source as source_url,
    election_system,
    next_election
FROM cities
WHERE term_limit IS NOT NULL
ORDER BY name;
