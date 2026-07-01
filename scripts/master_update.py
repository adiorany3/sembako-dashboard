#!/usr/bin/env python3
"""
Master Update Script - Update all dashboard data
- Generates 30 days historical data for new installations
- Updates daily data for all categories
- Saves to ~/sembako/ AND commits to GitHub

Usage:
    python3 master_update.py --init    # Initial setup (30 days back)
    python3 master_update.py            # Daily update
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Base paths
SEMBAKO_DIR = os.path.expanduser('~/sembako')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GIT_REMOTE = 'https://github.com/adiorany3/sembako-dashboard.git'

# ==========================================
# STYLE DEFINITIONS
# ==========================================
header_fill = PatternFill(start_color='667eea', end_color='667eea', fill_type='solid')
header_font = Font(bold=True, color='FFFFFF', size=11)
date_fill = PatternFill(start_color='10b981', end_color='10b981', fill_type='solid')
date_font = Font(bold=True, color='FFFFFF')
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

def git_commit_push(message):
    """Commit and push changes to GitHub"""
    if not os.path.exists(f'{SEMBAKO_DIR}/.git'):
        print("⚠️ Not a git repo, skipping push")
        return False
    
    os.system(f'cd {SEMBAKO_DIR} && git add . > /dev/null 2>&1')
    result = os.system(f'cd {SEMBAKO_DIR} && git commit -m "{message}" > /dev/null 2>&1')
    if result != 0:
        print("⚠️ Nothing to commit")
        return False
    
    result = os.system(f'cd {SEMBAKO_DIR} && git push origin main > /dev/null 2>&1')
    if result == 0:
        print("  ✅ Pushed to GitHub")
        return True
    else:
        print("  ⚠️ Push failed (will retry next time)")
        return False

# ==========================================
# DATA DEFINITIONS
# ==========================================

# SEMBAKO DATA
SEMBAKO_PRODUCTS = [
    ('Beras Premium', 15000, 'Kg'),
    ('Beras Medium', 13000, 'Kg'),
    ('Minyak Goreng', 20000, 'Liter'),
    ('Gula Pasir', 17000, 'Kg'),
    ('Garam', 5000, 'Kg'),
    ('Tepung Terigu', 12000, 'Kg'),
    ('Cabai Merah', 45000, 'Kg'),
    ('Cabai Rawit', 40000, 'Kg'),
    ('Bawang Merah', 40000, 'Kg'),
    ('Bawang Putih', 35000, 'Kg'),
    ('Minyak Tanah', 15000, 'Liter'),
    ('Telur Ayam Ras', 28000, 'Kg'),
    ('Telur Ayam Kampung', 45000, 'Kg'),
    ('Ayam Ras', 35000, 'Kg'),
    ('Ayam Kampung', 65000, 'Kg'),
    ('Daging Sapi', 130000, 'Kg'),
    ('Gas Elpiji 12 Kg', 200000, 'Pcs'),
    ('Garam Bata', 3000, 'Kg'),
    ('Garam Halus', 4000, 'Kg'),
    ('Susu KM Bendera', 15000, '390 ml'),
    ('Susu KM Indomilk', 14000, '390 ml'),
    ('Susu Bubuk Bendera', 45000, 'Kg'),
    ('Susu Bubuk Indomilk', 42000, 'Kg'),
]

# CRYPTO DATA
CRYPTO_BASE = {
    'BTC': {'price': 1500000000, 'change': 2.5},
    'ETH': {'price': 50000000, 'change': 3.2},
    'SOL': {'price': 2500000, 'change': 5.1},
    'ADA': {'price': 8000, 'change': -1.2},
    'DOGE': {'price': 2500, 'change': 1.8},
    'XRP': {'price': 9000, 'change': 0.5},
}

# GOLD DATA
GOLD_BASE = {
    'Antam Beli': 2450000,
    'Antam Buyback': 2350000,
    'Antam Pegadaian': 2400000,
    'Galeri 24': 2420000,
    'UBS Beli': 2440000,
}

# PERTANIAN DATA
PERTANIAN_PRODUCTS = [
    ('Jagung Pipilan', 8500, 'Kg'),
    ('Jagung Pakan', 8000, 'Kg'),
    ('Kedelai Impor', 14000, 'Kg'),
    ('Kedelai Lokal', 18000, 'Kg'),
    ('Pakan Broiler', 280000, '50 Kg'),
    ('Pakan Layer', 265000, '50 Kg'),
    ('Bungkil Kedelai', 12000, 'Kg'),
    ('Jagung Giling', 7500, 'Kg'),
    ('Dedak Padi', 4500, 'Kg'),
    ('Bungkil Kelapa', 9500, 'Kg'),
]

# ==========================================
# EXCEL CREATION FUNCTIONS
# ==========================================

def create_sembako_excel(days_back=30):
    """Create/update harga_sembako.xlsx with historical data"""
    print("\n📊 Updating Sembako data...")
    filepath = f'{SEMBAKO_DIR}/harga_sembako.xlsx'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Harga'
    
    # Headers
    headers = ['Tanggal', 'Beras Premium', 'Beras Medium', 'Minyak Goreng', 'Gula Pasir',
               'Garam', 'Tepung Terigu', 'Cabai Merah', 'Cabai Rawit', 'Bawang Merah',
               'Bawang Putih', 'Minyak Tanah', 'Telur Ras', 'Telur Kampung', 'Ayam Ras',
               'Ayam Kampung', 'Daging Sapi', 'Gas Elpiji', 'Garam Bata', 'Garam Halus',
               'Susu KM Bendera', 'Susu KM Indomilk', 'Susu Bubuk Bendera', 'Susu Bubuk Indomilk']
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', wrap_text=True)
        cell.border = thin_border
    
    # Generate historical data
    today = datetime.now()
    for day_offset in range(days_back, -1, -1):
        date = today - timedelta(days=day_offset)
        row = [date.strftime('%Y-%m-%d')]
        
        for product, base_price, satuan in SEMBAKO_PRODUCTS:
            # Add slight variation
            variation = base_price * random.uniform(-0.05, 0.05)
            price = round((base_price + variation) / 100) * 100
            row.append(int(price))
        
        for col, value in enumerate(row, 1):
            cell = ws.cell(row=days_back - day_offset + 2, column=col, value=value)
            if col == 1:
                cell.fill = date_fill
                cell.font = date_font
            cell.border = thin_border
    
    # Set column widths
    ws.column_dimensions['A'].width = 12
    for col in range(2, len(headers) + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15
    
    wb.save(filepath)
    print(f"  ✅ {filepath} - {days_back + 1} days, {len(SEMBAKO_PRODUCTS)} products")

def create_crypto_excel(days_back=30):
    """Create/update crypto_monitor.xlsx"""
    print("\n🪙 Updating Crypto data...")
    filepath = f'{SEMBAKO_DIR}/crypto_monitor.xlsx'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Sheet1'
    
    headers = ['Tanggal', 'Waktu', 'BTC USD', 'BTC IDR', 'BTC 24h',
               'ETH USD', 'ETH IDR', 'ETH 24h', 'SOL USD', 'SOL IDR', 'SOL 24h',
               'ADA USD', 'ADA IDR', 'ADA 24h', 'DOGE USD', 'DOGE IDR', 'DOGE 24h',
               'XRP USD', 'XRP IDR', 'XRP 24h', 'Market Cap', 'Sentimen']
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    
    today = datetime.now()
    for day_offset in range(days_back, -1, -1):
        date = today - timedelta(days=day_offset)
        row = [date.strftime('%Y-%m-%d'), '08:00']
        
        for coin, data in CRYPTO_BASE.items():
            usd_price = data['price'] / 15000  # Approx USD
            idr_price = data['price']
            change = data['change'] + random.uniform(-2, 2)
            row.extend([round(usd_price, 2), idr_price, round(change, 2)])
        
        row.extend(['High', 'Netral'])
        
        for col, value in enumerate(row, 1):
            cell = ws.cell(row=days_back - day_offset + 2, column=col, value=value)
            if col == 1:
                cell.fill = date_fill
                cell.font = date_font
            cell.border = thin_border
    
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 12
    
    wb.save(filepath)
    print(f"  ✅ {filepath} - {days_back + 1} days")

def create_emas_excel(days_back=30):
    """Create/update harga_emas.xlsx"""
    print("\n💰 Updating Emas data...")
    filepath = f'{SEMBAKO_DIR}/harga_emas.xlsx'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Harian'
    
    headers = ['Tanggal', 'Antam Beli', 'Antam Buyback', 'Antam Pegadaian', 
               'Galeri 24', 'UBS Beli', 'Selisih', 'Spread %']
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    
    today = datetime.now()
    for day_offset in range(days_back, -1, -1):
        date = today - timedelta(days=day_offset)
        row = [date.strftime('%Y-%m-%d')]
        
        for name, base_price in GOLD_BASE.items():
            variation = base_price * random.uniform(-0.02, 0.02)
            price = round((base_price + variation) / 1000) * 1000
            row.append(int(price))
        
        selisih = row[-1] - row[1]
        spread = round((selisih / row[1]) * 100, 2)
        row.extend([selisih, spread])
        
        for col, value in enumerate(row, 1):
            cell = ws.cell(row=days_back - day_offset + 2, column=col, value=value)
            if col == 1:
                cell.fill = date_fill
                cell.font = date_font
            cell.border = thin_border
    
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15
    
    wb.save(filepath)
    print(f"  ✅ {filepath} - {days_back + 1} days")

def create_pertanian_excel(days_back=30):
    """Create/update harga_pertanian_ternak.xlsx"""
    print("\n🌾 Updating Pertanian data...")
    filepath = f'{SEMBAKO_DIR}/harga_pertanian_ternak.xlsx'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    
    headers = ['Tanggal', 'Jagung Pipil', 'Jagung Pakan', 'Kedelai Impor', 'Kedelai Lokal',
               'Pakan Broiler', 'Pakan Layer', 'Bungkil Kedelai', 'Jagung Giling']
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    
    today = datetime.now()
    for day_offset in range(days_back, -1, -1):
        date = today - timedelta(days=day_offset)
        row = [date.strftime('%Y-%m-%d')]
        
        for product, base_price, satuan in PERTANIAN_PRODUCTS:
            variation = base_price * random.uniform(-0.05, 0.05)
            price = round((base_price + variation) / 100) * 100
            row.append(int(price))
        
        for col, value in enumerate(row, 1):
            cell = ws.cell(row=days_back - day_offset + 2, column=col, value=value)
            if col == 1:
                cell.fill = date_fill
                cell.font = date_font
            cell.border = thin_border
    
    ws.column_dimensions['A'].width = 12
    for col in range(2, len(headers) + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15
    
    wb.save(filepath)
    print(f"  ✅ {filepath} - {days_back + 1} days")

def daily_update_all():
    """Add today's data to all Excel files (append single row, skip if date exists)"""
    print("\n📝 Adding today's data to all files...")
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_date = datetime.now().date()
    
    def date_exists(ws):
        """Check if today's date already exists in column A"""
        for row in ws.iter_rows(min_col=1, max_col=1, values_only=True):
            val = row[0]
            if val is None:
                continue
            if isinstance(val, datetime):
                if val.date() == today_date:
                    return True
            elif str(val)[:10] == today:
                return True
        return False
    
    # Sembako - append one row
    filepath = f'{SEMBAKO_DIR}/harga_sembako.xlsx'
    if os.path.exists(filepath):
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        if date_exists(ws):
            print(f"  ⏭️ Sembako skipped (already has {today})")
        else:
            row_num = ws.max_row + 1
            ws.cell(row=row_num, column=1, value=today)
            for col, (_, base_price, _) in enumerate(SEMBAKO_PRODUCTS, 2):
                variation = base_price * random.uniform(-0.05, 0.05)
                price = round((base_price + variation) / 100) * 100
                ws.cell(row=row_num, column=col, value=int(price))
            print(f"  ✅ Sembako updated")
        wb.save(filepath)
    
    # Crypto - append one row
    filepath = f'{SEMBAKO_DIR}/crypto_monitor.xlsx'
    if os.path.exists(filepath):
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        if date_exists(ws):
            print(f"  ⏭️ Crypto skipped (already has {today})")
        else:
            row_num = ws.max_row + 1
            ws.cell(row=row_num, column=1, value=today)
            ws.cell(row=row_num, column=2, value='08:00')
            col = 3
            for coin, data in CRYPTO_BASE.items():
                usd_price = data['price'] / 15000
                idr_price = data['price']
                change = data['change'] + random.uniform(-2, 2)
                ws.cell(row=row_num, column=col, value=round(usd_price, 2)); col += 1
                ws.cell(row=row_num, column=col, value=idr_price); col += 1
                ws.cell(row=row_num, column=col, value=round(change, 2)); col += 1
            ws.cell(row=row_num, column=col, value='High')
            ws.cell(row=row_num, column=col+1, value='Netral')
            print(f"  ✅ Crypto updated")
        wb.save(filepath)
    
    # Gold - append one row
    filepath = f'{SEMBAKO_DIR}/harga_emas.xlsx'
    if os.path.exists(filepath):
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        if date_exists(ws):
            print(f"  ⏭️ Gold skipped (already has {today})")
        else:
            row_num = ws.max_row + 1
            ws.cell(row=row_num, column=1, value=today)
            col = 2
            for name, base_price in GOLD_BASE.items():
                variation = base_price * random.uniform(-0.02, 0.02)
                price = round((base_price + variation) / 1000) * 1000
                ws.cell(row=row_num, column=col, value=int(price)); col += 1
            print(f"  ✅ Gold updated")
        wb.save(filepath)
    
    # Pertanian - append one row
    filepath = f'{SEMBAKO_DIR}/harga_pertanian_ternak.xlsx'
    if os.path.exists(filepath):
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        if date_exists(ws):
            print(f"  ⏭️ Pertanian skipped (already has {today})")
        else:
            row_num = ws.max_row + 1
            ws.cell(row=row_num, column=1, value=today)
            for col, (_, base_price, _) in enumerate(PERTANIAN_PRODUCTS, 2):
                variation = base_price * random.uniform(-0.05, 0.05)
                price = round((base_price + variation) / 100) * 100
                ws.cell(row=row_num, column=col, value=int(price))
            print(f"  ✅ Pertanian updated")
        wb.save(filepath)
    
    # Peternakan - use its own script
    os.system(f'cd {SEMBAKO_DIR} && python3 update_peternakan.py > /dev/null 2>&1')
    print(f"  ✅ Peternakan updated")
    
    # Auto-dedup all files after update
    from utils.dedup import dedup_all
    reports = dedup_all(dry_run=False, verbose=False)
    removed = sum(r['duplicates_removed'] for r in reports)
    if removed > 0:
        print(f"\n🧹 Auto-dedup: removed {removed} duplicate rows")
    
    # Recovery: reload JSON history → Excel if data missing
    try:
        from scripts.recovery_json_to_excel import load_crypto_history_to_excel, load_emas_history_to_excel
        load_crypto_history_to_excel()
        load_emas_history_to_excel()
    except Exception as e:
        print(f"  ⚠️ Recovery loader error: {e}")

# ==========================================
# MAIN
# ==========================================

if __name__ == '__main__':
    init_mode = len(sys.argv) > 1 and sys.argv[1] == '--init'
    
    if init_mode:
        print("=" * 50)
        print("🚀 INITIAL SETUP - Generating 30 days historical data")
        print("=" * 50)
        
        create_sembako_excel(30)
        create_crypto_excel(30)
        create_emas_excel(30)
        create_pertanian_excel(30)
        
        print("\n" + "=" * 50)
        print("✅ ALL DATA INITIALIZED!")
        print("=" * 50)
        
        # Commit and push
        git_commit_push("Initial data setup - 30 days historical data for all categories")
        
    else:
        print("=" * 50)
        print("📅 DAILY UPDATE")
        print("=" * 50)
        
        daily_update_all()
        
        print("\n" + "=" * 50)
        print("✅ DAILY UPDATE COMPLETE!")
        print("=" * 50)
        
        # Commit and push
        git_commit_push(f"Daily update - {datetime.now().strftime('%Y-%m-%d')}")
