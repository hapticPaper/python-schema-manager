from typing import List, Dict, Any
from .schema_loader import TableSchema
from .sql_types import SQLEngine

try:
    import structlog

    logger = structlog.get_logger()
    HAS_STRUCTLOG = True
except ImportError:
    import logging

    logger = logging.getLogger(__name__)
    HAS_STRUCTLOG = False


class MergeManager:
    """
    Manages generation of Merge/Upsert SQL statements.

    Supports:
    1. Validation of incoming columns against schema
    2. Generation of Dry Run SQL to preview changes
    3. Generation of standard MERGE SQL
    """

    def __init__(self, schema: TableSchema, engine: SQLEngine = SQLEngine.BIGQUERY):
        """
        Initialize the MergeManager.

        Args:
            schema: TableSchema defining the target table structure
            engine: Target SQL engine (defaults to BIGQUERY)
        """
        self.schema = schema
        self.engine = engine
        self.column_map = {col.name: col for col in schema.columns}

        if HAS_STRUCTLOG:
            logger.info(
                "MergeManager initialized", table_name=schema.name, engine=engine.value
            )
        else:
            logger.info(
                f"MergeManager initialized for table {schema.name} (Engine: {engine.value})"
            )

    def validate_incoming_columns(self, incoming_columns: List[str]) -> bool:
        """
        Ensures all incoming column names exist in the target schema.

        Args:
            incoming_columns: List of column names in the source/incoming data

        Returns:
            True if valid

        Raises:
            ValueError: If unknown columns are found
        """
        unknown_cols = [col for col in incoming_columns if col not in self.column_map]

        if unknown_cols:
            error_msg = (
                f"Incoming data contains unknown columns: {', '.join(unknown_cols)}"
            )
            if HAS_STRUCTLOG:
                logger.error("Schema validation failed", unknown_columns=unknown_cols)
            else:
                logger.error(error_msg)
            raise ValueError(error_msg)

        return True

    def generate_dry_run_sql(
        self,
        source_table: str,
        target_table: str,
        join_keys: List[str],
        update_columns: List[str],
        label_columns: List[str] = [],
    ) -> str:
        """
        Generates SQL to preview changes that would occur in a merge.

        The output aims to show ONLY relevant info:
        - Key fields (to identify the record)
        - Label fields (extra context)
        - The changes themselves (column: old -> new)

        Args:
            source_table: Name of the staging/incoming table
            target_table: Name of the existing target table
            join_keys: List of columns to join on (primary keys)
            update_columns: List of columns to check for changes/update
            label_columns: Extra columns to select for context (e.g. name, status)

        Returns:
            Review SQL string
        """

        # 1. Build Join Condition
        join_cond = " AND ".join([f"T.{k} = S.{k}" for k in join_keys])

        # 2. Build Selection for Keys and Labels
        select_clause_parts = []
        for k in join_keys:
            select_clause_parts.append(f"COALESCE(T.{k}, S.{k}) as {k}")

        for l in label_columns:
            if l not in join_keys:
                select_clause_parts.append(f"COALESCE(T.{l}, S.{l}) as {l}")

        # 3. Build Change Detection & Object Construction (BigQuery Dialect Focus)
        # We want arrays of objects {col: "col_name", old: "val", new: "val"}

        # This part constructs the complicated CASE checks for each column
        # and bundles them into an ARRAY of JSON/STRUCTs

        change_array_elements = []

        for col in update_columns:
            # Skip if it's a key
            if col in join_keys:
                continue

            # Basic inequality check suitable for standard types.
            # Note: NULL handling is tricky.
            # (T.col IS DISTINCT FROM S.col) would be nice, but standard SQL replacement:
            # (T.col <> S.col OR (T.col IS NULL AND S.col IS NOT NULL) OR (T.col IS NOT NULL AND S.col IS NULL))

            # Using BigQuery specific helpers for cleaner SQL if possible, but sticking to standard-ish structure
            # to maximize readibility.

            check_diff = f"""
                (T.{col} <> S.{col} OR (T.{col} IS NULL AND S.{col} IS NOT NULL) OR (T.{col} IS NOT NULL AND S.{col} IS NULL))
            """

            # Construct the diff object.
            # CAST is important because array elements must be same type.
            # We use STRING for everything in the diff report for simplicity.
            diff_object = f"""
                IF({check_diff}, 
                   JSON_OBJECT('column', '{col}', 'old', CAST(T.{col} AS STRING), 'new', CAST(S.{col} AS STRING)), 
                   NULL)
            """
            change_array_elements.append(diff_object)

        # Concatenate array build
        # We wrap in TO_JSON_STRING or ARRAY_AGG filter in a smarter way if needed.
        # But simpler: Make a big array, then filter NULLs?
        # BQ: ARRAY(SELECT x FROM UNNEST([...]) AS x WHERE x IS NOT NULL)

        array_construction = ",\n                ".join(change_array_elements)

        changes_column = f"""
        ARRAY(
            SELECT x FROM UNNEST([
                {array_construction}
            ]) AS x WHERE x IS NOT NULL
        ) as changes
        """

        # 4. Filter only rows with changes or new rows
        # Change condition: Same check as above OR new row

        # Updates
        updates_check_parts = []
        for col in update_columns:
            if col not in join_keys:
                updates_check_parts.append(f"""
                (T.{col} <> S.{col} OR (T.{col} IS NULL AND S.{col} IS NOT NULL) OR (T.{col} IS NOT NULL AND S.{col} IS NULL))
                """)

        if updates_check_parts:
            updates_check = "(" + " OR ".join(updates_check_parts) + ")"
        else:
            updates_check = "FALSE"  # Should warn if no update columns?

        # New records (T.id IS NULL)
        new_record_check = (
            f"T.{join_keys[0]} IS NULL"  # Assuming first key is sufficient indicator
        )

        final_select = ",\n            ".join(select_clause_parts)

        sql = f"""
        SELECT 
            {final_select},
            CASE 
                WHEN {new_record_check} THEN 'INSERT'
                ELSE 'UPDATE'
            END as change_type,
            {changes_column}
        FROM `{source_table}` S
        LEFT JOIN `{target_table}` T
            ON {join_cond}
        WHERE 
            {new_record_check}
            OR 
            {updates_check}
        """

        return sql.strip()

    def generate_merge_sql(
        self,
        source_table: str,
        target_table: str,
        join_keys: List[str],
        update_columns: List[str],
    ) -> str:
        """
        Generates the standard MERGE statement to apply changes.

        Args:
            source_table: Name of the staging/incoming table
            target_table: Name of the existing target table
            join_keys: List of columns to join on
            update_columns: List of columns to update

        Returns:
            Merge SQL string
        """
        join_cond = " AND ".join([f"T.{k} = S.{k}" for k in join_keys])

        # Update clause
        update_set = []
        for col in update_columns:
            if col not in join_keys:
                update_set.append(f"{col} = S.{col}")

        current_cols = list(self.column_map.keys())
        insert_cols = ", ".join(current_cols)
        insert_vals = ", ".join([f"S.{col}" for col in current_cols])

        sql = f"""
        MERGE `{target_table}` T
        USING `{source_table}` S
        ON {join_cond}
        WHEN MATCHED AND (
            {" OR ".join([f"T.{col} <> S.{col} OR (T.{col} IS NULL AND S.{col} IS NOT NULL) OR (T.{col} IS NOT NULL AND S.{col} IS NULL)" for col in update_columns if col not in join_keys])}
        ) THEN
            UPDATE SET {", ".join(update_set)}
        WHEN NOT MATCHED THEN
            INSERT ({insert_cols})
            VALUES ({insert_vals})
        """

        return sql.strip()

    def _quote_identifier(self, identifier: str) -> str:
        """Quotes an identifier based on the SQL engine."""
        if self.engine == SQLEngine.POSTGRES:
            return f'"{identifier}"'
        # Default to BigQuery/backticks for others
        return f"`{identifier}`"

    def create_table_sql(self, table_name: str) -> str:
        """
        Generates CREATE TABLE SQL based on the schema.

        Args:
            table_name: Name of the table to create

        Returns:
            CREATE TABLE SQL string
        """
        columns_sql = []
        for col in self.schema.columns:
            col_def = f"{col.name} {col.type.value}"

            if col.mode == "REQUIRED":
                col_def += " NOT NULL"
            elif col.mode == "REPEATED":
                col_def = f"{col.name} ARRAY<{col.type.value}>"  # BigQuery style

            columns_sql.append(col_def)

        cols_str = ",\n    ".join(columns_sql)
        quoted_table = self._quote_identifier(table_name)
        return f"CREATE TABLE IF NOT EXISTS {quoted_table} (\n    {cols_str}\n)"

    def _format_value_for_sql(self, value: Any) -> str:
        """Formats a Python value for SQL injection."""
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if isinstance(value, str):
            # Basic escaping - simplistic for now
            escaped = value.replace("'", "\\'")
            return f"'{escaped}'"
        if isinstance(value, (int, float)):
            return str(value)
        # Datetime/Date/Timestamp handling - basic ISO format
        if hasattr(value, "isoformat"):
            return f"'{value.isoformat()}'"

        return str(value)

    def generate_insert_sql(self, table_name: str, data: Dict[str, Any]) -> str:
        """
        Generates a single INSERT statement.

        Args:
            table_name: Name of the target table
            data: Dictionary of {column: value}

        Returns:
            INSERT SQL string
        """
        self.validate_incoming_columns(list(data.keys()))

        columns = list(data.keys())

        vals = [self._format_value_for_sql(data[col]) for col in columns]

        cols_str = ", ".join(columns)
        vals_str = ", ".join(vals)
        quoted_table = self._quote_identifier(table_name)

        return f"INSERT INTO {quoted_table} ({cols_str}) VALUES ({vals_str})"

    def generate_bulk_insert_sql(
        self, table_name: str, data: List[Dict[str, Any]]
    ) -> str:
        """
        Generates a bulk INSERT statement.

        Args:
            table_name: Name of the target table
            data: List of dictionaries

        Returns:
            Bulk INSERT SQL string
        """
        if not data:
            return ""

        # Validate columns for the first record
        columns = list(data[0].keys())
        self.validate_incoming_columns(columns)

        values_groups = []
        for row in data:
            row_vals = [self._format_value_for_sql(row.get(col)) for col in columns]
            values_groups.append(f"({', '.join(row_vals)})")

        cols_str = ", ".join(columns)
        vals_block = ",\n    ".join(values_groups)
        quoted_table = self._quote_identifier(table_name)

        return f"INSERT INTO {quoted_table} ({cols_str}) VALUES \n    {vals_block}"
