#!/usr/bin/env python
"""
Example usage of the lean_hatch ETL utility package.

This example demonstrates:
1. Loading a schema from JSON
2. Generating sample data
3. Casting the data to match the schema
4. Exporting to parquet format
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path to import etl module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from schema_registry import SchemaLoader, DataCaster, ParquetExporter
import pandas as pd


def generate_sample_transactions(num_records: int = 100):
    """Generate sample transaction data."""
    transactions = []
    
    for i in range(num_records):
        transaction = {
            "transaction_id": f"TX{i:04d}",
            "customer_id": random.randint(1000, 9999),
            "transaction_amount": round(random.uniform(10.0, 1000.0), 2),
            "transaction_timestamp": (
                datetime.now() - timedelta(days=random.randint(0, 365))
            ).isoformat(),
            "transaction_date": (
                datetime.now() - timedelta(days=random.randint(0, 365))
            ).date().isoformat(),
            "is_refunded": random.choice([True, False, None]),
            "payment_method": random.choice(["credit_card", "debit_card", "paypal", "crypto"]),
            "metadata": {"source": "web", "campaign": random.choice(["summer_sale", "winter_promo", None])}
        }
        transactions.append(transaction)
    
    return transactions


def main():
    """Main demonstration of ETL utility."""
    
    print("=" * 80)
    print("lean_hatch ETL Utility - Example Usage")
    print("=" * 80)
    print()
    
    # 1. Load schema from JSON
    print("Step 1: Loading schema from JSON...")
    schema_path = os.path.join(
        os.path.dirname(__file__), 
        'customer_transactions_schema.json'
    )
    schema = SchemaLoader.load_from_file(schema_path)
    print(f"✓ Loaded schema: {schema.name}")
    print(f"  - Columns: {len(schema.columns)}")
    for col in schema.columns:
        print(f"    • {col.name}: {col.type} ({col.mode})")
    print()
    
    # 2. Generate sample data
    print("Step 2: Generating sample transaction data...")
    num_records = 100
    transactions = generate_sample_transactions(num_records)
    print(f"✓ Generated {num_records} sample transactions")
    print(f"  Sample record: {transactions[0]}")
    print()
    
    # 3. Cast data using DataCaster
    print("Step 3: Casting data to match schema...")
    caster = DataCaster(schema)
    
    # Convert to DataFrame for efficient processing
    df = pd.DataFrame(transactions)
    print(f"  Original DataFrame shape: {df.shape}")
    print(f"  Original dtypes:")
    for col in df.columns:
        print(f"    • {col}: {df[col].dtype}")
    print()
    
    # Cast the DataFrame
    df_casted = caster.cast_dataframe(df)
    print(f"✓ Data casted successfully")
    print(f"  Casted DataFrame shape: {df_casted.shape}")
    print(f"  Casted dtypes:")
    for col in df_casted.columns:
        print(f"    • {col}: {df_casted[col].dtype}")
    print()
    
    # 4. Export to parquet
    print("Step 4: Exporting to parquet file...")
    output_path = "/tmp/customer_transactions.parquet"
    exporter = ParquetExporter(schema)
    exporter.export_dataframe(df_casted, output_path, cast_types=False)  # Already casted
    
    # Get file size
    file_size = os.path.getsize(output_path)
    print(f"✓ Exported to parquet: {output_path}")
    print(f"  File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
    print()
    
    # 5. Read back and verify
    print("Step 5: Reading parquet file back for verification...")
    df_read = exporter.read_parquet(output_path)
    print(f"✓ Successfully read parquet file")
    print(f"  Records read: {len(df_read)}")
    print(f"  Data integrity check: {'PASSED' if len(df_read) == num_records else 'FAILED'}")
    print()
    
    # Display sample records
    print("Sample of exported data:")
    print(df_read.head(5).to_string())
    print()
    
    # Summary statistics
    print("=" * 80)
    print("Summary Statistics")
    print("=" * 80)
    print(f"Total transactions: {len(df_read)}")
    print(f"Total amount: ${df_read['transaction_amount'].sum():,.2f}")
    print(f"Average amount: ${df_read['transaction_amount'].mean():,.2f}")
    print(f"Refunded transactions: {df_read['is_refunded'].sum()}")
    print(f"Payment methods: {df_read['payment_method'].value_counts().to_dict()}")
    print()
    
    print("=" * 80)
    print("✓ ETL process completed successfully!")
    print("=" * 80)
    print()
    print("The data is now ready to be loaded into BigQuery or other data warehouses.")
    print(f"Parquet file location: {output_path}")


if __name__ == "__main__":
    main()
