# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-10-30

### Added
- Initial release of python-schema-manager
- Schema definition using JSON with SQL types
- Type casting and data validation using pydantic
- Parquet export functionality
- Consistent timestamp handling for BigQuery and parquet
- Support for all common SQL types (STRING, INTEGER, FLOAT, BOOLEAN, TIMESTAMP, etc.)
- Structured logging support (optional)
- Comprehensive test suite with 75 test cases
- Example schemas and usage patterns
- Documentation and quickstart guide

### Features
- **SchemaLoader**: Load schemas from JSON files, dictionaries, or strings
- **DataCaster**: Cast data to match schema definitions with validation
- **ParquetExporter**: Export data to parquet files with proper type handling
- **SQLType**: Enum of supported SQL types with type handlers
- **BigQuery compatibility**: Automatic UTC timestamp conversion
- **Pandas integration**: Seamless DataFrame processing
- **Error handling**: Clear validation messages and error reporting

### Dependencies
- pydantic>=2.0.0 for data validation
- pandas>=1.5.0 for data manipulation  
- pyarrow>=10.0.0 for parquet file support
- structlog>=22.0.0 (optional) for structured logging