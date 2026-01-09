import pytest
from datetime import datetime
from typing import Annotated, Any
from pydantic import BaseModel, BeforeValidator, Field, field_validator, ValidationError

from schema_registry.schema_loader import TableSchema, ColumnSchema
from schema_registry.to_pydantic import AsPydantic
from schema_registry.sql_types import SQLType


@pytest.fixture
def sample_schema():
    return TableSchema(
        name="test_table",
        columns=[
            ColumnSchema(name="id", type=SQLType.INT64, mode="REQUIRED"),
            ColumnSchema(name="name", type=SQLType.STRING, mode="NULLABLE"),
            ColumnSchema(name="tags", type=SQLType.STRING, mode="REPEATED"),
        ],
    )


def test_basic_model_generation(sample_schema):
    """Test that a basic model is generated correctly."""
    Model = AsPydantic(sample_schema)

    assert issubclass(Model, BaseModel)
    assert "id" in Model.model_fields
    assert "name" in Model.model_fields
    assert "tags" in Model.model_fields

    # Valid data
    data = {"id": 1, "name": "test", "tags": ["a", "b"]}
    obj = Model(**data)
    assert obj.id == 1
    assert obj.name == "test"
    assert obj.tags == ["a", "b"]

    # Missing required
    with pytest.raises(ValidationError):
        Model(name="test")

    # Wrong type
    with pytest.raises(ValidationError):
        Model(id="not an int")


def test_schema_types_mapping():
    """Test various SQL types mapping."""
    schema = TableSchema(
        name="types_table",
        columns=[
            ColumnSchema(name="f_bool", type=SQLType.BOOLEAN, mode="REQUIRED"),
            ColumnSchema(name="f_ts", type=SQLType.TIMESTAMP, mode="REQUIRED"),
            ColumnSchema(name="f_json", type=SQLType.JSON, mode="REQUIRED"),
        ],
    )
    Model = AsPydantic(schema)

    fields = Model.model_fields
    assert fields["f_bool"].annotation == bool
    assert fields["f_ts"].annotation == datetime
    assert fields["f_json"].annotation == dict


def test_custom_base_model(sample_schema):
    """Test inheriting from a custom base model."""

    class CustomBase(BaseModel):
        def custom_method(self):
            return "exists"

    Model = AsPydantic(sample_schema, base_model=CustomBase)
    obj = Model(id=1, name="foo", tags=[])

    assert isinstance(obj, CustomBase)
    assert obj.custom_method() == "exists"


def test_type_overrides(sample_schema):
    """Test overriding SQL to Python type mapping."""

    def to_upper(v: str) -> str:
        return v.upper()

    UppercaseStr = Annotated[str, BeforeValidator(to_upper)]

    Model = AsPydantic(sample_schema, type_overrides={SQLType.STRING: UppercaseStr})

    obj = Model(id=1, name="lower", tags=["val"])
    assert obj.name == "LOWER"
    # Note: REPEATED fields (List[T]) might need careful handling if the override is for T.
    # The current implementation wraps the mapped type in List[...].
    # So List[UppercaseStr] should work if Pydantic handles List[Annotated[...]] correctly.
    assert obj.tags == ["VAL"]


def test_validator_injection(sample_schema):
    """Test injecting custom validators."""

    @field_validator("id")
    def validate_positive(cls, v):
        if v < 0:
            raise ValueError("Must be positive")
        return v

    Model = AsPydantic(
        sample_schema, validators={"validate_positive": validate_positive}
    )

    # Valid
    Model(id=10, name="ok", tags=[])

    # Invalid
    with pytest.raises(ValidationError) as exc:
        Model(id=-5, name="bad", tags=[])
    assert "Must be positive" in str(exc.value)
