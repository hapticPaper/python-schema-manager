"""
Schema loader for reading JSON schema definitions.

Loads schema definitions from JSON files and validates them using pydantic.
"""

import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .sql_types import SQLType


class ColumnSchema(BaseModel):
    """Schema definition for a single column."""
    
    model_config = ConfigDict(use_enum_values=False)
    
    name: str = Field(..., description="Column name")
    type: SQLType = Field(..., description="SQL type for the column")
    mode: str = Field(default="NULLABLE", description="Column mode: NULLABLE, REQUIRED, or REPEATED")
    description: str | None = Field(default=None, description="Column description")
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Validate that mode is one of the allowed values."""
        allowed_modes = {'NULLABLE', 'REQUIRED', 'REPEATED'}
        if v.upper() not in allowed_modes:
            raise ValueError(f"mode must be one of {allowed_modes}")
        return v.upper()


class TableSchema(BaseModel):
    """Schema definition for a table."""
    
    model_config = ConfigDict(use_enum_values=False)
    
    name: str = Field(..., description="Table name")
    description: str | None = Field(default=None, description="Table description")
    columns: list[ColumnSchema] = Field(..., description="List of column schemas")
    
    @field_validator('columns')
    @classmethod
    def validate_columns(cls, v: list[ColumnSchema]) -> list[ColumnSchema]:
        """Validate that there is at least one column."""
        if not v:
            raise ValueError("Table must have at least one column")
        return v


class SchemaLoader:
    """Loads and validates schema definitions from JSON files."""
    
    @staticmethod
    def load_from_file(file_path: str | Path) -> TableSchema:
        """
        Load schema from a JSON file.
        
        Args:
            file_path: Path to the JSON schema file
            
        Returns:
            TableSchema object
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the JSON is invalid or doesn't match the schema
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Schema file not found: {file_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return SchemaLoader.load_from_dict(data)
    
    @staticmethod
    def load_from_dict(schema_dict: dict[str, Any]) -> TableSchema:
        """
        Load schema from a dictionary.
        
        Args:
            schema_dict: Dictionary containing schema definition
            
        Returns:
            TableSchema object
            
        Raises:
            ValueError: If the schema is invalid
        """
        return TableSchema(**schema_dict)
    
    @staticmethod
    def load_from_json_string(json_string: str) -> TableSchema:
        """
        Load schema from a JSON string.
        
        Args:
            json_string: JSON string containing schema definition
            
        Returns:
            TableSchema object
            
        Raises:
            ValueError: If the JSON is invalid or doesn't match the schema
        """
        data = json.loads(json_string)
        return SchemaLoader.load_from_dict(data)
