#!/usr/bin/env python3
"""CLI wrapper for dedup utilities."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.dedup import dedup_all, dedup_excel_file
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true')
parser.add_argument('--file', help='Specific file')
args = parser.parse_args()

if args.file:
    dedup_excel_file(os.path.join(os.path.expanduser('~/sembako/data'), args.file), dry_run=args.dry_run)
else:
    dedup_all(dry_run=args.dry_run)
