"""Test validation utilities."""
import os
import sys
import pytest
from datetime import datetime, timedelta


# Import from project
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestValidatePrice:
    def test_valid_price(self):
        from utils.validation import validate_price
        ok, msg = validate_price(15000)
        assert ok is True
        assert msg == ""

    def test_zero_price(self):
        from utils.validation import validate_price
        ok, msg = validate_price(0)
        assert ok is False

    def test_negative_price(self):
        from utils.validation import validate_price
        ok, msg = validate_price(-100)
        assert ok is False

    def test_empty_price(self):
        from utils.validation import validate_price
        ok, msg = validate_price(None)
        assert ok is False
        assert "empty" in msg.lower()

    def test_string_price_fails(self):
        from utils.validation import validate_price
        ok, msg = validate_price("abc")
        assert ok is False

    def test_too_low_price(self):
        from utils.validation import validate_price
        ok, msg = validate_price(10, min_price=100)
        assert ok is False
        assert "low" in msg.lower()

    def test_too_high_price(self):
        from utils.validation import validate_price
        ok, msg = validate_price(999999999999, max_price=100000000)
        assert ok is False
        assert "high" in msg.lower()


class TestValidateDate:
    def test_valid_date(self):
        from utils.validation import validate_date
        today = datetime.now().strftime('%Y-%m-%d')
        ok, msg = validate_date(today)
        assert ok is True

    def test_empty_date(self):
        from utils.validation import validate_date
        ok, msg = validate_date(None)
        assert ok is False

    def test_future_date(self):
        from utils.validation import validate_date
        future = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        ok, msg = validate_date(future)
        assert ok is False

    def test_very_old_date(self):
        from utils.validation import validate_date
        ok, msg = validate_date("2000-01-01", max_age_days=365)
        assert ok is False
        assert "old" in msg.lower()

    def test_recent_date(self):
        from utils.validation import validate_date
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        ok, msg = validate_date(yesterday)
        assert ok is True


class TestValidatePercentage:
    def test_valid_pct(self):
        from utils.validation import validate_percentage
        ok, msg = validate_percentage(5.0)
        assert ok is True

    def test_zero_pct(self):
        from utils.validation import validate_percentage
        ok, msg = validate_percentage(0.0)
        assert ok is True

    def test_negative_pct(self):
        from utils.validation import validate_percentage
        ok, msg = validate_percentage(-3.5)
        assert ok is True

    def test_too_high(self):
        from utils.validation import validate_percentage
        ok, msg = validate_percentage(150.0)
        assert ok is False

    def test_invalid_input(self):
        from utils.validation import validate_percentage
        ok, msg = validate_percentage("notanumber")
        assert ok is False
