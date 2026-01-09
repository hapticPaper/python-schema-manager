from datetime import date, datetime
from typing import Any, Type

from pydantic import BaseModel, ConfigDict, Field, create_model

from .schema_loader import TableSchema
from .sql_types import SQLType

# Mapping from SQLType to Python/Pydantic types
SQL_TYPE_MAPPING: dict[SQLType, Type[Any] | Any] = {
    SQLType.STRING: str,
    SQLType.INTEGER: int,
    SQLType.INT64: int,
    SQLType.FLOAT: float,
    SQLType.FLOAT64: float,
    SQLType.BOOLEAN: bool,
    SQLType.BOOL: bool,
    SQLType.TIMESTAMP: datetime,
    SQLType.DATETIME: datetime,
    SQLType.DATE: date,
    SQLType.NUMERIC: float,
    SQLType.BIGNUMERIC: float,
    SQLType.BYTES: bytes,
    SQLType.JSON: dict,  # Or Any, but dict is usually what we want for JSON objects
    SQLType.ARRAY: list,
    SQLType.STRUCT: dict,
    SQLType.UNIQUE: str,
    SQLType.UUID: str,
    SQLType.GUID: str,
    SQLType.REAL: float,
    SQLType.TEXT: str,
}


def AsPydantic(
    schema: TableSchema,
    type_overrides: dict[SQLType, Any] | None = None,
    base_model: Type[BaseModel] = BaseModel,
    validators: dict[str, Any] | None = None,
) -> Type[BaseModel]:
    """
    Dynamically create a Pydantic model from a TableSchema.

    Args:
        schema: The TableSchema definition.
        type_overrides: Optional dictionary mapping SQLTypes to specific Python/Pydantic types.
                        This allows using Annotated types or custom classes for specific SQL types.
        base_model: Optional base class to inherit from (default: pydantic.BaseModel).
        validators: Optional dictionary of validators to attach to the model.
                    Keys are validator names, values are validator functions/methods.

    Returns:
        A Pydantic BaseModel class corresponding to the schema.
    """
    fields: dict[str, Any] = {}
    type_mapping = SQL_TYPE_MAPPING.copy()
    if type_overrides:
        type_mapping.update(type_overrides)

    for col in schema.columns:
        python_type = type_mapping.get(col.type, Any)
        field_def: tuple[Any, Any]

        # Handle modes
        if col.mode == "REPEATED":
            python_type = list[python_type]  # type: ignore
            # If mode is REPEATED, let's assume it's a list.
            field_def = (python_type, Field(default=None, description=col.description))
        elif col.mode == "NULLABLE":
            python_type = python_type | None
            field_def = (python_type, Field(default=None, description=col.description))
        else:  # REQUIRED
            field_def = (python_type, Field(..., description=col.description))

        fields[col.name] = field_def

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    return create_model(
        schema.name,
        __config__=model_config,
        __base__=base_model,
        __validators__=validators,
        **fields,
    )
