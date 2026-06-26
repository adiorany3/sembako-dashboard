#!/usr/bin/env python3
"""
Update Saham IHSG & Bluechip - Daily during market hours
Runs: Mon-Fri at 09:00, 12:00, 15:30 WIB
"""

import sys
import os
sys.path.insert(0, '/root/sembako')

from create_saham_ihsg import update_ihsg_data, update_bluechip_data

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Updating IHSG & Saham data...")
    
    # Update all data
    ihsg_updated = update_ihsg_data()
    bluechip_updated = update_bluechip_data()
    
    if ihsg_updated and bluechip_updated:
        print("✅ Saham data updated successfully")
    else:
        print("⚠️ Some data may not have updated properly")

if __name__ == '__main__':
    from datetime import datetime
    main()
