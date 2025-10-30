# ETL Utility Package

A lightweight ETL utility package for lean_hatch that provides schema-driven data transformation and export capabilities.

## Overview

This ETL utility centralizes data type handling, validation, and export functionality to ensure consistency across different platforms (parquet files, BigQuery, etc.). It's designed to be simple, efficient, and easy to integrate into ETL pipelines.

## Features

- **Schema-driven data validation**: Define schemas using JSON with SQL types
- **Type casting with pydantic**: Robust data validation and type conversion
- **Parquet export**: Write data to parquet files with proper type handling
- **BigQuery compatibility**: Timestamps are automatically converted to UTC for BigQuery
- **Consistent timestamp handling**: Centralized timestamp processing for pandas, parquet, and SQL
- **Structured logging**: Built-in support for structlog (optional)

## Installation

The ETL utility is included in lean_hatch. Install dependencies:

```bash
pip install -r requirements.txt
```

Required packages:
- `pydantic` - Data validation
- `pandas` - Data manipulation
- `pyarrow` - Parquet file support
- `structlog` - Structured logging (optional)

## Quick Start

### 1. Define a Schema

Create a JSON schema file defining your data structure:

```json
{
  "name": "customer_transactions",
  "description": "Customer transaction data",
  "columns": [
    {
      "name": "transaction_id",
      "type": "STRING",
      "mode": "REQUIRED",
      "description": "Unique transaction identifier"
    },
    {
      "name": "customer_id",
      "type": "INTEGER",
      "mode": "REQUIRED"
    },
    {
      "name": "amount",
      "type": "FLOAT",
      "mode": "REQUIRED"
    },
    {
      "name": "transaction_timestamp",
      "type": "TIMESTAMP",
      "mode": "REQUIRED",
      "description": "Transaction time in UTC"
    },
    {
      "name": "is_refunded",
      "type": "BOOLEAN",
      "mode": "NULLABLE"
    }
  ]
}
```

### 2. Load and Use the Schema

```python
from schema_registry import SchemaLoader, DataCaster, ParquetExporter
import pandas as pd

# Load schema
schema = SchemaLoader.load_from_file('schema.json')

# Create a data caster
caster = DataCaster(schema)

# Cast your data
raw_data = [
    {
        "transaction_id": "TX001",
        "customer_id": "123",  # Will be cast to integer
        "amount": "99.99",      # Will be cast to float
        "transaction_timestamp": "2024-01-15 10:30:00",  # Will be cast to UTC timestamp
        "is_refunded": "false"  # Will be cast to boolean
    }
]

# Cast records
casted_data = caster.cast_records(raw_data)

# Or cast a DataFrame
df = pd.DataFrame(raw_data)
casted_df = caster.cast_dataframe(df)

# Export to parquet
exporter = ParquetExporter(schema)
exporter.export_dataframe(casted_df, 'output.parquet')
```

## Supported SQL Types

The ETL utility supports the following SQL types:

| SQL Type | Python Type | Description |
|----------|-------------|-------------|
| `STRING` | `str` | Text data |
| `INTEGER`, `INT64` | `int` | Integer numbers |
| `FLOAT`, `FLOAT64` | `float` | Floating-point numbers |
| `BOOLEAN`, `BOOL` | `bool` | True/False values |
| `TIMESTAMP` | `pd.Timestamp` | Timestamp with UTC timezone (BigQuery compatible) |
| `DATETIME` | `datetime` | Datetime without timezone |
| `DATE` | `date` | Date only |
| `NUMERIC`, `BIGNUMERIC` | `float` | Decimal numbers |
| `BYTES` | `bytes` | Binary data |
| `JSON` | `dict`, `list` | JSON objects |

## Column Modes

- `REQUIRED`: Column cannot contain null values (validation enforced)
- `NULLABLE`: Column can contain null values (default)
- `REPEATED`: Column contains array values (for future use)

## Timestamp Handling

The ETL utility provides consistent timestamp handling across platforms:

### For Parquet Files
```python
# Timestamps are automatically converted to pandas Timestamp with UTC timezone
schema = SchemaLoader.load_from_dict({
    "name": "events",
    "columns": [
        {"name": "event_time", "type": "TIMESTAMP", "mode": "REQUIRED"}
    ]
})

caster = DataCaster(schema)
df = pd.DataFrame([{"event_time": "2024-01-01 12:00:00"}])
casted_df = caster.cast_dataframe(df)

# event_time is now a pandas Timestamp with UTC timezone
# This is compatible with both parquet and BigQuery
```

### For BigQuery
BigQuery expects timestamps in UTC. The ETL utility automatically converts all `TIMESTAMP` type columns to UTC:

