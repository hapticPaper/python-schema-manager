"""
Tests for SchemaLoader class.
"""

import json
import pytest
from pathlib import Path
import tempfile

from schema_registry import SchemaLoader
from schema_registry.schema_loader import TableSchema, ColumnSchema
from schema_registry.sql_types import SQLType


class TestSchemaLoader:
    """Test cases for SchemaLoader."""
    
    def test_load_from_dict_valid_schema(self):
        """Test loading a valid schema from a dictionary."""
        schema_dict = {
            "name": "test_table",
            "description": "Test table description",
            "columns": [
                {
                    "name": "id",
                    "type": "INTEGER",
                    "mode": "REQUIRED",
                    "description": "Primary key"
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "mode": "NULLABLE"
                }
            ]
        }
        
        schema = SchemaLoader.load_from_dict(schema_dict)
        
        assert isinstance(schema, TableSchema)
        assert schema.name == "test_table"
        assert schema.description == "Test table description"
        assert len(schema.columns) == 2
        assert schema.columns[0].name == "id"
        assert schema.columns[0].type == SQLType.INTEGER
        assert schema.columns[0].mode == "REQUIRED"
        assert schema.columns[1].name == "name"
        assert schema.columns[1].type == SQLType.STRING
        assert schema.columns[1].mode == "NULLABLE"
    
    def test_load_from_dict_minimal_schema(self):
        """Test loading a minimal schema (only required fields)."""
        schema_dict = {
            "name": "minimal_table",
            "columns": [
                {
                    "name": "col1",
                    "type": "STRING"
                }
            ]
        }
        
        schema = SchemaLoader.load_from_dict(schema_dict)
        
        assert schema.name == "minimal_table"
        assert schema.description is None
        assert len(schema.columns) == 1
        assert schema.columns[0].mode == "NULLABLE"  # Default mode
        assert schema.columns[0].description is None
    
    def test_load_from_dict_empty_columns(self):
        """Test that loading a schema with empty columns raises ValueError."""
        schema_dict = {
            "name": "empty_table",
            "columns": []
        }
        
        with pytest.raises(ValueError, match="Table must have at least one column"):
            SchemaLoader.load_from_dict(schema_dict)
    
    def test_load_from_dict_invalid_mode(self):
        """Test that invalid mode raises ValueError."""
        schema_dict = {
            "name": "test_table",
            "columns": [
                {
                    "name": "col1",
                    "type": "STRING",
                    "mode": "INVALID_MODE"
                }
            ]
        }
        
        with pytest.raises(ValueError, match="mode must be one of"):
            SchemaLoader.load_from_dict(schema_dict)
    
    def test_load_from_dict_mode_case_insensitive(self):
        """Test that mode is case-insensitive and normalized to uppercase."""
        schema_dict = {
            "name": "test_table",
            "columns": [
                {
                    "name": "col1",
                    "type": "STRING",
                    "mode": "required"
                }
            ]
        }
        
        schema = SchemaLoader.load_from_dict(schema_dict)
        assert schema.columns[0].mode == "REQUIRED"
    
    def test_load_from_json_string(self):
        """Test loading schema from JSON string."""
        json_string = json.dumps({
            "name": "json_table",
            "columns": [
                {
                    "name": "id",
                    "type": "INTEGER"
                }
            ]
        })
        
        schema = SchemaLoader.load_from_json_string(json_string)
        
        assert schema.name == "json_table"
        assert len(schema.columns) == 1
    
    def test_load_from_json_string_invalid_json(self):
        """Test that invalid JSON string raises an error."""
        invalid_json = "{ invalid json }"
        
        with pytest.raises(json.JSONDecodeError):
            SchemaLoader.load_from_json_string(invalid_json)
    
    def test_load_from_file(self):
        """Test loading schema from a file."""
        schema_dict = {
            "name": "file_table",
            "description": "Loaded from file",
            "columns": [
                {
                    "name": "id",
                    "type": "INTEGER",
                    "mode": "REQUIRED"
                },
                {
                    "name": "value",
                    "type": "FLOAT"
                }
            ]
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema_dict, f)
            temp_path = f.name
        
        try:
            schema = SchemaLoader.load_from_file(temp_path)
            
            assert schema.name == "file_table"
            assert schema.description == "Loaded from file"
            assert len(schema.columns) == 2
        finally:
            # Clean up
            Path(temp_path).unlink()
    
    def test_load_from_file_not_found(self):
        """Test that loading from non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Schema file not found"):
            SchemaLoader.load_from_file("/nonexistent/path/schema.json")
    
    def test_all_sql_types(self):
        """Test that all SQL types can be loaded."""
        schema_dict = {
            "name": "all_types_table",
            "columns": [
                {"name": "col_string", "type": "STRING"},
                {"name": "col_integer", "type": "INTEGER"},
                {"name": "col_int64", "type": "INT64"},
                {"name": "col_float", "type": "FLOAT"},
                {"name": "col_float64", "type": "FLOAT64"},
                {"name": "col_boolean", "type": "BOOLEAN"},
                {"name": "col_bool", "type": "BOOL"},
                {"name": "col_timestamp", "type": "TIMESTAMP"},
                {"name": "col_datetime", "type": "DATETIME"},
                {"name": "col_date", "type": "DATE"},
                {"name": "col_numeric", "type": "NUMERIC"},
                {"name": "col_bignumeric", "type": "BIGNUMERIC"},
                {"name": "col_bytes", "type": "BYTES"},
                {"name": "col_json", "type": "JSON"},
            ]
        }
        
        schema = SchemaLoader.load_from_dict(schema_dict)
        
        assert len(schema.columns) == 14
        assert schema.columns[0].type == SQLType.STRING
        assert schema.columns[1].type == SQLType.INTEGER
        assert schema.columns[7].type == SQLType.TIMESTAMP
        assert schema.columns[13].type == SQLType.JSON
    
    def test_column_schema_validation(self):
        """Test ColumnSchema validation."""
        # Valid column
        col = ColumnSchema(name="test_col", type=SQLType.STRING, mode="REQUIRED")
        assert col.name == "test_col"
        assert col.type == SQLType.STRING
        assert col.mode == "REQUIRED"
        
        # Valid column with default mode
        col2 = ColumnSchema(name="test_col2", type=SQLType.INTEGER)
        assert col2.mode == "NULLABLE"
    
    def test_repeated_mode(self):
        """Test that REPEATED mode is accepted."""
        schema_dict = {
            "name": "test_table",
            "columns": [
                {
                    "name": "tags",
                    "type": "STRING",
                    "mode": "REPEATED"
                }
            ]
        }
        
        schema = SchemaLoader.load_from_dict(schema_dict)
        assert schema.columns[0].mode == "REPEATED"
