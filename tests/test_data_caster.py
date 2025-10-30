"""
Tests for DataCaster class.
"""

import pytest
import pandas as pd
from datetime import datetime, date

from schema_registry import SchemaLoader, DataCaster
from schema_registry.schema_loader import TableSchema, ColumnSchema
from schema_registry.sql_types import SQLType


class TestDataCaster:
    """Test cases for DataCaster."""
    
    @pytest.fixture
    def simple_schema(self):
        """Create a simple test schema."""
        return SchemaLoader.load_from_dict({
            "name": "simple_table",
            "columns": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"},
                {"name": "name", "type": "STRING", "mode": "REQUIRED"},
                {"name": "value", "type": "FLOAT", "mode": "NULLABLE"},
            ]
        })
    
    @pytest.fixture
    def complex_schema(self):
        """Create a complex test schema with all types."""
        return SchemaLoader.load_from_dict({
            "name": "complex_table",
            "columns": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"},
                {"name": "name", "type": "STRING"},
                {"name": "amount", "type": "FLOAT"},
                {"name": "is_active", "type": "BOOLEAN"},
                {"name": "created_at", "type": "TIMESTAMP"},
                {"name": "birth_date", "type": "DATE"},
                {"name": "metadata", "type": "JSON"},
            ]
        })
    
    def test_init(self, simple_schema):
        """Test DataCaster initialization."""
        caster = DataCaster(simple_schema)
        
        assert caster.schema == simple_schema
        assert len(caster.column_map) == 3
        assert "id" in caster.column_map
        assert "name" in caster.column_map
        assert "value" in caster.column_map
    
    def test_cast_value_string(self, simple_schema):
        """Test casting values to string type."""
        caster = DataCaster(simple_schema)
        col = simple_schema.columns[1]  # name column (STRING)
        
        assert caster.cast_value("hello", col) == "hello"
        assert caster.cast_value(123, col) == "123"
        assert caster.cast_value(45.67, col) == "45.67"
    
    def test_cast_value_integer(self, simple_schema):
        """Test casting values to integer type."""
        caster = DataCaster(simple_schema)
        col = simple_schema.columns[0]  # id column (INTEGER)
        
        assert caster.cast_value(123, col) == 123
        assert caster.cast_value("456", col) == 456
        assert caster.cast_value(78.9, col) == 78
    
    def test_cast_value_float(self, simple_schema):
        """Test casting values to float type."""
        caster = DataCaster(simple_schema)
        col = simple_schema.columns[2]  # value column (FLOAT)
        
        assert caster.cast_value(123.45, col) == 123.45
        assert caster.cast_value("67.89", col) == 67.89
        assert caster.cast_value(100, col) == 100.0
    
    def test_cast_value_required_not_null(self, simple_schema):
        """Test that required columns cannot be null."""
        caster = DataCaster(simple_schema)
        col = simple_schema.columns[0]  # id column (REQUIRED)
        
        with pytest.raises(ValueError, match="Required column 'id' cannot be null"):
            caster.cast_value(None, col)
    
    def test_cast_value_nullable_can_be_null(self, simple_schema):
        """Test that nullable columns can be null."""
        caster = DataCaster(simple_schema)
        col = simple_schema.columns[2]  # value column (NULLABLE)
        
        # Should not raise an error
        result = caster.cast_value(None, col)
        assert result is None
    
    def test_cast_row_basic(self, simple_schema):
        """Test casting a basic row."""
        caster = DataCaster(simple_schema)
        
        row = {
            "id": "123",
            "name": "test",
            "value": "45.67"
        }
        
        casted = caster.cast_row(row)
        
        assert casted["id"] == 123
        assert casted["name"] == "test"
        assert casted["value"] == 45.67
    
    def test_cast_row_missing_nullable_column(self, simple_schema):
        """Test casting a row with missing nullable column."""
        caster = DataCaster(simple_schema)
        
        row = {
            "id": "123",
            "name": "test"
            # value is missing
        }
        
        casted = caster.cast_row(row)
        
        assert casted["id"] == 123
        assert casted["name"] == "test"
        assert casted["value"] is None
    
    def test_cast_records(self, simple_schema):
        """Test casting multiple records."""
        caster = DataCaster(simple_schema)
        
        records = [
            {"id": "1", "name": "first", "value": "10.5"},
            {"id": "2", "name": "second", "value": "20.5"},
            {"id": "3", "name": "third", "value": None},
        ]
        
        casted = caster.cast_records(records)
        
        assert len(casted) == 3
        assert casted[0]["id"] == 1
        assert casted[0]["value"] == 10.5
        assert casted[1]["id"] == 2
        assert casted[2]["value"] is None
    
    def test_cast_dataframe_basic(self, simple_schema):
        """Test casting a basic DataFrame."""
        caster = DataCaster(simple_schema)
        
        df = pd.DataFrame([
            {"id": "1", "name": "first", "value": "10.5"},
            {"id": "2", "name": "second", "value": "20.5"},
        ])
        
        casted_df = caster.cast_dataframe(df)
        
        assert len(casted_df) == 2
        assert casted_df["id"].iloc[0] == 1
        assert casted_df["name"].iloc[0] == "first"
        assert casted_df["value"].iloc[0] == 10.5
    
    def test_cast_dataframe_with_nulls(self, simple_schema):
        """Test casting DataFrame with null values."""
        caster = DataCaster(simple_schema)
        
        df = pd.DataFrame([
            {"id": "1", "name": "first", "value": "10.5"},
            {"id": "2", "name": "second", "value": None},
        ])
        
        casted_df = caster.cast_dataframe(df)
        
        assert casted_df["value"].iloc[0] == 10.5
        assert pd.isna(casted_df["value"].iloc[1])
    
    def test_cast_dataframe_required_field_validation(self, simple_schema):
        """Test that required fields with nulls raise ValueError."""
        caster = DataCaster(simple_schema)
        
        df = pd.DataFrame([
            {"id": "1", "name": "first", "value": "10.5"},
            {"id": None, "name": "second", "value": "20.5"},
        ])
        
        with pytest.raises(ValueError, match="Required column 'id' has 1 null values"):
            caster.cast_dataframe(df)
    
    def test_cast_dataframe_missing_column(self, simple_schema):
        """Test casting DataFrame with missing columns."""
        caster = DataCaster(simple_schema)
        
        df = pd.DataFrame([
            {"id": "1", "name": "first"},
            # value column is missing
        ])
        
        casted_df = caster.cast_dataframe(df)
        
        assert "value" in casted_df.columns
        assert pd.isna(casted_df["value"].iloc[0])
    
    def test_cast_dataframe_timestamp(self, complex_schema):
        """Test casting timestamp columns in DataFrame."""
        caster = DataCaster(complex_schema)
        
        df = pd.DataFrame([
            {
                "id": 1,
                "name": "test",
                "amount": 100.0,
                "is_active": True,
                "created_at": "2024-01-15 10:30:00",
                "birth_date": "1990-01-15",
                "metadata": {"key": "value"}
            }
        ])
        
        casted_df = caster.cast_dataframe(df)
        
        # Timestamp should be converted to pandas Timestamp with UTC
        assert isinstance(casted_df["created_at"].iloc[0], pd.Timestamp)
        assert casted_df["created_at"].iloc[0].tz is not None
    
    def test_cast_dataframe_date(self, complex_schema):
        """Test casting date columns in DataFrame."""
        caster = DataCaster(complex_schema)
        
        df = pd.DataFrame([
            {
                "id": 1,
                "name": "test",
                "amount": 100.0,
                "is_active": True,
                "created_at": "2024-01-15 10:30:00",
                "birth_date": "1990-01-15",
                "metadata": {"key": "value"}
            }
        ])
        
        casted_df = caster.cast_dataframe(df)
        
        # Date should be converted to date object
        assert isinstance(casted_df["birth_date"].iloc[0], date)
        assert casted_df["birth_date"].iloc[0] == date(1990, 1, 15)
    
    def test_cast_dataframe_boolean(self, complex_schema):
        """Test casting boolean columns in DataFrame."""
        caster = DataCaster(complex_schema)
        
        df = pd.DataFrame([
            {
                "id": 1,
                "name": "test",
                "amount": 100.0,
                "is_active": "true",
                "created_at": "2024-01-15",
                "birth_date": "1990-01-15",
                "metadata": {}
            },
            {
                "id": 2,
                "name": "test2",
                "amount": 200.0,
                "is_active": "false",
                "created_at": "2024-01-16",
                "birth_date": "1991-02-20",
                "metadata": {}
            }
        ])
        
        casted_df = caster.cast_dataframe(df)
        
        assert casted_df["is_active"].iloc[0] == True
        assert casted_df["is_active"].iloc[1] == False
    
    def test_cast_value_with_unsupported_type(self):
        """Test casting with unsupported SQL type."""
        schema = SchemaLoader.load_from_dict({
            "name": "test_table",
            "columns": [
                {"name": "col1", "type": "ARRAY"}
            ]
        })
        
        caster = DataCaster(schema)
        col = schema.columns[0]
        
        # Should return value unchanged (no handler for ARRAY)
        result = caster.cast_value([1, 2, 3], col)
        assert result == [1, 2, 3]
    
    def test_cast_dataframe_all_types(self, complex_schema):
        """Test casting DataFrame with all supported types."""
        caster = DataCaster(complex_schema)
        
        df = pd.DataFrame([
            {
                "id": "123",
                "name": "John Doe",
                "amount": "99.99",
                "is_active": "true",
                "created_at": "2024-01-15 10:30:00",
                "birth_date": "1990-05-20",
                "metadata": '{"city": "NYC", "age": 34}'
            }
        ])
        
        casted_df = caster.cast_dataframe(df)
        
        assert casted_df["id"].iloc[0] == 123
        assert casted_df["name"].iloc[0] == "John Doe"
        assert casted_df["amount"].iloc[0] == 99.99
        assert casted_df["is_active"].iloc[0] == True
        assert isinstance(casted_df["created_at"].iloc[0], pd.Timestamp)
        assert isinstance(casted_df["birth_date"].iloc[0], date)
        assert isinstance(casted_df["metadata"].iloc[0], dict)
        assert casted_df["metadata"].iloc[0]["city"] == "NYC"
