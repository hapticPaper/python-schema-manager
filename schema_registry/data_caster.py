"""
Data caster for converting data to match schema definitions.

Uses type handlers to cast data values to the appropriate SQL types.
"""

from typing import Any
import pandas as pd
try:
    import structlog
    logger = structlog.get_logger()
    HAS_STRUCTLOG = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    HAS_STRUCTLOG = False

from .schema_loader import TableSchema, ColumnSchema
from .sql_types import TYPE_HANDLERS, SQLType, PANDAS_DTYPE_MAP


class DataCaster:
    """
    Casts data to match a schema definition.
    
    Supports casting individual values, dictionaries, lists of dictionaries,
    and pandas DataFrames.
    """
    
    def __init__(self, schema: TableSchema):
        """
        Initialize the DataCaster with a schema.
        
        Args:
            schema: TableSchema defining the target schema
        """
        self.schema = schema
        self.column_map = {col.name: col for col in schema.columns}
        
        if HAS_STRUCTLOG:
            logger.info("DataCaster initialized", 
                       table_name=schema.name, 
                       num_columns=len(schema.columns))
        else:
            logger.info(f"DataCaster initialized for table {schema.name} with {len(schema.columns)} columns")
    
    def cast_value(self, value: Any, column: ColumnSchema) -> Any:
        """
        Cast a single value to the specified column type.
        
        Args:
            value: Value to cast
            column: Column schema defining the target type
            
        Returns:
            Casted value or None if casting fails
        """
        # Handle required fields - check for None or pd.NA
        if column.mode == "REQUIRED":
            try:
                if value is None or pd.isna(value):
                    raise ValueError(f"Required column '{column.name}' cannot be null")
            except (TypeError, ValueError) as e:
                if value is None:
                    raise ValueError(f"Required column '{column.name}' cannot be null")
        
        # Get the appropriate type handler
        handler = TYPE_HANDLERS.get(column.type)
        if handler is None:
            if HAS_STRUCTLOG:
                logger.warning("No handler for type", 
                             column_name=column.name, 
                             column_type=column.type)
            else:
                logger.warning(f"No handler for type {column.type} in column {column.name}")
            return value
        
        # Apply the type handler
        try:
            casted_value = handler(value)
            return casted_value
        except Exception as e:
            if HAS_STRUCTLOG:
                logger.error("Error casting value", 
                           column_name=column.name, 
                           column_type=column.type, 
                           error=str(e))
            else:
                logger.error(f"Error casting value for column {column.name}: {e}")
            return None
    
    def cast_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """
        Cast a dictionary row to match the schema.
        
        Args:
            row: Dictionary representing a single row
            
        Returns:
            Dictionary with casted values
        """
        casted_row = {}
        
        for col_name, column in self.column_map.items():
            value = row.get(col_name)
            casted_row[col_name] = self.cast_value(value, column)
        
        return casted_row
    
    def cast_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cast a pandas DataFrame to match the schema.
        
        This method is optimized for DataFrame operations and handles
        timestamp conversions consistently for both parquet and BigQuery.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with casted columns
        """
        if HAS_STRUCTLOG:
            logger.info("Casting DataFrame", 
                       table_name=self.schema.name, 
                       num_rows=len(df))
        else:
            logger.info(f"Casting DataFrame for {self.schema.name} with {len(df)} rows")
        
        casted_df = df.copy()
        
        for column in self.schema.columns:
            if column.name not in casted_df.columns:
                # Add missing columns with None values
                casted_df[column.name] = None
            
            # Apply type casting
            handler = TYPE_HANDLERS.get(column.type)
            if handler:
                try:
                    # For timestamp columns, use pandas-optimized conversion
                    if column.type in (SQLType.TIMESTAMP, SQLType.DATETIME):
                        # Ensure UTC timezone for timestamps (BigQuery requirement)
                        casted_df[column.name] = pd.to_datetime(
                            casted_df[column.name], 
                            utc=(column.type == SQLType.TIMESTAMP),
                            errors='coerce'
                        )
                    elif column.type == SQLType.DATE:
                        # Convert to datetime then extract date
                        casted_df[column.name] = pd.to_datetime(
                            casted_df[column.name], 
                            errors='coerce'
                        ).dt.date
                    else:
                        # Apply handler to each value
                        casted_df[column.name] = casted_df[column.name].apply(handler)
                    
                    # Handle required fields
                    if column.mode == "REQUIRED":
                        null_count = casted_df[column.name].isna().sum()
                        if null_count > 0:
                            raise ValueError(
                                f"Required column '{column.name}' has {null_count} null values"
                            )
                
                except Exception as e:
                    if HAS_STRUCTLOG:
                        logger.error("Error casting column", 
                                   column_name=column.name, 
                                   error=str(e))
                    else:
                        logger.error(f"Error casting column {column.name}: {e}")
                    raise
        
        return casted_df
    
    def cast_records(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Cast a list of dictionary records to match the schema.
        
        Args:
            records: List of dictionaries representing rows
            
        Returns:
            List of dictionaries with casted values
        """
        if HAS_STRUCTLOG:
            logger.info("Casting records", 
                       table_name=self.schema.name, 
                       num_records=len(records))
        else:
            logger.info(f"Casting {len(records)} records for {self.schema.name}")
        
        return [self.cast_row(row) for row in records]
