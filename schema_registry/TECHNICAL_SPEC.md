# ETL Utility - Technical Specification

## Overview

The lean_hatch ETL utility is a lightweight, schema-driven data transformation package designed to centralize data type handling and export functionality across different platforms (parquet, BigQuery, SQL databases).

## Architecture

### Core Components

1. **Schema Loader** (`schema_loader.py`)
   - Loads and validates JSON schema definitions
   - Uses pydantic for robust schema validation
   - Supports table-level and column-level metadata

2. **SQL Types** (`sql_types.py`)
   - Defines supported SQL types (STRING, INTEGER, FLOAT, TIMESTAMP, etc.)
   - Provides type handlers for data conversion
   - Maps SQL types to pandas dtypes

3. **Data Caster** (`data_caster.py`)
   - Casts data to match schema definitions
   - Supports dictionaries, lists, and pandas DataFrames
   - Validates required fields

4. **Parquet Exporter** (`parquet_exporter.py`)
   - Exports data to parquet files
   - Ensures BigQuery compatibility
   - Handles timestamp conversion to UTC

## Supported SQL Types

| SQL Type | Python Type | Pandas dtype | Description |
|----------|-------------|--------------|-------------|
| STRING | str | object | Text data |
| INTEGER | int | Int64 | Integer numbers |
| INT64 | int | Int64 | 64-bit integers |
| FLOAT | float | float64 | Floating-point numbers |
| FLOAT64 | float | float64 | 64-bit floats |
| BOOLEAN | bool | boolean | True/False values |
| BOOL | bool | boolean | Boolean alias |
| TIMESTAMP | pd.Timestamp | datetime64[ns, UTC] | UTC timestamps |
| DATETIME | datetime | datetime64[ns] | Datetimes |
| DATE | date | object | Date only |
| NUMERIC | float | float64 | Decimal numbers |
| BIGNUMERIC | float | float64 | Large decimals |
| BYTES | bytes | object | Binary data |
| JSON | dict/list | object | JSON objects |

## Schema Definition Format

### JSON Schema Structure

```json
{
  "name": "table_name",
  "description": "Optional table description",
  "columns": [
    {
      "name": "column_name",
      "type": "SQL_TYPE",
      "mode": "REQUIRED|NULLABLE|REPEATED",
      "description": "Optional column description"
    }
  ]
}
```

### Column Modes

- **REQUIRED**: Column cannot contain null values (enforced during casting)
- **NULLABLE**: Column can contain null values (default)
- **REPEATED**: For future array support

## Type Conversion Logic

### Null Handling

The ETL utility uses a robust null checking mechanism that handles:
- Python `None` values
- Pandas `NA` values
- NumPy `nan` values
- Empty strings (converted to `None` for most types)

Implementation:
```python
def _is_null(value: Any) -> bool:
    if value is None:
        return True
    try:
        return pd.isna(value)
    except (TypeError, ValueError):
        return False
```

### Timestamp Conversion

Timestamps are automatically converted to UTC for BigQuery compatibility:

```python
def to_timestamp(value: Any) -> pd.Timestamp | None:
    if TypeHandler._is_null(value):
        return None
    if isinstance(value, str) and value.strip() == '':
        return None
    
    try:
        ts = pd.to_datetime(value, utc=True)
        return ts
    except (ValueError, TypeError):
        return None
```

### Type Coercion Examples

| Input | Type | Output |
|-------|------|--------|
| "123" | INTEGER | 123 |
| "45.67" | FLOAT | 45.67 |
| "true" | BOOLEAN | True |
| "2024-01-01" | TIMESTAMP | 2024-01-01 00:00:00+00:00 |
| "" | INTEGER | None |
| None | STRING | None |

## Usage Patterns

### Basic Usage

```python
from schema_registry import SchemaLoader, DataCaster, ParquetExporter

# 1. Load schema
schema = SchemaLoader.load_from_file('schema.json')

# 2. Create caster
caster = DataCaster(schema)

# 3. Cast data
df = pd.DataFrame(raw_data)
df_casted = caster.cast_dataframe(df)

# 4. Export to parquet
exporter = ParquetExporter(schema)
exporter.export_dataframe(df_casted, 'output.parquet')
```

### Error Handling

```python
try:
    df_casted = caster.cast_dataframe(df)
except ValueError as e:
    # Handle required field validation errors
    print(f"Validation error: {e}")
```

### Logging Integration

The ETL utility automatically integrates with structlog when available:

```python
# With structlog installed
from schema_registry import DataCaster

# Logs are automatically structured
caster = DataCaster(schema)
# Output: [info] DataCaster initialized [table_name=customers] [num_columns=5]

df_casted = caster.cast_dataframe(df)
# Output: [info] Casting DataFrame [table_name=customers] [num_rows=1000]
```

