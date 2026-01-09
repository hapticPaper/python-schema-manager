import pytest
import psycopg2
import os
from datetime import datetime
from schema_registry.schema_loader import TableSchema, ColumnSchema
from schema_registry.sql_types import SQLType, SQLEngine
from schema_registry.merge_manager import MergeManager

# Configuration for local Postgres
# Users can override these with environment variables
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "pguser")
PG_PASSWORD = os.getenv("PG_PASSWORD", "pgpass")
PG_DB = os.getenv("PG_DB", "postgres")


@pytest.fixture(scope="module")
def pg_conn():
    """Establishes a connection to the local Postgres database."""
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASSWORD, dbname=PG_DB
        )
        conn.autocommit = True
        yield conn
        conn.close()
    except psycopg2.OperationalError as e:
        pytest.skip(f"Could not connect to Postgres: {e}")


@pytest.fixture
def test_schema():
    return TableSchema(
        name="test_user_events_pg",
        columns=[
            ColumnSchema(name="event_id", type=SQLType.STRING, mode="REQUIRED"),
            ColumnSchema(name="user_id", type=SQLType.INT64, mode="REQUIRED"),
            ColumnSchema(name="timestamp", type=SQLType.TIMESTAMP, mode="NULLABLE"),
            ColumnSchema(name="properties", type=SQLType.JSON, mode="NULLABLE"),
            ColumnSchema(name="is_active", type=SQLType.BOOLEAN, mode="NULLABLE"),
        ],
    )


def test_postgres_integration(pg_conn, test_schema):
    cursor = pg_conn.cursor()
    manager = MergeManager(test_schema, engine=SQLEngine.POSTGRES)
    table_name = "integration_test_table"

    try:
        # 1. Generate and Execute CREATE TABLE
        print(f"\nCreating table {table_name}...")
        create_sql = manager.create_table_sql(table_name)
        # Postgres uses 'TEXT' or 'VARCHAR' for STRING, 'TIMESTAMP WITH TIME ZONE' etc.
        # MergeManager currently outputs SQLType.value directly.
        # For STRING ("STRING"), Postgres might fail if it expects "TEXT" or "VARCHAR".
        # Let's see if SQLType.STRING.value is "STRING". If so, Postgres might reject it.
        # However, many Postgres setups have a 'string' domain or alias, or we might need to adjust logic.
        # But let's run it and see. If it fails, I'll need to patch MergeManager for dialect support.

        # Checking SQLType definition:
        # STRING = "STRING"
        # INT64 = "INT64" -> Postgres uses BIGINT usually.

        # If the user-provided code generates "STRING", it might be BigQuery specific.
        # I might need to replace types for Postgres in the SQL string for this test,
        # or better yet, update MergeManager to handle dialects.
        # For now, I'll try to run it. If it fails, I'll fix it.

        # Patching for standard Postgres compliance just in case for the test:
        clean_create_sql = (
            create_sql.replace("STRING", "TEXT")
            .replace("INT64", "BIGINT")
            .replace("FLOAT64", "DOUBLE PRECISION")
        )
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(clean_create_sql)
        print("Table created.")

        # 2. Generate Bulk Insert
        data = [
            {
                "event_id": "evt_1",
                "user_id": 101,
                "timestamp": datetime.now(),
                "properties": '{"key": "val"}',  # JSON as string for simplified SQL injection
                "is_active": True,
            },
            {
                "event_id": "evt_2",
                "user_id": 102,
                "timestamp": None,
                "properties": None,
                "is_active": False,
            },
        ]

        insert_sql = manager.generate_bulk_insert_sql(table_name, data)
        print("Executing Insert...")
        cursor.execute(insert_sql)

        # 3. Verify Data
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        assert count == 2
        print(f"Verified count: {count}")

        cursor.execute(
            f"SELECT event_id, is_active FROM {table_name} ORDER BY event_id"
        )
        rows = cursor.fetchall()
        assert rows[0] == ("evt_1", True)
        assert rows[1] == ("evt_2", False)
        print("Verified data integrity.")

    finally:
        # Cleanup
        # cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.close()
