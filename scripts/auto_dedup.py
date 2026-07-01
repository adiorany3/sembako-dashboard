#!/usr/bin/env python3
"""
Auto-dedup hook - run after every data update.
Ensures no duplicate rows exist per date per file.
Usage: python3 auto_dedup.py [--dry-run]
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.dedup import dedup_all

if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    reports = dedup_all(dry_run=dry_run)
    
    removed = sum(r['duplicates_removed'] for r in reports)
    errors = [r for r in reports if r['status'] == 'error']
    
    if removed > 0 and not dry_run:
        print(f"\n✅ Auto-dedup complete: {removed} duplicates removed")
    elif removed == 0:
        print("\n✅ No duplicates found")
    
    if errors:
        print(f"\n⚠️ {len(errors)} file(s) had errors:")
        for e in errors:
            print(f"  - {e['file']}: {e['error']}")
