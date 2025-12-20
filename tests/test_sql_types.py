"""
Tests for SQLType and TypeHandler classes.
"""

import pytest
from datetime import datetime, date
import pandas as pd

from schema_registry.sql_types import SQLType, TypeHandler


class TestTypeHandler:
    """Test cases for TypeHandler conversion methods."""

    def test_to_string_basic(self):
        """Test basic string conversion."""
        assert TypeHandler.to_string("hello") == "hello"
        assert TypeHandler.to_string(123) == "123"
        assert TypeHandler.to_string(45.67) == "45.67"
        assert TypeHandler.to_string(True) == "True"

    def test_to_string_null_values(self):
        """Test string conversion with null values."""
        assert TypeHandler.to_string(None) is None
        assert TypeHandler.to_string(pd.NA) is None
        assert TypeHandler.to_string(float("nan")) is None

    def test_to_integer_basic(self):
        """Test basic integer conversion."""
        assert TypeHandler.to_integer(123) == 123
        assert TypeHandler.to_integer("456") == 456
        assert TypeHandler.to_integer(78.9) == 78
        assert TypeHandler.to_integer("12.7") == 12

    def test_to_integer_null_values(self):
        """Test integer conversion with null values."""
        assert TypeHandler.to_integer(None) is None
        assert TypeHandler.to_integer(pd.NA) is None
        assert TypeHandler.to_integer("") is None
        assert TypeHandler.to_integer("  ") is None

    def test_to_integer_invalid(self):
        """Test integer conversion with invalid values."""
        assert TypeHandler.to_integer("invalid") is None
        assert TypeHandler.to_integer("12.34.56") is None

    def test_to_float_basic(self):
        """Test basic float conversion."""
        assert TypeHandler.to_float(123.45) == 123.45
        assert TypeHandler.to_float("67.89") == 67.89
        assert TypeHandler.to_float(100) == 100.0
        assert TypeHandler.to_float("200") == 200.0

    def test_to_float_null_values(self):
        """Test float conversion with null values."""
        assert TypeHandler.to_float(None) is None
        assert TypeHandler.to_float(pd.NA) is None
        assert TypeHandler.to_float("") is None
        assert TypeHandler.to_float("  ") is None

    def test_to_float_invalid(self):
        """Test float conversion with invalid values."""
        assert TypeHandler.to_float("invalid") is None
        assert TypeHandler.to_float("12.34.56") is None

    def test_to_boolean_true_values(self):
        """Test boolean conversion with true values."""
        assert TypeHandler.to_boolean(True) is True
        assert TypeHandler.to_boolean("true") is True
        assert TypeHandler.to_boolean("TRUE") is True
        assert TypeHandler.to_boolean("True") is True
        assert TypeHandler.to_boolean("1") is True
        assert TypeHandler.to_boolean("yes") is True
        assert TypeHandler.to_boolean("y") is True
        assert TypeHandler.to_boolean("t") is True
        assert TypeHandler.to_boolean(1) is True

    def test_to_boolean_false_values(self):
        """Test boolean conversion with false values."""
        assert TypeHandler.to_boolean(False) is False
        assert TypeHandler.to_boolean("false") is False
        assert TypeHandler.to_boolean("FALSE") is False
        assert TypeHandler.to_boolean("False") is False
        assert TypeHandler.to_boolean("0") is False
        assert TypeHandler.to_boolean("no") is False
        assert TypeHandler.to_boolean("n") is False
        assert TypeHandler.to_boolean("f") is False
        assert TypeHandler.to_boolean(0) is False
        assert TypeHandler.to_boolean("") is False

    def test_to_boolean_null_values(self):
        """Test boolean conversion with null values."""
        assert TypeHandler.to_boolean(None) is None
        assert TypeHandler.to_boolean(pd.NA) is None

    def test_to_boolean_invalid(self):
        """Test boolean conversion with invalid values."""
        assert TypeHandler.to_boolean("invalid") is None
        assert TypeHandler.to_boolean("maybe") is None

    def test_to_timestamp_basic(self):
        """Test basic timestamp conversion."""
        # String timestamp
        ts = TypeHandler.to_timestamp("2024-01-15 10:30:00")
        assert isinstance(ts, pd.Timestamp)
        assert ts.tz is not None  # Should be UTC

        # ISO format
        ts2 = TypeHandler.to_timestamp("2024-01-15T10:30:00Z")
        assert isinstance(ts2, pd.Timestamp)
        assert ts2.tz is not None

    def test_to_timestamp_null_values(self):
        """Test timestamp conversion with null values."""
        assert TypeHandler.to_timestamp(None) is None
        assert TypeHandler.to_timestamp(pd.NA) is None
        assert TypeHandler.to_timestamp("") is None
        assert TypeHandler.to_timestamp("  ") is None

    def test_to_timestamp_invalid(self):
        """Test timestamp conversion with invalid values."""
        assert TypeHandler.to_timestamp("invalid") is None
        assert TypeHandler.to_timestamp("2024-13-45") is None

    def test_to_datetime_basic(self):
        """Test basic datetime conversion."""
        dt = TypeHandler.to_datetime("2024-01-15 10:30:00")
        assert isinstance(dt, datetime)

        # From pandas Timestamp
        ts = pd.Timestamp("2024-01-15 10:30:00")
        dt2 = TypeHandler.to_datetime(ts)
        assert isinstance(dt2, datetime)

    def test_to_datetime_null_values(self):
        """Test datetime conversion with null values."""
        assert TypeHandler.to_datetime(None) is None
        assert TypeHandler.to_datetime(pd.NA) is None
        assert TypeHandler.to_datetime("") is None

    def test_to_date_basic(self):
        """Test basic date conversion."""
        d = TypeHandler.to_date("2024-01-15")
        assert isinstance(d, date)
        assert d.year == 2024
        assert d.month == 1
        assert d.day == 15

        # From datetime
        dt = datetime(2024, 1, 15, 10, 30, 0)
        d2 = TypeHandler.to_date(dt)
        assert isinstance(d2, date)
        assert d2 == date(2024, 1, 15)

        # From pandas Timestamp
        ts = pd.Timestamp("2024-01-15 10:30:00")
        d3 = TypeHandler.to_date(ts)
        assert isinstance(d3, date)
        assert d3 == date(2024, 1, 15)

    def test_to_date_null_values(self):
        """Test date conversion with null values."""
        assert TypeHandler.to_date(None) is None
        assert TypeHandler.to_date(pd.NA) is None
        assert TypeHandler.to_date("") is None

    def test_to_numeric_basic(self):
        """Test numeric conversion (same as float)."""
        assert TypeHandler.to_numeric(123.45) == 123.45
        assert TypeHandler.to_numeric("67.89") == 67.89
        assert TypeHandler.to_numeric(None) is None

    def test_to_bytes_basic(self):
        """Test basic bytes conversion."""
        # From string
        b = TypeHandler.to_bytes("hello")
        assert isinstance(b, bytes)
        assert b == b"hello"

        # From bytes (passthrough)
        b2 = TypeHandler.to_bytes(b"world")
        assert b2 == b"world"

        # From other types
        b3 = TypeHandler.to_bytes(123)
        assert b3 == b"123"

    def test_to_bytes_null_values(self):
        """Test bytes conversion with null values."""
        assert TypeHandler.to_bytes(None) is None
        assert TypeHandler.to_bytes(pd.NA) is None

    def test_to_json_basic(self):
        """Test basic JSON conversion."""
        # From dict
        obj = {"key": "value", "num": 123}
        result = TypeHandler.to_json(obj)
        assert result == obj

        # From JSON string
        json_str = '{"key": "value", "num": 123}'
        result3 = TypeHandler.to_json(json_str)
        assert isinstance(result3, dict)
        assert result3["key"] == "value"
        assert result3["num"] == 123

    def test_to_json_null_values(self):
        """Test JSON conversion with null values."""
        assert TypeHandler.to_json(None) is None
        assert TypeHandler.to_json(pd.NA) is None

    def test_to_json_invalid(self):
        """Test JSON conversion with invalid values."""
        assert TypeHandler.to_json("invalid json {") is None
        assert TypeHandler.to_json(123) is None

    def test_is_null_helper(self):
        """Test the _is_null helper method."""
        # Null values
        assert TypeHandler._is_null(None) is True
        assert TypeHandler._is_null(pd.NA) is True
        assert TypeHandler._is_null(float("nan")) is True

        # Non-null values
        assert TypeHandler._is_null(0) is False
        assert TypeHandler._is_null("") is False
        assert TypeHandler._is_null(False) is False
        assert TypeHandler._is_null("hello") is False


