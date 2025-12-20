"""
Parquet exporter for writing data to parquet files.

Handles consistent timestamp conversion for both parquet and BigQuery compatibility.
"""

from pathlib import Path
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

from .schema_loader import TableSchema
from .data_caster import DataCaster


class ParquetExporter:
    """
    Exports data to parquet files with consistent schema handling.

    Ensures timestamps are properly formatted for BigQuery compatibility
    and maintains data type consistency across platforms.
    """

    def __init__(self, schema: TableSchema):
        """
        Initialize the ParquetExporter with a schema.

        Args:
            schema: TableSchema defining the data structure
        """
        self.schema = schema
        self.caster = DataCaster(schema)

        if HAS_STRUCTLOG:
            logger.info("ParquetExporter initialized", table_name=schema.name)
        else:
            logger.info(f"ParquetExporter initialized for table {schema.name}")

    def export_dataframe(
        self,
        df: pd.DataFrame,
        output_path: str | Path,
        cast_types: bool = True,
        compression: str = "snappy",
        **kwargs: Any,
    ) -> None:
        """
        Export a DataFrame to a parquet file.

        Args:
            df: DataFrame to export
            output_path: Path to the output parquet file
            cast_types: Whether to cast types according to schema (default: True)
            compression: Compression algorithm (default: 'snappy')
            **kwargs: Additional arguments to pass to DataFrame.to_parquet()
        """
        # Cast types if requested
        if cast_types:
            df = self.caster.cast_dataframe(df)

        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to parquet with BigQuery-compatible settings
        if HAS_STRUCTLOG:
            logger.info(
                "Writing parquet file",
                output_path=str(output_path),
                num_rows=len(df),
                num_columns=len(df.columns),
            )
        else:
            logger.info(f"Writing {len(df)} rows to {output_path}")

        df.to_parquet(output_path, engine="pyarrow", compression=compression, index=False, **kwargs)

        if HAS_STRUCTLOG:
            logger.info("Parquet file written successfully", output_path=str(output_path))
        else:
            logger.info(f"Parquet file written successfully to {output_path}")

    def export_records(
        self,
        records: list[dict[str, Any]],
        output_path: str | Path,
        cast_types: bool = True,
        compression: str = "snappy",
        **kwargs: Any,
    ) -> None:
        """
        Export a list of records to a parquet file.

        Args:
            records: List of dictionaries to export
            output_path: Path to the output parquet file
            cast_types: Whether to cast types according to schema (default: True)
            compression: Compression algorithm (default: 'snappy')
            **kwargs: Additional arguments to pass to DataFrame.to_parquet()
        """
        # Convert records to DataFrame
        df = pd.DataFrame(records)

        # Export using the DataFrame method
        self.export_dataframe(
            df, output_path, cast_types=cast_types, compression=compression, **kwargs
        )

    def read_parquet(self, input_path: str | Path) -> pd.DataFrame:
        """
        Read a parquet file and return a DataFrame.

        This is a convenience method for reading parquet files.

        Args:
            input_path: Path to the parquet file

        Returns:
            DataFrame with the parquet data
        """
        input_path = Path(input_path)

        if not input_path.exists():
            raise FileNotFoundError(f"Parquet file not found: {input_path}")

        if HAS_STRUCTLOG:
            logger.info("Reading parquet file", input_path=str(input_path))
        else:
            logger.info(f"Reading parquet file from {input_path}")

        df = pd.read_parquet(input_path, engine="pyarrow")

        if HAS_STRUCTLOG:
            logger.info(
                "Parquet file read successfully", num_rows=len(df), num_columns=len(df.columns)
            )
        else:
            logger.info(f"Read {len(df)} rows from parquet file")

        return df
