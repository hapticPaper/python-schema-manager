"""
SQL Type definitions and mappings for ETL operations.

Supports common SQL types used in BigQuery and other SQL databases.
"""

from enum import Enum
from typing import Any, Callable
from datetime import datetime, date
import pandas as pd


class SQLType(str, Enum):
    """Supported SQL types for schema definitions."""
    
    STRING = "STRING"
    INTEGER = "INTEGER"
    INT64 = "INT64"
    FLOAT = "FLOAT"
    FLOAT64 = "FLOAT64"
    BOOLEAN = "BOOLEAN"
    BOOL = "BOOL"
    TIMESTAMP = "TIMESTAMP"
    DATETIME = "DATETIME"
    DATE = "DATE"
    NUMERIC = "NUMERIC"
    BIGNUMERIC = "BIGNUMERIC"
    BYTES = "BYTES"
    JSON = "JSON"
    ARRAY = "ARRAY"
    STRUCT = "STRUCT"
    UNIQUE = "UNIQUE"
    UUID = "UUID"
    GUID = "GUID"
    REAL = "REAL"
    TEXT = "TEXT"


class SQLEngine(str, Enum):
    """Supported SQL Engines."""
    
    BIGQUERY = "BIGQUERY"
    SQLITE = "SQLITE"
    POSTGRES = "POSTGRES"
    MYSQL = "MYSQL"
    VERTICA = "VERTICA"
    SNOWFLAKE = "SNOWFLAKE"


class TypeHandler:
    """Handles type conversion for different SQL types."""
    
    @staticmethod
    def _is_null(value: Any) -> bool:
        """Check if value is null/NA, handling pandas and regular Python types."""
        if value is None:
            return True
        try:
            return pd.isna(value)
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def to_string(value: Any) -> str | None:
        """Convert value to string."""
        if TypeHandler._is_null(value):
            return None
        return str(value)
    
    @staticmethod
    def to_integer(value: Any) -> int | None:
        """Convert value to integer."""
        if TypeHandler._is_null(value):
            return None
        if isinstance(value, str) and value.strip() == '':
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def to_float(value: Any) -> float | None:
        """Convert value to float."""
        if TypeHandler._is_null(value):
            return None
        if isinstance(value, str) and value.strip() == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def to_boolean(value: Any) -> bool | None:
        """Convert value to boolean."""
        if TypeHandler._is_null(value):
            return None
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ('true', '1', 'yes', 'y', 't'):
                return True
            elif value_lower in ('false', '0', 'no', 'n', 'f', ''):
                return False
            return None
        return bool(value)
    
    @staticmethod
    def to_timestamp(value: Any) -> pd.Timestamp | None:
        """
        Convert value to pandas Timestamp.
        
        This ensures consistent timestamp handling across parquet and BigQuery.
        BigQuery expects UTC timestamps, and parquet handles pandas Timestamps well.
        """
        if TypeHandler._is_null(value):
            return None
        if isinstance(value, str) and value.strip() == '':
            return None
        
        try:
            # Parse to pandas Timestamp which handles various formats
            ts = pd.to_datetime(value, utc=True)
            return ts
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def to_datetime(value: Any) -> datetime | None:
        """Convert value to datetime."""
        if TypeHandler._is_null(value):
            return None
        if isinstance(value, str) and value.strip() == '':
            return None
        
        try:
            if isinstance(value, pd.Timestamp):
                return value.to_pydatetime()
            return pd.to_datetime(value).to_pydatetime()
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def to_date(value: Any) -> date | None:
        """Convert value to date."""
        if TypeHandler._is_null(value):
            return None
        if isinstance(value, str) and value.strip() == '':
            return None
        
        try:
            if isinstance(value, pd.Timestamp):
                return value.date()
            if isinstance(value, datetime):
                return value.date()
            return pd.to_datetime(value).date()
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def to_numeric(value: Any) -> float | None:
        """Convert value to numeric (same as float for most use cases)."""
        return TypeHandler.to_float(value)
    
    @staticmethod
    def to_bytes(value: Any) -> bytes | None:
        """Convert value to bytes."""
        if TypeHandler._is_null(value):
            return None
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode('utf-8')
        return str(value).encode('utf-8')
    
    @staticmethod
    def to_json(value: Any) -> dict | list | None:
        """Convert value to JSON (dict or list)."""
        if TypeHandler._is_null(value):
            return None
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            import json
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None


# Mapping of SQL types to handler functions
TYPE_HANDLERS: dict[SQLType, Callable] = {
    SQLType.STRING: TypeHandler.to_string,
    SQLType.INTEGER: TypeHandler.to_integer,
    SQLType.INT64: TypeHandler.to_integer,
    SQLType.FLOAT: TypeHandler.to_float,
    SQLType.FLOAT64: TypeHandler.to_float,
    SQLType.BOOLEAN: TypeHandler.to_boolean,
    SQLType.BOOL: TypeHandler.to_boolean,
    SQLType.TIMESTAMP: TypeHandler.to_timestamp,
    SQLType.DATETIME: TypeHandler.to_datetime,
    SQLType.DATE: TypeHandler.to_date,
    SQLType.NUMERIC: TypeHandler.to_numeric,
    SQLType.BIGNUMERIC: TypeHandler.to_numeric,
    SQLType.BYTES: TypeHandler.to_bytes,
    SQLType.JSON: TypeHandler.to_json,
    SQLType.UNIQUE: TypeHandler.to_string,
    SQLType.UUID: TypeHandler.to_string,
    SQLType.GUID: TypeHandler.to_string,
    SQLType.REAL: TypeHandler.to_float,
    SQLType.TEXT: TypeHandler.to_string,
}


