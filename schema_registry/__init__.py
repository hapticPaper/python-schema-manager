"""
ETL Utility Package for lean_hatch

A utility package for ETL operations that provides:
- Schema definition using JSON with SQL types
- Type casting and data validation using pydantic
- Parquet export functionality
- Consistent timestamp handling for BigQuery and parquet
- Structured logging support
"""

from .schema_loader import SchemaLoader
from .data_caster import DataCaster
from .parquet_exporter import ParquetExporter
from .sql_types import SQLType
from .to_pydantic import AsPydantic

__version__ = "1.2.3"

__all__ = [
    "SchemaLoader",
    "DataCaster",
    "ParquetExporter",
    "SQLType",
    "AsPydantic",
]