## Performance Considerations

### DataFrame Operations

The DataCaster uses pandas-optimized operations for DataFrame conversion:

```python
# For timestamp columns, use vectorized pandas operations
if column.type == SQLType.TIMESTAMP:
    casted_df[column.name] = pd.to_datetime(
        casted_df[column.name], 
        utc=True,
        errors='coerce'
    )
```

### Memory Efficiency

- Uses `copy()` to avoid modifying original DataFrames
- Applies type handlers column-by-column
- Leverages pandas' efficient dtype system

## BigQuery Integration

### Parquet Export for BigQuery

```python
# 1. Define schema matching BigQuery table
schema = SchemaLoader.load_from_file('bq_schema.json')

# 2. Cast data with UTC timestamps
caster = DataCaster(schema)
df_casted = caster.cast_dataframe(df)

# 3. Export with BigQuery-compatible settings
exporter = ParquetExporter(schema)
exporter.export_dataframe(
    df_casted, 
    'bq_data.parquet',
    compression='snappy'  # BigQuery default
)
```

### Loading to BigQuery

```bash
# Using bq command line
bq load --source_format=PARQUET dataset.table bq_data.parquet

# Or using Python client
from google.cloud import bigquery

client = bigquery.Client()
job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.PARQUET
)

with open('bq_data.parquet', 'rb') as f:
    job = client.load_table_from_file(
        f, 'dataset.table', job_config=job_config
    )
```

## Testing Strategy

### Unit Tests

The ETL utility includes comprehensive unit tests:
- Schema loading and validation
- Type handler conversions
- DataFrame casting
- Parquet export/import
- Required field validation
- End-to-end workflow

Run tests:
```bash
pytest tests/etl/test_etl_utility.py -v
```

### Test Coverage

- Schema validation: 4 tests
- Type handlers: 6 tests
- Data casting: 4 tests
- Parquet operations: 2 tests
- End-to-end: 1 test

**Total: 17 tests, all passing**

## Security Considerations

### Input Validation

- All schemas are validated using pydantic
- Type conversion errors are caught and logged
- Required field validation prevents null values

### Safe Type Conversion

- JSON parsing uses try/except for malformed data
- Type errors return None instead of raising exceptions
- No arbitrary code execution

### CodeQL Analysis

The ETL utility has been analyzed with CodeQL and found **0 security vulnerabilities**.

## Extension Points

### Adding New Types

To add a new SQL type:

1. Add to `SQLType` enum in `sql_types.py`
2. Create a type handler in `TypeHandler` class
3. Add to `TYPE_HANDLERS` mapping
4. Add to `PANDAS_DTYPE_MAP` if applicable
5. Write tests

Example:
```python
class SQLType(str, Enum):
    # ... existing types
    CUSTOM_TYPE = "CUSTOM_TYPE"

class TypeHandler:
    @staticmethod
    def to_custom_type(value: Any) -> CustomType | None:
        # Implementation
        pass

TYPE_HANDLERS[SQLType.CUSTOM_TYPE] = TypeHandler.to_custom_type
```

### Custom Schema Loaders

You can create custom schema loaders for different formats:

```python
class YAMLSchemaLoader:
    @staticmethod
    def load_from_file(file_path: str) -> TableSchema:
        with open(file_path) as f:
            data = yaml.safe_load(f)
        return TableSchema(**data)
```

## Best Practices

1. **Always define schemas**: Don't rely on implicit type inference
2. **Use TIMESTAMP for UTC times**: Ensures BigQuery compatibility
3. **Mark required fields**: Catch missing data early
4. **Test schema changes**: Validate schemas before production use
5. **Use structured logging**: Helps with debugging and monitoring
6. **Handle errors gracefully**: Validate data before export
7. **Version your schemas**: Track schema changes over time

## Limitations

- ARRAY and STRUCT types not fully implemented
- Limited support for nested JSON structures
- No automatic schema inference from data
- Pandas-dependent (not pure Python)

## Future Enhancements

- [ ] Support for ARRAY and STRUCT types
- [ ] Schema versioning and migration tools
- [ ] Automatic schema inference from data
- [ ] Direct BigQuery export (without intermediate parquet)
- [ ] Support for other file formats (Avro, ORC)
- [ ] Data quality checks and validation rules
- [ ] Performance optimizations for large datasets
- [ ] Schema registry integration

## Dependencies

- `pydantic` >= 2.0: Schema validation
- `pandas` >= 2.0: Data manipulation
- `pyarrow` >= 10.0: Parquet support
- `structlog` (optional): Structured logging

## License

Part of the lean_hatch project.

## Contact

For issues or questions, please refer to the main lean_hatch repository.
