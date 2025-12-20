"""
Data caster for converting data to match schema definitions.

Uses type handlers to cast data values to the appropriate SQL types.
"""

from typing import Any
import pandas as pd

try:
    import structlog
    import time

    logger = structlog.get_logger()
    HAS_STRUCTLOG = True
except ImportError:
    import logging
    import time

    logger = logging.getLogger(__name__)
    HAS_STRUCTLOG = False
from .schema_loader import TableSchema, ColumnSchema
from .sql_types import TYPE_HANDLERS, SQLType, SQLEngine


class DataCaster:
    """
    Casts data to match a schema definition.

    Supports casting individual values, dictionaries, lists of dictionaries,
    and pandas DataFrames.
    """

    def __init__(self, schema: TableSchema, sql_engine: SQLEngine = SQLEngine.BIGQUERY):
        """
        Initialize the DataCaster with a schema and SQL engine.

        Args:
            schema: TableSchema defining the target schema
            sql_engine: Target SQL engine (defaults to BIGQUERY)
        """
        self.schema = schema
        self.column_map = {col.name: col for col in schema.columns}
        self.sql_engine = sql_engine

        # Lazy load dialect
        if sql_engine == SQLEngine.SQLITE:
            from .dialects.sqlite import SQLiteDialect

            self.dialect = SQLiteDialect()
        else:
            # Default to BigQuery
            from .dialects.bigquery import BigQueryDialect

            self.dialect = BigQueryDialect()

        self.pandas_dtype_map = self.dialect.get_pandas_dtype_map()

        if HAS_STRUCTLOG:
            logger.info(
                "DataCaster initialized",
                table_name=schema.name,
                num_columns=len(schema.columns),
                engine=sql_engine.value,
            )
        else:
            logger.info(
                f"DataCaster initialized for table {schema.name} with "
                f"{len(schema.columns)} columns (Engine: {sql_engine.value})"
            )

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
                logger.warning(
                    "No handler for type", column_name=column.name, column_type=column.type
                )
            else:
                logger.warning(f"No handler for type {column.type} in column {column.name}")
            return value

        # Apply the type handler
        try:
            casted_value = handler(value)
            return casted_value
        except Exception as e:
            if HAS_STRUCTLOG:
                logger.error(
                    "Error casting value",
                    column_name=column.name,
                    column_type=column.type,
                    error=str(e),
                )
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

    def apply_computations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply computed fields to the DataFrame.
        """
        # No copy here, modifying passed df directly as intended by the new design
        df_computed = df

        for column in self.schema.columns:
            if not column.computation:
                continue

            comp_str = column.computation
            try:
                # Parse simple function syntax: func(arg, 'param')
                # Very basic parser for now: strftime(col, 'fmt')
                if comp_str.startswith("strftime(") and comp_str.endswith(")"):
                    # Extract content
                    content = comp_str[9:-1]  # remove strftime( and )
                    parts = [p.strip() for p in content.split(",")]
                    if len(parts) == 2:
                        source_col = parts[0]
                        fmt = parts[1].strip("'\"")  # remove quotes

                        if source_col in df_computed.columns:
                            df_computed[column.name] = pd.to_datetime(
                                df_computed[source_col], errors="coerce"
                            ).dt.strftime(fmt)

                elif comp_str.startswith("constant(") and comp_str.endswith(")"):
                    # constant(value)
                    content = comp_str[9:-1]
                    val = content.strip("'\"")
                    df_computed[column.name] = val

                    df_computed[column.name] = val

                elif comp_str == "now()":
                    df_computed[column.name] = int(time.time())

                else:
                    if HAS_STRUCTLOG:
                        logger.warning(
                            "Unknown computation format",
                            column_name=column.name,
                            computation=comp_str,
                        )
                    else:
                        logger.warning(f"Unknown computation format for {column.name}: {comp_str}")

            except Exception as e:
                if HAS_STRUCTLOG:
                    logger.error(
                        "Error computing field",
                        column_name=column.name,
                        computation=column.computation,
                        error=str(e),
                    )
                else:
                    logger.error(f"Error computing field {column.name}: {e}")

        return df_computed

    def cast_dataframe(self, df: pd.DataFrame, inplace: bool = True) -> pd.DataFrame:
        """
        Cast a pandas DataFrame to match the schema.

        This method is optimized for DataFrame operations and handles
        timestamp conversions consistently for both parquet and BigQuery.

        Args:
            df: Input DataFrame
        inplace: If True, modify the DataFrame in-place. If False, return a copy. Defaults to True.

        Returns:
            DataFrame with casted columns
        """
        if HAS_STRUCTLOG:
            logger.info("Casting DataFrame", table_name=self.schema.name, num_rows=len(df))
        else:
            logger.info(f"Casting DataFrame for {self.schema.name} with {len(df)} rows")

        if inplace:
            casted_df = df
        else:
            casted_df = df.copy()

        # Apply computations first to generate derived fields
        casted_df = self.apply_computations(casted_df)

        for column in self.schema.columns:
            if column.name not in casted_df.columns:
                # Add missing columns with None values
                casted_df[column.name] = None

            # Apply type casting
            handler = TYPE_HANDLERS.get(column.type)
            if handler:
                try:
                    if column.name not in casted_df.columns:
                        continue

                    current_dtype = casted_df[column.name].dtype

                    # For timestamp columns, use pandas-optimized conversion
                    if column.type in (SQLType.TIMESTAMP, SQLType.DATETIME):
                        # Optimization: Skip if already datetime
                        if pd.api.types.is_datetime64_any_dtype(current_dtype):
                            # Ensure UTC for TIMESTAMP if needed
                            if column.type == SQLType.TIMESTAMP:
                                # If no timezone, localize. If timezone, convert.
                                # For now, simplistic check: if it is datetime64[ns, UTC], skip.
                                if str(current_dtype) == "datetime64[ns, UTC]":
                                    continue
                                # Else falling through to to_datetime might be safest for tz conversion
                            else:
                                # DATETIME (no tz)
                                if str(current_dtype).startswith("datetime64[ns]"):
                                    continue

                        # Ensure UTC timezone for timestamps (BigQuery requirement)
                        casted_df[column.name] = pd.to_datetime(
                            casted_df[column.name],
                            utc=(column.type == SQLType.TIMESTAMP),
                            errors="coerce",
                        )
                    elif column.type == SQLType.DATE:
                        # Optimization: Skip if already date objects (object dtype usually) or datetime
                        # Hard to verify 'date' objects in object dtype efficiently without checking values.
                        # But if it is datetime, we can .dt.date

                        # Convert to datetime then extract date
                        casted_df[column.name] = pd.to_datetime(
                            casted_df[column.name], errors="coerce"
                        ).dt.date
                    else:
                        # Optimization: Try to use batch astype if dialect provides a map
                        target_dtype = self.pandas_dtype_map.get(column.type)

                        # Check if already correct dtype
                        # Optimization: JSON/ARRAY/STRUCT types are object,
                        # but need parsing from string
                        complex_types = (SQLType.JSON, SQLType.ARRAY, SQLType.STRUCT)
                        if (
                            target_dtype
                            and str(current_dtype) == target_dtype
                            and column.type not in complex_types
                        ):
                            # Already correct
                            mapped = True
                        else:
                            mapped = False
                            if target_dtype and column.type not in complex_types:
                                try:
                                    casted_df[column.name] = casted_df[column.name].astype(
                                        target_dtype
                                    )
                                    mapped = True
                                except (ValueError, TypeError):
                                    pass

                            if not mapped:
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
                        logger.error("Error casting column", column_name=column.name, error=str(e))
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
            logger.info("Casting records", table_name=self.schema.name, num_records=len(records))
        else:
            logger.info(f"Casting {len(records)} records for {self.schema.name}")

        return [self.cast_row(row) for row in records]