```python
# The timestamp will be in UTC, ready for BigQuery ingestion
exporter = ParquetExporter(schema)
exporter.export_dataframe(df, 'bq_data.parquet')

# You can then load this parquet file to BigQuery
# bq load --source_format=PARQUET dataset.table bq_data.parquet
```

## Advanced Usage

### Custom Type Casting

```python
from schema_registry import DataCaster, SchemaLoader

schema = SchemaLoader.load_from_file('schema.json')
caster = DataCaster(schema)

# Cast a single row
row = {"id": "123", "value": "45.67"}
casted_row = caster.cast_row(row)

# Cast multiple records
records = [
    {"id": "1", "value": "10.5"},
    {"id": "2", "value": "20.5"}
]
casted_records = caster.cast_records(records)
```

### Parquet Export Options

```python
from schema_registry import ParquetExporter

exporter = ParquetExporter(schema)

# Export with different compression
exporter.export_dataframe(df, 'output.parquet', compression='gzip')

# Export without type casting (use raw DataFrame types)
exporter.export_dataframe(df, 'output.parquet', cast_types=False)

# Read parquet file back
df_read = exporter.read_parquet('output.parquet')
```

### Structured Logging

The ETL utility automatically uses structlog if available:

```python
# Logging is built-in and will use structlog if available
from schema_registry import DataCaster, SchemaLoader

schema = SchemaLoader.load_from_file('schema.json')
caster = DataCaster(schema)

# Operations are automatically logged
df_casted = caster.cast_dataframe(df)
# Output: [info] Casting DataFrame [table_name=customer_transactions] [num_rows=1000]
```

## Examples

See the `examples/` directory for sample schema files:
- `customer_transactions_schema.json` - Transaction data schema
- `user_events_schema.json` - User event tracking schema

## Testing

Run the test suite:

```bash
python -m pytest tests/etl/test_etl_utility.py -v
```

## Error Handling

The ETL utility provides clear error messages for common issues:

```python
# Invalid schema
try:
    schema = SchemaLoader.load_from_dict({
        "name": "test",
        "columns": []  # Empty columns
    })
except ValueError as e:
    print(e)  # "Table must have at least one column"

# Required field validation
try:
    caster = DataCaster(schema)
    df = pd.DataFrame([{"required_field": None}])
    casted_df = caster.cast_dataframe(df)
except ValueError as e:
    print(e)  # "Required column 'required_field' has 1 null values"
```

## Best Practices

1. **Always define schemas for your data**: This ensures consistency and catches errors early
2. **Use TIMESTAMP type for timezone-aware datetimes**: Especially when working with BigQuery
3. **Mark truly required fields as REQUIRED**: This validates your data before export
4. **Use appropriate numeric types**: `INTEGER` for whole numbers, `FLOAT` for decimals
5. **Test your schemas**: Write tests that validate your schema definitions

## Integration with BigQuery

Example workflow for BigQuery:

```python
from schema_registry import SchemaLoader, DataCaster, ParquetExporter
import pandas as pd

# 1. Define schema matching your BigQuery table
schema = SchemaLoader.load_from_file('bq_table_schema.json')

# 2. Load your data
df = pd.read_csv('raw_data.csv')

# 3. Cast to schema
caster = DataCaster(schema)
df_casted = caster.cast_dataframe(df)

# 4. Export to parquet
exporter = ParquetExporter(schema)
exporter.export_dataframe(df_casted, 'bq_data.parquet')

# 5. Load to BigQuery (using bq command line or Python client)
# bq load --source_format=PARQUET dataset.table bq_data.parquet
```

## API Reference

### SchemaLoader

```python
SchemaLoader.load_from_file(file_path: str | Path) -> TableSchema
SchemaLoader.load_from_dict(schema_dict: dict) -> TableSchema
SchemaLoader.load_from_json_string(json_string: str) -> TableSchema
```

### DataCaster

```python
DataCaster(schema: TableSchema)
DataCaster.cast_value(value: Any, column: ColumnSchema) -> Any
DataCaster.cast_row(row: dict) -> dict
DataCaster.cast_dataframe(df: pd.DataFrame) -> pd.DataFrame
DataCaster.cast_records(records: list[dict]) -> list[dict]
```

### ParquetExporter

```python
ParquetExporter(schema: TableSchema)
ParquetExporter.export_dataframe(df: pd.DataFrame, output_path: str | Path, 
                                 cast_types: bool = True, compression: str = 'snappy')
ParquetExporter.export_records(records: list[dict], output_path: str | Path,
                               cast_types: bool = True, compression: str = 'snappy')
ParquetExporter.read_parquet(input_path: str | Path) -> pd.DataFrame
```

## License

Part of the lean_hatch project.
