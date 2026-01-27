#!/usr/bin/env python3
"""
YAML Schema Definition for OC City Council Data

This module defines the canonical schema for city council YAML files,
including required fields, optional fields, and validation rules.
"""

# =============================================================================
# SCHEMA DEFINITION
# =============================================================================

SCHEMA = {
    # -------------------------------------------------------------------------
    # TOP-LEVEL FIELDS
    # -------------------------------------------------------------------------
    "top_level": {
        "required": [
            ("city", "URL slug (e.g., 'fountain-valley')"),
            ("city_name", "Display name (e.g., 'Fountain Valley')"),
            ("website", "Main city website URL"),
            ("council_url", "City council page URL"),
            ("last_updated", "Date string 'YYYY-MM-DD'"),
            ("members", "Array of council members"),
            ("meetings", "Meeting schedule and location"),
            ("portals", "Online portal links"),
            ("broadcast", "TV/streaming broadcast info"),
            ("clerk", "City clerk contact info"),
            ("public_comment", "Public comment procedures"),
            ("council", "Council structure info"),
            ("elections", "Election info"),
        ],
        "optional": [
            ("email", "General city council email"),
            ("phone", "General city council phone"),
            ("instagram", "City council Instagram handle"),
        ],
    },

    # -------------------------------------------------------------------------
    # MEMBER FIELDS
    # -------------------------------------------------------------------------
    "member": {
        "required": [
            ("name", "Full name"),
            ("position", "Mayor, Vice Mayor, Mayor Pro Tem, or Councilmember"),
            ("district", "District X, Ward X, At-Large, or null"),
            ("email", "Email address"),
            ("phone", "Phone number (XXX) XXX-XXXX"),
            ("city_page", "URL to city profile page"),
            ("photo_url", "URL to headshot photo"),
            ("bio", "Biography text (empty string if unavailable)"),
            ("term_start", "Year term started (integer)"),
            ("term_end", "Year term ends (integer)"),
        ],
        "optional": [
            ("website", "Personal campaign/political website"),
            ("instagram", "Personal Instagram handle"),
        ],
    },

    # -------------------------------------------------------------------------
    # MEETINGS FIELDS
    # -------------------------------------------------------------------------
    "meetings": {
        "required": [
            ("schedule", "Meeting schedule (e.g., '1st and 3rd Tuesdays')"),
            ("time", "Meeting start time (e.g., '6:00 PM')"),
            ("location", "Object with name, address, city_state_zip"),
        ],
        "optional": [
            ("closed_session_time", "Closed session start time"),
            ("remote", "Object with zoom_url, zoom_id, zoom_passcode"),
        ],
    },

    # -------------------------------------------------------------------------
    # MEETINGS.LOCATION FIELDS
    # -------------------------------------------------------------------------
    "meetings.location": {
        "required": [
            ("name", "Venue name (e.g., 'Council Chambers')"),
            ("address", "Street address"),
            ("city_state_zip", "City, State ZIP"),
        ],
        "optional": [],
    },

    # -------------------------------------------------------------------------
    # PORTALS FIELDS (standardized)
    # -------------------------------------------------------------------------
    # These are the ONLY portal fields that should be used.
    # The dashboard Quick Links section displays these fields.
    #
    # Migration notes:
    #   granicus, granicus_archive -> video_archive
    #   wtv_stream, facebook -> live_stream
    #   agendalink, meetings -> agendas
    #   ecomment_live, online_comment -> ecomment
    #   destiny, legistar, civicclerk, primegov -> can keep as additional
    # -------------------------------------------------------------------------
    "portals": {
        "required": [
            ("agendas", "URL to agenda/minutes page"),
            ("live_stream", "URL to live stream (or null if none)"),
        ],
        "optional": [
            ("video_archive", "URL to recorded meetings (Granicus, etc)"),
            ("youtube", "YouTube channel URL"),
            ("ecomment", "eComment/online comment submission URL"),
        ],
    },

    # -------------------------------------------------------------------------
    # BROADCAST FIELDS
    # -------------------------------------------------------------------------
    "broadcast": {
        "required": [
            ("cable_channels", "Array of {provider, channel} objects"),
            ("live_stream", "URL to live stream"),
        ],
        "optional": [
            ("tv_channel", "TV channel name/brand"),
        ],
    },

    # -------------------------------------------------------------------------
    # CLERK FIELDS
    # -------------------------------------------------------------------------
    "clerk": {
        "required": [
            ("name", "Clerk's full name"),
            ("title", "Job title"),
            ("phone", "Phone number"),
            ("email", "Email address"),
        ],
        "optional": [
            ("fax", "Fax number"),
            ("address", "Office address"),
            ("deputy", "Deputy clerk name"),
        ],
    },

    # -------------------------------------------------------------------------
    # PUBLIC_COMMENT FIELDS
    # -------------------------------------------------------------------------
    "public_comment": {
        "required": [
            ("in_person", "Boolean: in-person comment allowed"),
            ("remote_live", "Boolean: live remote comment allowed"),
            ("ecomment", "Boolean: eComment system available"),
            ("written_email", "Boolean: written email comments accepted"),
            ("time_limit", "Speaker time limit (e.g., '3 minutes per speaker')"),
            ("email", "Email for public comments"),
        ],
        "optional": [
            ("deadline", "Comment submission deadline"),
            ("notes", "Additional notes about procedures"),
            ("ecomment_url", "URL to eComment system"),
            ("speaker_card", "Speaker card requirements"),
        ],
    },

    # -------------------------------------------------------------------------
    # COUNCIL FIELDS
    # -------------------------------------------------------------------------
    "council": {
        "required": [
            ("size", "Total council size including mayor"),
            ("districts", "Number of district seats (0 if at-large) - OR use 'wards' for Santa Ana"),
            ("at_large", "Number of at-large seats"),
            ("mayor_elected", "Boolean: mayor directly elected by voters"),
        ],
        "optional": [
            ("wards", "Number of ward seats (Santa Ana only, alternative to districts)"),
            ("term_length", "Standard term length in years"),
            ("expanded_date", "Date council expanded to districts"),
            ("notes", "Additional notes"),
        ],
    },

    # -------------------------------------------------------------------------
    # ELECTIONS FIELDS
    # -------------------------------------------------------------------------
    "elections": {
        "required": [
            ("next_election", "Date of next election 'YYYY-MM-DD'"),
            ("seats_up", "Array of seats up for election"),
            ("election_system", "by-district, by-ward, or at-large"),
        ],
        "optional": [
            ("term_length", "Term length in years"),
            ("term_limits", "Term limit info if applicable"),
        ],
    },
}


def get_required_fields(section: str) -> list:
    """Get list of required field names for a section."""
    if section in SCHEMA:
        return [f[0] for f in SCHEMA[section]["required"]]
    return []


def get_optional_fields(section: str) -> list:
    """Get list of optional field names for a section."""
    if section in SCHEMA:
        return [f[0] for f in SCHEMA[section]["optional"]]
    return []


def print_schema():
    """Print the schema in a human-readable format."""
    for section, fields in SCHEMA.items():
        print(f"\n{'='*60}")
        print(f" {section.upper()}")
        print(f"{'='*60}")

        print("\n  REQUIRED:")
        for name, desc in fields["required"]:
            print(f"    - {name}: {desc}")

        if fields["optional"]:
            print("\n  OPTIONAL:")
            for name, desc in fields["optional"]:
                print(f"    - {name}: {desc}")


if __name__ == "__main__":
    print_schema()
