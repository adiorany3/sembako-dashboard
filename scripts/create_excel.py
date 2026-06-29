import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import LineChart, Reference, BarChart
from datetime import datetime
import os

EXCEL_PATH = os.path.expanduser("~/sembako/data/harga_sembako.xlsx")

def create_or_load_workbook():
    if os.path.exists(EXCEL_PATH):
        wb = openpyxl.load_workbook(EXCEL_PATH)
        ws = wb.active
        return wb, ws
    return create_new_workbook()

def create_new_workbook():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Harga Sembako"
    
    hf = Font(bold=True, color="FFFFFF", size=10)
    hfill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
    ha = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ca = Alignment(horizontal="center", vertical="center")
    thin = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )
    
    headers = [
        "Tanggal",
        "Beras Premium\n(Rp/kg)", "Beras Medium\n(Rp/kg)",
        "Gula Putih\n(Rp/kg)", "Minyak Goreng\nCurah (Rp/kg)",
        "Minyak Goreng\nKemasan (Rp/ltr)",
        "Telur Ayam Ras\n(Rp/kg)", "Telur Ayam Kampung\n(Rp/kg)",
        "Daging Ayam Ras\n(Rp/kg)", "Daging Ayam Kampung\n(Rp/kg)",
        "Daging Sapi\n(Rp/kg)",
        "Cabai Merah\nKeriting (Rp/kg)", "Cabai Rawit\nMerah (Rp/kg)",
        "Bawang Merah\n(Rp/kg)", "Bawang Putih\n(Rp/kg)",
        "Garam Halus\n(Rp/kg)", "Gas Elpiji\n(Rp)",
        "Sumber"
    ]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = hf
        cell.fill = hfill
        cell.alignment = ha
        cell.border = thin
    
    # Category sub-headers coloring
    cat_colors = {
        range(2, 4): "4472C4",    # Beras - biru
        range(4, 7): "548235",    # Minyak/Gula - hijau
        range(7, 9): "ED7D31",    # Telur - oranye
        range(9, 11): "C00000",   # Daging ayam - merah
        range(11, 12): "7030A0",  # Daging sapi - ungu
        range(12, 16): "BF8F00",  # Bumbu - kuning
        range(16, 18): "808080",  # Lainnya - abu
    }
    for cols, color in cat_colors.items():
        for col in cols:
            ws.cell(row=1, column=col).fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
    
    widths = [13, 16, 16, 14, 18, 20, 16, 18, 16, 18, 14, 18, 18, 16, 16, 14, 12, 25]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    
    ws.row_dimensions[1].height = 40
    ws.freeze_panes = "B2"
    return wb, ws

def add_row(tanggal, data_dict, sumber="Siskaperbapo Jatim"):
    """
    data_dict keys: beras_premium, beras_medium, gula, minyak_curah, minyak_kemasan,
    telur_ras, telur_kampung, ayam_ras, ayam_kampung, sapi,
    cabai_keriting, cabai_rawit, bawang_merah, bawang_putih, garam, elpiji
    """
    wb, ws = create_or_load_workbook()
    ca = Alignment(horizontal="center", vertical="center")
    thin = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )
    
    row = ws.max_row + 1
    
    keys_order = [
        "beras_premium", "beras_medium", "gula", "minyak_curah", "minyak_kemasan",
        "telur_ras", "telur_kampung", "ayam_ras", "ayam_kampung", "sapi",
        "cabai_keriting", "cabai_rawit", "bawang_merah", "bawang_putih", "garam", "elpiji"
    ]
    
    c = ws.cell(row=row, column=1, value=tanggal)
    c.alignment = ca; c.border = thin
    
    for i, key in enumerate(keys_order, 2):
        val = data_dict.get(key, 0)
        c = ws.cell(row=row, column=i, value=val)
        c.alignment = ca; c.border = thin
        if val: c.number_format = '#,##0'
    
    c = ws.cell(row=row, column=18, value=sumber)
    c.alignment = ca; c.border = thin
    
    wb.save(EXCEL_PATH)
    print(f"Row added: {tanggal}")
    return EXCEL_PATH

if __name__ == "__main__":
    # Data 21 Juni 2026 (dari Siskaperbapo Jatim via detik.com)
    add_row("2026-06-21", {
        "beras_premium": 15010, "beras_medium": 12953,
        "gula": 17166, "minyak_curah": 20462, "minyak_kemasan": 21708,
        "telur_ras": 25198, "telur_kampung": 46663,
        "ayam_ras": 32256, "ayam_kampung": 66888,
        "sapi": 126568,
        "cabai_keriting": 37870, "cabai_rawit": 57232,
        "bawang_merah": 42529, "bawang_putih": 35265,
        "garam": 9662, "elpiji": 20092
    })
    
    # Data 23 Juni 2026 (sama, belum ada update baru)
    add_row("2026-06-23", {
        "beras_premium": 15010, "beras_medium": 12953,
        "gula": 17166, "minyak_curah": 20462, "minyak_kemasan": 21708,
        "telur_ras": 25198, "telur_kampung": 46663,
        "ayam_ras": 32256, "ayam_kampung": 66888,
        "sapi": 126568,
        "cabai_keriting": 37870, "cabai_rawit": 57232,
        "bawang_merah": 42529, "bawang_putih": 35265,
        "garam": 9662, "elpiji": 20092
    })
    
    print(f"File saved: {EXCEL_PATH}")
