from typing import Dict
from schema_registry.sql_types import SQLType
from .base import BaseDialect

class BigQueryDialect(BaseDialect):
    """BigQuery implementation of the dialect."""

    def get_type_map(self) -> Dict[SQLType, str]:
        # BigQuery uses strings that mostly match our Enums, but we can be explicit if needed.
        # For now, returning the Enum value itself is sufficient as standard BQ types.
        return {t: t.value for t in SQLType}

    def get_pandas_dtype_map(self) -> Dict[SQLType, str]:
        return {
            SQLType.STRING: 'object',
            SQLType.INTEGER: 'Int64',
            SQLType.INT64: 'Int64',
            SQLType.FLOAT: 'float64',
            SQLType.FLOAT64: 'float64',
            SQLType.BOOLEAN: 'boolean',
            SQLType.BOOL: 'boolean',
            SQLType.TIMESTAMP: 'datetime64[ns, UTC]',
            SQLType.DATETIME: 'datetime64[ns]',
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
