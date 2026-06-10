
from typing import Dict, Any, Tuple, Optional, Type
from datetime import datetime
from pydantic import create_model, BaseModel, field_validator, ValidationError
import pandas as pd


class ValidatorFactory:
    """Factory for creating dynamic Pydantic validators based on schema definitions."""

    NEGATIVE_ALLOWED_KEYWORDS = {
    "delta", "change", "temperature", "diff", "balance",
    "lat", "lng", "lon", "longitude", "latitude",
    "coord", "x", "y", "z", "delay", "discount"}

    def build(self, schema: Dict[str, Any]) -> Type[BaseModel]:
        """
        Build a dynamic Pydantic model from a schema dictionary.
        """
        if not isinstance(schema, dict) or "columns" not in schema:
            raise ValueError("Schema must be a dict with 'columns' key")

        columns = schema.get("columns", [])
        field_definitions = {}

        for col_info in columns:
            col_name = col_info.get("name")
            col_type = col_info.get("detected_type")

            if not col_name or not col_type:
                continue

            if col_type == "NUMERIC":
                field_definitions[col_name] = (Optional[float], None)
            elif col_type == "BOOLEAN":
                field_definitions[col_name] = (Optional[bool], None)
            else:
                # ID, DATE, CATEGORY, TEXT
                field_definitions[col_name] = (Optional[str], None)

        # Build model with just field definitions — no dynamic validators
        # Validation logic is handled in validate_row() directly
        model_class = create_model(
            "DynamicValidator",
            **field_definitions
        )

        # Attach schema metadata so validate_row can use it
        model_class.__schema_columns__ = {
            col["name"]: col["detected_type"]
            for col in columns
            if col.get("name") and col.get("detected_type")
        }

        return model_class

    def validate_row(
            self,
            model_class: Type[BaseModel],
            row: Dict[str, Any]
        ) -> Tuple[bool, str]:
        """
        Validate a single row. Only checks critical business rules.
        Type coercion is already handled by the loader.
        """
        schema_columns = getattr(model_class, "__schema_columns__", {})
        
        for col_name, col_type in schema_columns.items():
            value = row.get(col_name)

        # Only reject truly null ID fields
        if col_type == "ID":
            if value is None or str(value).strip() == "":
                return (False, f"null or empty ID: {col_name}")

        # Only reject negative NUMERIC values
        # Skip if column allows negatives
        elif col_type == "NUMERIC":
            if value is not None and value != "" and value == value:  # NaN check
                try:
                    num = float(value)
                    col_lower = col_name.lower()
                    allows_negative = any(
                        kw in col_lower
                        for kw in self.NEGATIVE_ALLOWED_KEYWORDS
                    )
                    if not allows_negative and num < 0:
                        return (False, f"negative value in {col_name}: {value}")
                except (TypeError, ValueError):
                    pass

        # Skip DATE validation — loader already coerced dates
        # Skip TEXT/CATEGORY — no rules needed

        return (True, "")