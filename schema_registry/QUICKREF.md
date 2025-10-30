# ETL Utility - Quick Reference Guide

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Create a Schema (JSON)

```json
{
  "name": "my_table",
  "columns": [
    {"name": "id", "type": "INTEGER", "mode": "REQUIRED"},
    {"name": "name", "type": "STRING", "mode": "REQUIRED"},
    {"name": "created_at", "type": "TIMESTAMP", "mode": "NULLABLE"}
  ]
}
```

### 2. Use the ETL Utility

```python
from schema_registry import SchemaLoader, DataCaster, ParquetExporter
import pandas as pd

# Load schema
schema = SchemaLoader.load_from_file('schema.json')

# Prepare data
data = [
    {"id": "1", "name": "Alice", "created_at": "2024-01-01 10:00:00"},
    {"id": "2", "name": "Bob", "created_at": "2024-01-02 11:00:00"}
]

# Cast data
caster = DataCaster(schema)
df = pd.DataFrame(data)
df_casted = caster.cast_dataframe(df)

# Export to parquet
exporter = ParquetExporter(schema)
exporter.export_dataframe(df_casted, 'output.parquet')
```

## Common Operations

### Load Schema from Different Sources

```python
# From file
schema = SchemaLoader.load_from_file('schema.json')

# From dictionary
schema = SchemaLoader.load_from_dict({
    "name": "users",
    "columns": [{"name": "id", "type": "INTEGER", "mode": "REQUIRED"}]
})

# From JSON string
schema = SchemaLoader.load_from_json_string('{"name": "users", "columns": [...]}')
```

### Cast Different Data Types

```python
# Cast records (list of dicts)
casted_records = caster.cast_records(records)

# Cast single row
casted_row = caster.cast_row(row_dict)

# Cast DataFrame
casted_df = caster.cast_dataframe(df)
```

### Export Options

```python
# Export with different compression
exporter.export_dataframe(df, 'output.parquet', compression='gzip')

# Export without type casting (if data is already casted)
exporter.export_dataframe(df, 'output.parquet', cast_types=False)

# Read parquet back
df_read = exporter.read_parquet('output.parquet')
```

## Supported Types

| Type | Example Input | Output |
|------|---------------|--------|
| STRING | `"hello"` or `123` | `"hello"` or `"123"` |
| INTEGER | `"123"` or `123.7` | `123` |
| FLOAT | `"45.67"` or `45` | `45.67` or `45.0` |
| BOOLEAN | `"true"` or `1` | `True` |
| TIMESTAMP | `"2024-01-01 12:00:00"` | `2024-01-01 12:00:00+00:00` (UTC) |
| DATE | `"2024-01-01"` | `2024-01-01` |
| JSON | `'{"key": "value"}'` | `{"key": "value"}` |

## Error Handling

```python
try:
    df_casted = caster.cast_dataframe(df)
except ValueError as e:
    print(f"Validation error: {e}")
    # Handle required field violations or schema mismatches
```

## Testing

```bash
# Run all tests
pytest tests/etl/test_etl_utility.py -v

# Run specific test
pytest tests/etl/test_etl_utility.py::TestDataCaster::test_cast_dataframe -v

# Run example
python etl/examples/example_usage.py
```

## Common Pitfall

### ❌ Wrong: Using string types for timestamps
```json
{"name": "created_at", "type": "STRING"}
```

### ✅ Correct: Using TIMESTAMP type
```json
{"name": "created_at", "type": "TIMESTAMP", "mode": "REQUIRED"}
```

This ensures proper UTC conversion and BigQuery compatibility.

## BigQuery Workflow

```python
# 1. Define schema matching BigQuery table
schema = SchemaLoader.load_from_file('bq_schema.json')

# 2. Cast and export
caster = DataCaster(schema)
exporter = ParquetExporter(schema)

df_casted = caster.cast_dataframe(df)
exporter.export_dataframe(df_casted, 'bq_data.parquet')

# 3. Load to BigQuery
# bq load --source_format=PARQUET dataset.table bq_data.parquet
```

## Structured Logging

When structlog is installed, you get detailed logs:

```
[info] DataCaster initialized [table_name=customers] [num_columns=5]
[info] Casting DataFrame [table_name=customers] [num_rows=1000]
[info] Writing parquet file [output_path=output.parquet] [num_rows=1000]
```

## Tips

1. **Always validate schemas** before using in production
2. **Use TIMESTAMP for datetime fields** when working with BigQuery
3. **Mark truly required fields** as REQUIRED to catch errors early
4. **Test with sample data** before processing large datasets
5. **Use compression** for large parquet files (`compression='gzip'`)

## Examples

See `etl/examples/` for:
- `customer_transactions_schema.json` - Transaction data schema
- `user_events_schema.json` - Event tracking schema
- `example_usage.py` - Complete end-to-end example

## Documentation

- [README.md](README.md) - User guide and API reference
- [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md) - Technical specification
- [Test suite](../../tests/etl/test_etl_utility.py) - Usage examples in tests

## Support

For issues or questions:
1. Check the documentation
2. Review the example scripts
3. Look at the test cases
4. Refer to the technical specification
