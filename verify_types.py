from schema_registry.sql_types import SQLType, TypeHandler
from schema_registry.schema_loader import SchemaLoader
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_types():
    print("Verifying SQL types...")
    
    # 1. Verify Enum values
    expected_new_types = ["UNIQUE", "UUID", "GUID", "REAL", "TEXT"]
    for type_name in expected_new_types:
        try:
            enum_val = getattr(SQLType, type_name)
            print(f"✅ SQLType.{type_name} exists: {enum_val}")
        except AttributeError:
            print(f"❌ SQLType.{type_name} missing")
            return

    # 2. Verify Schema Loading with Pydantic
    schema_json = """
    {
      "name": "test_table",
      "columns": [
        {"name": "id", "type": "UUID"},
        {"name": "guid_col", "type": "GUID"},
        {"name": "unique_col", "type": "UNIQUE"},
        {"name": "text_col", "type": "TEXT"},
        {"name": "real_col", "type": "REAL"}
      ]
    }
    """
    try:
        schema = SchemaLoader.load_from_json_string(schema_json)
        print("✅ Schema loaded successfully with new types")
        for col in schema.columns:
            print(f"   - Column {col.name}: {col.type}")
    except Exception as e:
        print(f"❌ Schema loading failed: {e}")
        return

    # 3. Verify Type Handling
    print("\nVerifying TypeHandler...")
    
    # Text-like types
    text_val = "some-unique-string"
    assert TypeHandler.to_string(text_val) == text_val, "Failed GUID/TEXT string conversion"
    print("✅ to_string handler works for text-like types")

    # Real type
    float_val = 123.456
    float_str = "123.456"
    assert TypeHandler.to_float(float_val) == float_val, "Failed REAL float conversion"
    assert TypeHandler.to_float(float_str) == float_val, "Failed REAL string->float conversion"
    print("✅ to_float handler works for REAL type")

if __name__ == "__main__":
    verify_types()
