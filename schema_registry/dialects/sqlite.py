from typing import Dict
from schema_registry.sql_types import SQLType
from .base import BaseDialect

class SQLiteDialect(BaseDialect):
    """SQLite implementation of the dialect."""

    def get_type_map(self) -> Dict[SQLType, str]:
        # SQLite uses a simpler type system (Storage Classes)
        return {
            SQLType.STRING: 'TEXT',
            SQLType.INTEGER: 'INTEGER',
            SQLType.INT64: 'INTEGER',
            SQLType.FLOAT: 'REAL',
            SQLType.FLOAT64: 'REAL',
            SQLType.BOOLEAN: 'INTEGER', # 0 or 1
            SQLType.BOOL: 'INTEGER',
            SQLType.TIMESTAMP: 'TEXT', # ISO8601 strings
            SQLType.DATETIME: 'TEXT',
            SQLType.DATE: 'TEXT',
            SQLType.NUMERIC: 'NUMERIC',
            SQLType.BIGNUMERIC: 'NUMERIC',
            SQLType.BYTES: 'BLOB',
            SQLType.JSON: 'TEXT',
            SQLType.UNIQUE: 'TEXT',
            SQLType.UUID: 'TEXT',
            SQLType.GUID: 'TEXT',
            SQLType.REAL: 'REAL',
            SQLType.TEXT: 'TEXT',
        }

    def get_pandas_dtype_map(self) -> Dict[SQLType, str]:
        # Similar to BigQuery for Pandas, but we might want to be flexible.
        return {
            SQLType.STRING: 'object',
            SQLType.INTEGER: 'Int64',
            SQLType.INT64: 'Int64',
            SQLType.FLOAT: 'float64',
            SQLType.FLOAT64: 'float64',
            SQLType.BOOLEAN: 'float64', # SQLite bools are tricky in pandas, often float if nulls exist
            SQLType.BOOL: 'float64',
            SQLType.TIMESTAMP: 'object', # Keep as string for SQLite load
            SQLType.DATETIME: 'object', # Keep as string for SQLite load
            SQLType.DATE: 'object',
            SQLType.NUMERIC: 'float64',
            SQLType.BIGNUMERIC: 'float64',
            SQLType.BYTES: 'object',
            SQLType.JSON: 'object',
            SQLType.UNIQUE: 'object',
            SQLType.UUID: 'object',
            SQLType.GUID: 'object',
            SQLType.REAL: 'float64',
            SQLType.TEXT: 'object',
        }
