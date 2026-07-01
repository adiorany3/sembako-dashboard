"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def data_dir():
    """Return the data directory path."""
    return os.path.expanduser('~/sembako/data')


@pytest.fixture
def temp_excel(tmp_path):
    """Create a temp Excel file with sample data for testing."""
    import openpyxl
    filepath = tmp_path / "test_data.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "TestSheet"
    ws.append(["Tanggal", "Komoditas", "Harga", "Sumber"])
    ws.append(["2026-06-30", "Beras Premium", 15000, "test"])
    ws.append(["2026-06-30", "Gula Pasir", 17500, "test"])
    ws.append(["2026-06-29", "Beras Premium", 15200, "test"])
    ws.append(["2026-06-29", "Gula Pasir", 17500, "test"])
    ws.append(["2026-06-28", "Beras Premium", 15100, "test"])
    ws.append(["2026-06-28", "Gula Pasir", 17400, "test"])
    wb.save(str(filepath))
    return filepath


@pytest.fixture
def temp_excel_with_dupes(tmp_path):
    """Create a temp Excel file with duplicate rows for dedup testing."""
    import openpyxl
    filepath = tmp_path / "test_dupes.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "TestSheet"
    ws.append(["Tanggal", "Komoditas", "Harga", "Sumber"])
    ws.append(["2026-06-30", "Beras", 15000, "source1"])
    ws.append(["2026-06-30", "Beras", 15000, "source1"])
    ws.append(["2026-06-30", "Beras", 15000, "source1"])
    ws.append(["2026-06-30", "Gula", 17500, "source1"])
    ws.append(["2026-06-30", "Gula", 17500, "source1"])
    wb.save(str(filepath))
    return filepath
