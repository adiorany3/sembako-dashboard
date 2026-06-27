#!/usr/bin/env python3
"""
Update Saham IHSG & Bluechip - Daily during market hours
Runs: Mon-Fri at 09:00, 12:00, 15:30 WIB
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from create_saham_ihsg import create_ihsg_excel
from datetime import datetime

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Updating IHSG & Saham data...")
    
    try:
        # Generate/regenerate with 30 days back
        result = create_ihsg_excel(days_back=30)
        print(result)
    except Exception as e:
        print(f"Error updating saham data: {e}")

if __name__ == "__main__":
    main()