class TestSQLType:
    """Test cases for SQLType enum."""

    def test_sql_type_values(self):
        """Test that SQLType enum has expected values."""
        assert SQLType.STRING == "STRING"
        assert SQLType.INTEGER == "INTEGER"
        assert SQLType.INT64 == "INT64"
        assert SQLType.FLOAT == "FLOAT"
        assert SQLType.FLOAT64 == "FLOAT64"
        assert SQLType.BOOLEAN == "BOOLEAN"
        assert SQLType.BOOL == "BOOL"
        assert SQLType.TIMESTAMP == "TIMESTAMP"
        assert SQLType.DATETIME == "DATETIME"
        assert SQLType.DATE == "DATE"
        assert SQLType.NUMERIC == "NUMERIC"
        assert SQLType.BIGNUMERIC == "BIGNUMERIC"
        assert SQLType.BYTES == "BYTES"
        assert SQLType.JSON == "JSON"

    def test_sql_type_string_inheritance(self):
        """Test that SQLType can be used as string."""
        assert isinstance(SQLType.STRING, str)
        # SQLType is a string enum, so the string representation includes the enum name
        assert SQLType.INTEGER.value == "INTEGER"

    def test_type_handlers_coverage(self):
        """Test that all main SQL types have handlers."""
        from schema_registry.sql_types import TYPE_HANDLERS

        # These types should have handlers
        expected_types = [
            SQLType.STRING,
            SQLType.INTEGER,
            SQLType.INT64,
            SQLType.FLOAT,
            SQLType.FLOAT64,
            SQLType.BOOLEAN,
            SQLType.BOOL,
            SQLType.TIMESTAMP,
            SQLType.DATETIME,
            SQLType.DATE,
            SQLType.NUMERIC,
            SQLType.BIGNUMERIC,
            SQLType.BYTES,
            SQLType.JSON,
        ]

        for sql_type in expected_types:
            assert sql_type in TYPE_HANDLERS, f"Missing handler for {sql_type}"
            assert callable(TYPE_HANDLERS[sql_type])
