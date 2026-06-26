#!/usr/bin/env python3
"""
Proses nota/foto struk → catat keuangan.
Support: foto nota (OCR), input manual, format teks.
"""
import re
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~/sembako"))
from create_keuangan_excel import add_transaksi, update_ringkasan

HISTORY_PATH = os.path.expanduser("~/sembako/keuangan_history.json")

KATEGORI_KEYWORDS = {
    "Makanan & Minuman": ["makan", "minum", "nasi", "ayam", "ikan", "sayur", "buah", "roti", "kopi", "teh", "susu", "air", "jus", "mie", "bakso", "soto", "warung", "resto", "kafe", "gofood", "grabfood"],
    "Transportasi": ["grab", "gojek", "uber", "bensin", "solar", "parkir", "tol", "tiket", "kereta", "bus", "pesawat", "ojol"],
    "Belanja Rumah Tangga": ["sabun", "shampoo", "deterjen", "tisu", "minyak goreng", "beras", "gula", "garam", "indomaret", "alfamart", "supermarket", "pasar"],
    "Tagihan & Utilitas": ["listrik", "air", "pdam", "internet", "wifi", "pulsa", "token", "pln", "bpjs", "asuransi"],
    "Kesehatan": ["obat", "dokter", "rumah sakit", "apotek", "vitamin", "klinik", "laboratorium"],
    "Pendidikan": ["sekolah", "kuliah", "buku", "alat tulis", "kursus", "les", "SPP"],
    "Hiburan": ["bioskop", "netflix", "spotify", "game", "liburan", "hotel", "tiket wisata"],
    "Pakaian": ["baju", "celana", "sepatu", "sandal", "jaket", "topi", "kaus"],
    "Pertanian & Ternak": ["pakan", "bibit", "pupuk", "obat hama", "jagung", "kedelai", "ternak", "ayam", "sapi", "kambing"],
    "Investasi": ["emas", "saham", "crypto", "bitcoin", "deposito", "reksadana", "obligasi"],
}

def kategorikan(text):
    """Auto-detect category from text."""
    text_lower = text.lower()
    for kategori, keywords in KATEGORI_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return kategori
    return "Lainnya"

def parse_nota_text(text):
    """
    Parse nota dari text (hasil OCR atau manual).
    Extract: tanggal, item, harga, total.
    """
    lines = text.strip().split('\n')
    items = []
    tanggal = datetime.now().strftime("%Y-%m-%d")
    total = 0
    
    # Try to find date
    for line in lines:
        # DD/MM/YYYY or DD-MM-YYYY
        m = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', line)
        if m:
            d, mo, y = m.groups()
            if len(y) == 2: y = "20" + y
            tanggal = f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
            break
        # "23 Juni 2026" format
        m = re.search(r'(\d{1,2})\s+(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+(\d{4})', line, re.I)
        if m:
            bulan_map = {"Januari":"01","Februari":"02","Maret":"03","April":"04","Mei":"05","Juni":"06",
                        "Juli":"07","Agustus":"08","September":"09","Oktober":"10","November":"11","Desember":"12"}
            d = m.group(1).zfill(2)
            mo = bulan_map.get(m.group(2), "01")
            y = m.group(3)
            tanggal = f"{y}-{mo}-{d}"
            break
    
    # Extract items with prices
    for line in lines:
        # Pattern: "item name    Rp 25.000" or "item    25000" or "item    25.000"
        m = re.search(r'(.+?)\s+(?:Rp\.?\s*)?([\d.,]+)(?:\s*$|\s*x\s*\d)', line, re.I)
        if m:
            name = m.group(1).strip()
            price_str = m.group(2).replace('.', '').replace(',', '')
            try:
                price = int(price_str)
                if 100 <= price <= 100000000:  # reasonable range
                    items.append({"name": name, "price": price})
            except:
                pass
        
        # Find total
        m_total = re.search(r'(?:total|jumlah|grand\s*total)\s*(?:Rp\.?\s*)?([\d.,]+)', line, re.I)
        if m_total:
            total_str = m_total.group(1).replace('.', '').replace(',', '')
            try:
                total = int(total_str)
            except:
                pass
    
    if not total and items:
        total = sum(i["price"] for i in items)
    
    return {
        "tanggal": tanggal,
        "items": items,
        "total": total,
        "deskripsi": ", ".join(i["name"] for i in items[:3]) if items else "Transaksi dari nota"
    }

def proses_nota_file(file_path):
    """Process a receipt image/PDF."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.jpg', '.jpeg', '.png', '.webp']:
        # Image - use OCR
        try:
            from PIL import Image
            import pytesseract
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='ind+eng')
            return parse_nota_text(text)
        except Exception as e:
            print(f"⚠️ OCR error: {e}")
            return None
    
    elif ext == '.pdf':
        # PDF - use pymupdf
        try:
            import pymupdf
            doc = pymupdf.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return parse_nota_text(text)
        except Exception as e:
            print(f"⚠️ PDF error: {e}")
            return None
    
    elif ext == '.txt':
        with open(file_path) as f:
            return parse_nota_text(f.read())
    
    return None

def proses_manual(tanggal, jenis, kategori, deskripsi, jumlah, metode=""):
    """Manual entry."""
    add_transaksi(tanggal, jenis, kategori, deskripsi, jumlah, metode)
    update_ringkasan()

def proses_teks_nota(text, jenis="Pengeluaran", metode=""):
    """Process receipt from text input."""
    parsed = parse_nota_text(text)
    
    if parsed["total"] > 0:
        kategori = kategorikan(parsed["deskripsi"])
        add_transaksi(parsed["tanggal"], jenis, kategori, parsed["deskripsi"], 
                     parsed["total"], metode, nota="OCR")
        update_ringkasan()
        return parsed
    
    return None

def get_summary(bulan=None):
    """Get financial summary."""
    import openpyxl
    if not os.path.exists(EXCEL_PATH):
        return None
    
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb["Transaksi"]
    
    if not bulan:
        bulan = datetime.now().strftime("%Y-%m")
    
    masuk = 0
    keluar = 0
    transaksi = []
    
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] and str(row[0]).startswith(bulan):
            transaksi.append(row)
            if row[1] == "Pemasukan":
                masuk += row[4] or 0
            else:
                keluar += row[4] or 0
    
    return {
        "bulan": bulan,
        "pemasukan": masuk,
        "pengeluaran": keluar,
        "saldo": masuk - keluar,
        "transaksi": len(transaksi)
    }

EXCEL_PATH = os.path.expanduser("~/sembako/keuangan.xlsx")

if __name__ == "__main__":
    # Test
    from create_keuangan_excel import add_transaksi, update_ringkasan
    print("✅ Modul keuangan siap")
    print("Gunakan: proses_manual(), proses_teks_nota(), atau proses_nota_file()")
