"""
Data validation utilities.
Provides consistent validation for all data types.
"""
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Import config
try:
    from utils.config import STALE_THRESHOLDS, STATUS_VALID, STATUS_STALE, STATUS_FAILED, STATUS_ESTIMATED
except ImportError:
    STATUS_VALID = 'valid'
    STATUS_STALE = 'stale'
    STATUS_FAILED = 'failed'
    STATUS_ESTIMATED = 'estimated'
    STALE_THRESHOLDS = {
        'crypto': 6,
        'sembako': 48,
        'emas': 24,
        'kurs': 24,
        'saham': 24,
        'cuaca': 12,
        'pertanian': 168,
        'peternakan': 168,
    }


def validate_price(price, min_price: int = 100, max_price: int = 100000000) -> Tuple[bool, str]:
    """
    Validate price is within reasonable range.
    Returns (is_valid, error_message).
    """
    if price is None or price == '':
        return False, "Price is empty"
    
    try:
        p = int(price)
        if p <= 0:
            return False, "Price must be positive"
        if p < min_price:
            return False, f"Price too low (min {min_price})"
        if p > max_price:
            return False, f"Price too high (max {max_price})"
        return True, ""
    except (ValueError, TypeError):
        return False, f"Invalid price format: {price}"


def validate_date(date_val, max_age_days: int = 365) -> Tuple[bool, str]:
    """
    Validate date is within reasonable range.
    Returns (is_valid, error_message).
    """
    if not date_val:
        return False, "Date is empty"
    
    # Try to parse date
    if isinstance(date_val, str):
        date_str = date_val[:10]  # YYYY-MM-DD
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return False, f"Invalid date format: {date_val}"
    elif isinstance(date_val, datetime):
        dt = date_val
    else:
        return False, f"Unknown date type: {type(date_val)}"
    
    # Check not too old
    age = datetime.now() - dt
    if age.days > max_age_days:
        return False, f"Date too old: {age.days} days"
    
    # Check not in future
    if dt > datetime.now():
        return False, "Date is in the future"
    
    return True, ""


def validate_percentage(pct: float, max_val: float = 100.0) -> Tuple[bool, str]:
    """Validate percentage."""
    try:
        p = float(pct)
        if p < -max_val or p > max_val:
            return False, f"Percentage out of range: {p}"
        return True, ""
    except (ValueError, TypeError):
        return False, f"Invalid percentage: {pct}"


def check_price_change_extreme(
    old_price: int, 
    new_price: int, 
    threshold_pct: float = 50.0
) -> Tuple[bool, str]:
    """
    Check if price change is too extreme.
    Returns (is_extreme, warning_message).
    """
    if not old_price or old_price <= 0:
        return False, ""
    
    try:
        change_pct = abs((new_price - old_price) / old_price) * 100
        if change_pct > threshold_pct:
            return True, f"Large price change: {change_pct:.1f}% (from {old_price} to {new_price})"
        return False, ""
    except:
        return False, ""


def validate_row_completeness(row: List, required_cols: List[int]) -> Tuple[bool, str]:
    """
    Validate row has required columns filled.
    Returns (is_complete, error_message).
    """
    for col_idx in required_cols:
        if col_idx >= len(row) or not row[col_idx]:
            return False, f"Missing required column: {col_idx}"
    return True, ""


def validate_source(source: str) -> Tuple[bool, str]:
    """Validate source is not empty."""
    if not source or source.strip() == '':
        return False, "Source is empty"
    return True, ""


def get_data_status(dataset: str, last_success_at: Optional[str]) -> str:
    """Determine if data is stale based on dataset type."""
    if not last_success_at:
        return STATUS_FAILED
    
    try:
        last_success = datetime.fromisoformat(last_success_at.replace('Z', '+00:00'))
    except:
        return STATUS_FAILED
    
    threshold_hours = STALE_THRESHOLDS.get(dataset, 24)
    age_hours = (datetime.now() - last_success).total_seconds() / 3600
    
    if age_hours > threshold_hours:
        return STATUS_STALE
    
    return STATUS_VALID


def validate_dataset(
    rows: List[List],
    required_columns: List[str],
    dataset: str = 'general'
) -> Dict:
    """
    Validate entire dataset.
    Returns validation report dict.
    """
    report = {
        'dataset': dataset,
        'total_rows': len(rows),
        'valid_rows': 0,
        'invalid_rows': 0,
        'errors': [],
        'warnings': [],
        'status': STATUS_VALID,
    }
    
    if not rows:
        report['status'] = STATUS_FAILED
        report['errors'].append("No data rows")
        return report
    
    # Check minimum rows
    if len(rows) < 1:
        report['errors'].append("Empty dataset")
        report['status'] = STATUS_FAILED
    
    # Validate each row
    for idx, row in enumerate(rows):
        row_valid = True
        
        # Check required columns exist
        for col_idx in range(min(len(required_columns), len(row))):
            if col_idx >= len(row) or not row[col_idx]:
                row_valid = False
                report['errors'].append(f"Row {idx+1}: missing column {col_idx}")
        
        if row_valid:
            report['valid_rows'] += 1
        else:
            report['invalid_rows'] += 1
    
    # Determine overall status
    if report['invalid_rows'] == report['total_rows']:
        report['status'] = STATUS_FAILED
    elif report['errors']:
        report['status'] = STATUS_STALE
    
    return report


def sanitize_price(price_str: str) -> Optional[int]:
    """Convert price string to integer."""
    if not price_str:
        return None
    
    # Remove currency symbols and spaces
    cleaned = re.sub(r'[Rp\s]', '', str(price_str))
    
    # Remove thousand separators (dots in Indonesian format like 15.000)
    # Pattern: dot followed by exactly 3 digits = thousand separator
    cleaned = re.sub(r'\.(\d{3})(?=\D|$)', r'\1', cleaned)
    
    # Remove remaining dots (decimal points like .00)
    cleaned = cleaned.replace('.', '')
    
    try:
        return int(cleaned)
    except ValueError:
        return None


def normalize_date(date_val) -> Optional[str]:
    """Normalize date to ISO format."""
    if not date_val:
        return None
    
    if isinstance(date_val, str):
        return date_val[:10]
    
    if isinstance(date_val, datetime):
        return date_val.strftime('%Y-%m-%d')
    
    return None