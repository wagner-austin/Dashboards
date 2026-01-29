#!/usr/bin/env python3
"""
Add missing fields to all city YAML files based on the reference schema (Aliso Viejo).
Fields are added with null values where missing.

Usage:
    python add_missing_fields.py --dry-run   # Preview changes
    python add_missing_fields.py             # Apply changes
"""

import yaml
import sys
from pathlib import Path
from copy import deepcopy


# Preserve YAML formatting
class MyDumper(yaml.SafeDumper):
    pass

def str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

MyDumper.add_representer(str, str_representer)


def load_yaml(filepath):
    """Load a YAML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_yaml(filepath, data):
    """Save data to YAML file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=MyDumper, default_flow_style=False,
                  allow_unicode=True, sort_keys=False, width=120)


def ensure_field(data, path, default=None):
    """Ensure a field exists at the given path. Returns True if added."""
    parts = path.split('.')
    current = data

    for i, part in enumerate(parts[:-1]):
        if part not in current:
            current[part] = {}
        elif current[part] is None:
            current[part] = {}
        current = current[part]

    final_key = parts[-1]
    if final_key not in current:
        current[final_key] = default
        return True
    return False


def add_missing_fields(target: dict, reference: dict) -> list:
    """Add missing top-level and section fields from reference to target."""
    changes = []

    # Top-level fields to ensure exist
    top_level_order = ['city', 'city_name', 'website', 'council_url', 'last_updated',
                       'email', 'phone', 'instagram', 'members']

    for field in top_level_order:
        if field not in target and field in reference:
            if field in ['email', 'phone', 'instagram']:
                target[field] = None
                changes.append(f"Added {field}: null")

    # Reorder to put email/phone/instagram after last_updated
    if 'email' in target or 'phone' in target or 'instagram' in target:
        new_target = {}
        for key in ['city', 'city_name', 'website', 'council_url', 'last_updated']:
            if key in target:
                new_target[key] = target.pop(key)
        for key in ['email', 'phone', 'instagram']:
            if key in target:
                new_target[key] = target.pop(key)
        new_target.update(target)
        target.clear()
        target.update(new_target)

    # Meetings section
    if 'meetings' in target and 'meetings' in reference:
        ref_meetings = reference['meetings']
        tgt_meetings = target['meetings']

        if 'closed_session_time' not in tgt_meetings:
            tgt_meetings['closed_session_time'] = None
            changes.append("Added meetings.closed_session_time: null")

        if 'remote' not in tgt_meetings and 'remote' in ref_meetings:
            tgt_meetings['remote'] = {
                'zoom_url': None,
                'zoom_id': None,
                'zoom_passcode': None,
                'phone_numbers': None
            }
            changes.append("Added meetings.remote section")

    # Portals section
    if 'portals' in target and 'portals' in reference:
        ref_portals = reference['portals']
        tgt_portals = target['portals']

        if 'youtube' not in tgt_portals:
            tgt_portals['youtube'] = None
            changes.append("Added portals.youtube: null")

    # Clerk section
    if 'clerk' in target and 'clerk' in reference:
        ref_clerk = reference['clerk']
        tgt_clerk = target['clerk']

        if 'fax' not in tgt_clerk:
            tgt_clerk['fax'] = None
            changes.append("Added clerk.fax: null")

        if 'address' not in tgt_clerk:
            tgt_clerk['address'] = None
            changes.append("Added clerk.address: null")

    # Public comment section
    if 'public_comment' in target and 'public_comment' in reference:
        ref_pc = reference['public_comment']
        tgt_pc = target['public_comment']

        if 'deadline' not in tgt_pc:
            tgt_pc['deadline'] = None
            changes.append("Added public_comment.deadline: null")

        if 'notes' not in tgt_pc:
            tgt_pc['notes'] = None
            changes.append("Added public_comment.notes: null")

    # Council section
    if 'council' in target and 'council' in reference:
        ref_council = reference['council']
        tgt_council = target['council']

        if 'expanded_date' not in tgt_council:
            tgt_council['expanded_date'] = None
            changes.append("Added council.expanded_date: null")

        if 'notes' not in tgt_council:
            tgt_council['notes'] = None
            changes.append("Added council.notes: null")

    # Elections section
    if 'elections' in target and 'elections' in reference:
        ref_elections = reference['elections']
        tgt_elections = target['elections']

        if 'mayor_term_length' not in tgt_elections:
            tgt_elections['mayor_term_length'] = None
            changes.append("Added elections.mayor_term_length: null")

        if 'districting_info' not in tgt_elections:
            tgt_elections['districting_info'] = None
            changes.append("Added elections.districting_info: null")

        if 'transition_note' not in tgt_elections:
            tgt_elections['transition_note'] = None
            changes.append("Added elections.transition_note: null")

        # Term limit fields
        term_limit_fields = [
            'term_limit', 'term_limit_type', 'term_limit_cooldown',
            'term_limit_cooldown_unit', 'term_limit_effective',
            'term_limit_notes', 'term_limit_source'
        ]
        for field in term_limit_fields:
            if field not in tgt_elections:
                tgt_elections[field] = None
                changes.append(f"Added elections.{field}: null")

        # Cycle pattern
        if 'cycle_pattern' not in tgt_elections and 'cycle_pattern' in ref_elections:
            tgt_elections['cycle_pattern'] = None
            changes.append("Added elections.cycle_pattern: null")

        # Candidate info
        if 'candidate_info' not in tgt_elections and 'candidate_info' in ref_elections:
            tgt_elections['candidate_info'] = None
            changes.append("Added elections.candidate_info: null")

        # Nomination period
        if 'nomination_period' not in tgt_elections:
            tgt_elections['nomination_period'] = None
            changes.append("Added elections.nomination_period: null")

        # Sources
        if 'results_source' not in tgt_elections:
            tgt_elections['results_source'] = None
            changes.append("Added elections.results_source: null")

        if 'source' not in tgt_elections:
            tgt_elections['source'] = None
            changes.append("Added elections.source: null")

        # History
        if 'history' not in tgt_elections:
            tgt_elections['history'] = []
            changes.append("Added elections.history: []")

    return changes


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Add missing fields to city YAML files')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    parser.add_argument('--reference', default='aliso-viejo', help='Reference city')
    parser.add_argument('city', nargs='?', help='Process single city')
    args = parser.parse_args()

    data_dir = Path(__file__).parent / '_council_data'

    # Load reference
    ref_path = data_dir / f'{args.reference}.yaml'
    reference = load_yaml(ref_path)

    print(f"Reference: {reference.get('city_name', args.reference)}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLY CHANGES'}")
    print("=" * 60)

    # Get files to process
    if args.city:
        yaml_files = [data_dir / f'{args.city}.yaml']
    else:
        yaml_files = sorted(data_dir.glob('*.yaml'))
        yaml_files = [f for f in yaml_files if f.name != f'{args.reference}.yaml']

    total_changes = 0
    files_changed = 0

    for filepath in yaml_files:
        target = load_yaml(filepath)
        city_name = target.get('city_name', filepath.stem)

        changes = add_missing_fields(target, reference)

        if changes:
            files_changed += 1
            total_changes += len(changes)
            print(f"\n{city_name} ({len(changes)} changes):")
            for change in changes:
                print(f"  + {change}")

            if not args.dry_run:
                save_yaml(filepath, target)

    print(f"\n{'=' * 60}")
    print(f"Summary: {files_changed} files, {total_changes} total changes")
    if args.dry_run:
        print("(No files modified - use without --dry-run to apply)")


if __name__ == '__main__':
    main()
