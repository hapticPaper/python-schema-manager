"""
Tests for ParquetExporter class.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
from datetime import datetime, date
import random

from schema_registry import SchemaLoader, ParquetExporter


class TestParquetExporter:
    """Test cases for ParquetExporter."""
    
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
        """Create a complex test schema."""
        return SchemaLoader.load_from_dict({
            "name": "complex_table",
            "columns": [
                {"name": "id", "type": "INTEGER"},
                {"name": "name", "type": "STRING"},
                {"name": "amount", "type": "FLOAT"},
                {"name": "is_active", "type": "BOOLEAN"},
                {"name": "created_at", "type": "TIMESTAMP"},
                {"name": "birth_date", "type": "DATE"},
            ]
        })
    
    @pytest.fixture
    def temp_parquet_path(self):
        """Create a temporary parquet file path."""
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            path = Path(f.name)
        
        yield path
        
        # Cleanup
        if path.exists():
            path.unlink()
    
    def test_init(self, simple_schema):
        """Test ParquetExporter initialization."""
        exporter = ParquetExporter(simple_schema)
        
        assert exporter.schema == simple_schema
        assert exporter.caster is not None
    
    def test_export_dataframe_basic(self, simple_schema, temp_parquet_path):
        """Test basic DataFrame export."""
        exporter = ParquetExporter(simple_schema)
        
        df = pd.DataFrame([
            {"id": 1, "name": "first", "value": 10.5},
            {"id": 2, "name": "second", "value": 20.5},
        ])
        
        exporter.export_dataframe(df, temp_parquet_path, cast_types=False)
        
        assert temp_parquet_path.exists()
        assert temp_parquet_path.stat().st_size > 0
    
    def test_export_dataframe_with_casting(self, simple_schema, temp_parquet_path):
        """Test DataFrame export with type casting."""
        exporter = ParquetExporter(simple_schema)
        
        df = pd.DataFrame([
            {"id": "1", "name": "first", "value": "10.5"},
            {"id": "2", "name": "second", "value": "20.5"},
        ])
        
        exporter.export_dataframe(df, temp_parquet_path, cast_types=True)
        
        assert temp_parquet_path.exists()
        
        # Read back and verify types
        df_read = pd.read_parquet(temp_parquet_path)
        assert df_read["id"].iloc[0] == 1
        assert df_read["value"].iloc[0] == 10.5
    
    def test_export_dataframe_creates_directory(self, simple_schema):
        """Test that export creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir1" / "subdir2" / "output.parquet"
            
            exporter = ParquetExporter(simple_schema)
            df = pd.DataFrame([{"id": 1, "name": "test", "value": 10.0}])
            
            exporter.export_dataframe(df, output_path, cast_types=False)
            
            assert output_path.exists()
    
    def test_export_dataframe_compression_snappy(self, simple_schema, temp_parquet_path):
        """Test DataFrame export with snappy compression."""
        exporter = ParquetExporter(simple_schema)
        
        df = pd.DataFrame([
            {"id": 1, "name": "first", "value": 10.5},
            {"id": 2, "name": "second", "value": 20.5},
        ])
        
        exporter.export_dataframe(df, temp_parquet_path, compression='snappy')
        
        assert temp_parquet_path.exists()
    
    def test_export_dataframe_compression_gzip(self, simple_schema, temp_parquet_path):
        """Test DataFrame export with gzip compression."""
        exporter = ParquetExporter(simple_schema)
        
        df = pd.DataFrame([
            {"id": 1, "name": "first", "value": 10.5},
            {"id": 2, "name": "second", "value": 20.5},
        ])
        
        exporter.export_dataframe(df, temp_parquet_path, compression='gzip')
        
        assert temp_parquet_path.exists()
    
    def test_export_records_basic(self, simple_schema, temp_parquet_path):
        """Test basic records export."""
        exporter = ParquetExporter(simple_schema)
        
        records = [
            {"id": 1, "name": "first", "value": 10.5},
            {"id": 2, "name": "second", "value": 20.5},
        ]
        
        exporter.export_records(records, temp_parquet_path, cast_types=False)
        
        assert temp_parquet_path.exists()
    
    def test_export_records_with_casting(self, simple_schema, temp_parquet_path):
        """Test records export with type casting."""
        exporter = ParquetExporter(simple_schema)
        
        records = [
            {"id": "1", "name": "first", "value": "10.5"},
            {"id": "2", "name": "second", "value": "20.5"},
        ]
        
        exporter.export_records(records, temp_parquet_path, cast_types=True)
        
        assert temp_parquet_path.exists()
        
        # Read back and verify
        df_read = pd.read_parquet(temp_parquet_path)
        assert len(df_read) == 2
        assert df_read["id"].iloc[0] == 1
    
    def test_read_parquet_basic(self, simple_schema, temp_parquet_path):
        """Test reading parquet file."""
        exporter = ParquetExporter(simple_schema)
        
        # Create and export data
        df = pd.DataFrame([
            {"id": 1, "name": "first", "value": 10.5},
            {"id": 2, "name": "second", "value": 20.5},
            {"id": 3, "name": "third", "value": 30.5},
        ])
        
        exporter.export_dataframe(df, temp_parquet_path, cast_types=False)
        
        # Read back
        df_read = exporter.read_parquet(temp_parquet_path)
        
        assert len(df_read) == 3
        assert list(df_read.columns) == ["id", "name", "value"]
        assert df_read["id"].iloc[0] == 1
        assert df_read["name"].iloc[1] == "second"
        assert df_read["value"].iloc[2] == 30.5
    
    def test_read_parquet_file_not_found(self, simple_schema):
        """Test reading non-existent parquet file raises error."""
        exporter = ParquetExporter(simple_schema)
        
        with pytest.raises(FileNotFoundError, match="Parquet file not found"):
            exporter.read_parquet("/nonexistent/path/file.parquet")
    
    def test_export_and_read_timestamp(self, complex_schema, temp_parquet_path):
        """Test exporting and reading timestamp data."""
        exporter = ParquetExporter(complex_schema)
        
        df = pd.DataFrame([
            {
                "id": 1,
                "name": "test",
                "amount": 100.0,
                "is_active": True,
                "created_at": "2024-01-15 10:30:00",
                "birth_date": "1990-01-15"
            }
        ])
        
        # Export with casting
        exporter.export_dataframe(df, temp_parquet_path, cast_types=True)
        
        # Read back
        df_read = exporter.read_parquet(temp_parquet_path)
        
        assert len(df_read) == 1
        # Timestamp should be preserved
        assert isinstance(df_read["created_at"].iloc[0], pd.Timestamp)
    
    def test_export_and_read_date(self, complex_schema, temp_parquet_path):
        """Test exporting and reading date data."""
        exporter = ParquetExporter(complex_schema)
        
        df = pd.DataFrame([
            {
                "id": 1,
                "name": "test",
                "amount": 100.0,
                "is_active": True,
                "created_at": "2024-01-15 10:30:00",
                "birth_date": "1990-01-15"
            }
        ])
        
        # Export with casting
        exporter.export_dataframe(df, temp_parquet_path, cast_types=True)
        
        # Read back
        df_read = exporter.read_parquet(temp_parquet_path)
        
        assert len(df_read) == 1
        # Date should be converted to date object by caster
        assert df_read["birth_date"].iloc[0] == date(1990, 1, 15)
    
    def test_export_and_read_boolean(self, complex_schema, temp_parquet_path):
        """Test exporting and reading boolean data."""
        exporter = ParquetExporter(complex_schema)
        
        df = pd.DataFrame([
            {
                "id": 1,
                "name": "test1",
                "amount": 100.0,
                "is_active": "true",
                "created_at": "2024-01-15",
                "birth_date": "1990-01-15"
            },
            {
                "id": 2,
                "name": "test2",
                "amount": 200.0,
                "is_active": "false",
                "created_at": "2024-01-16",
                "birth_date": "1991-02-20"
            }
        ])
        
        # Export with casting
        exporter.export_dataframe(df, temp_parquet_path, cast_types=True)
        
        # Read back
        df_read = exporter.read_parquet(temp_parquet_path)
        
        assert df_read["is_active"].iloc[0] == True
        assert df_read["is_active"].iloc[1] == False
    
    def test_export_large_dataset(self, simple_schema, temp_parquet_path):
        """Test exporting a larger dataset."""
        exporter = ParquetExporter(simple_schema)
        
        # Create a larger dataset
        records = [
            {
                "id": i,
                "name": f"name_{i}",
                "value": random.uniform(0, 1000)
            }
            for i in range(1000)
        ]
        
        df = pd.DataFrame(records)
        
        exporter.export_dataframe(df, temp_parquet_path, cast_types=False)
        
        # Read back and verify
        df_read = exporter.read_parquet(temp_parquet_path)
        
        assert len(df_read) == 1000
        assert list(df_read.columns) == ["id", "name", "value"]
    
    def test_export_with_null_values(self, simple_schema, temp_parquet_path):
        """Test exporting data with null values."""
        exporter = ParquetExporter(simple_schema)
        
        df = pd.DataFrame([
            {"id": 1, "name": "first", "value": 10.5},
            {"id": 2, "name": "second", "value": None},
            {"id": 3, "name": "third", "value": 30.5},
        ])
        
        exporter.export_dataframe(df, temp_parquet_path, cast_types=False)
        
        # Read back
        df_read = exporter.read_parquet(temp_parquet_path)
        
        assert pd.isna(df_read["value"].iloc[1])
        assert df_read["value"].iloc[0] == 10.5
        assert df_read["value"].iloc[2] == 30.5
    
    def test_roundtrip_data_integrity(self, complex_schema, temp_parquet_path):
        """Test that data roundtrip maintains integrity."""
        exporter = ParquetExporter(complex_schema)
        
        df_original = pd.DataFrame([
            {
                "id": 1,
                "name": "Alice",
                "amount": 123.45,
                "is_active": True,
                "created_at": "2024-01-15 10:30:00",
                "birth_date": "1990-05-20"
            },
            {
                "id": 2,
                "name": "Bob",
                "amount": 678.90,
                "is_active": False,
                "created_at": "2024-02-20 14:45:00",
                "birth_date": "1985-12-15"
            }
        ])
        
        # Export with casting
        exporter.export_dataframe(df_original, temp_parquet_path, cast_types=True)
        
        # Read back
        df_read = exporter.read_parquet(temp_parquet_path)
        
        assert len(df_read) == 2
        assert df_read["id"].iloc[0] == 1
        assert df_read["name"].iloc[0] == "Alice"
        assert df_read["amount"].iloc[0] == 123.45
        assert df_read["is_active"].iloc[0] == True
        assert df_read["birth_date"].iloc[1] == date(1985, 12, 15)
