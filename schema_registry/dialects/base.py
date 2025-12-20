from abc import ABC, abstractmethod
from typing import Dict
from schema_registry.sql_types import SQLType

class BaseDialect(ABC):
    """Abstract base class for SQL dialects."""

    @abstractmethod
    def get_type_map(self) -> Dict[SQLType, str]:
        """Returns the mapping from SQLType to the engine's data type string."""
        pass

    @abstractmethod
    def get_pandas_dtype_map(self) -> Dict[SQLType, str]:
        """Returns the mapping from SQLType to pandas dtype."""
        pass
