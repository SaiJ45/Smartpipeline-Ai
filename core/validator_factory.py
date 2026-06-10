from typing import Dict, Any, Tuple, Optional, Type
from datetime import datetime
from pydantic import create_model, BaseModel, field_validator, ValidationError


class ValidatorFactory:
    """Factory for creating dynamic Pydantic validators based on schema definitions."""
    
    # Keywords that allow negative values in NUMERIC fields
    NEGATIVE_ALLOWED_KEYWORDS = {"delta", "change", "temperature", "diff", "balance"}
    
    def build(self, schema: Dict[str, Any]) -> Type[BaseModel]:
        """
        Build a dynamic Pydantic model from a schema dictionary.
        
        The schema should have a 'columns' key containing a list of column definitions,
        each with at least 'name' and 'detected_type' keys.
        
        Column type rules:
        - ID: Optional[str], rejects None/empty string
        - DATE: Optional[str], rejects future dates
        - NUMERIC: Optional[float], rejects negative (unless column name contains delta/change/etc)
        - Others: Optional[str], no validation
        
        Args:
            schema: Schema dictionary with 'columns' list
            
        Returns:
            A dynamically created Pydantic BaseModel subclass
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
            
            # Define field with appropriate type and validator
            field_definitions[col_name] = self._create_field_definition(
                col_name, col_type
            )
        
        # Create the model dynamically
        model_class = create_model(
            "DynamicValidator",
            __base__=BaseModel,
            **field_definitions
        )
        
        return model_class
    
    def build(self, schema: Dict[str, Any]) -> Type[BaseModel]:
        """
        Build a dynamic Pydantic model from a schema dictionary.
        
        The schema should have a 'columns' key containing a list of column definitions,
        each with at least 'name' and 'detected_type' keys.
        
        Column type rules:
        - ID: Optional[str], rejects None/empty string
        - DATE: Optional[str], rejects future dates
        - NUMERIC: Optional[float], rejects negative (unless column name contains delta/change/etc)
        - Others: Optional[str], no validation
        
        Args:
            schema: Schema dictionary with 'columns' list
            
        Returns:
            A dynamically created Pydantic BaseModel subclass
        """
        if not isinstance(schema, dict) or "columns" not in schema:
            raise ValueError("Schema must be a dict with 'columns' key")
        
        columns = schema.get("columns", [])
        validators = {}
        field_definitions = {}
        
        for col_info in columns:
            col_name = col_info.get("name")
            col_type = col_info.get("detected_type")
            
            if not col_name or not col_type:
                continue
            
            # Define field type
            if col_type == "ID":
                field_definitions[col_name] = (Optional[str], None)
            elif col_type == "DATE":
                field_definitions[col_name] = (Optional[str], None)
            elif col_type == "NUMERIC":
                field_definitions[col_name] = (Optional[float], None)
            else:
                # BOOLEAN, CATEGORY, TEXT, and unknown types
                field_definitions[col_name] = (Optional[str], None)
            
            # Create validators for specific types
            validator_func = self._create_validator(col_name, col_type)
            if validator_func:
                validators[f"validate_{col_name}"] = field_validator(col_name)(validator_func)
        
        return create_model(
            "DynamicValidator",
            __base__=BaseModel,
            __validators__=validators,
            **field_definitions
        )
    
    def _create_validator(self, col_name: str, col_type: str):
        """
        Create a validator function for a column based on its type.
        
        Args:
            col_name: Name of the column
            col_type: Detected type (ID, DATE, NUMERIC, CATEGORY, TEXT, BOOLEAN)
            
        Returns:
            Validator function or None if no validation needed
        """
        if col_type == "ID":
            def validate_id(cls, value):
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    raise ValueError(f"ID field '{col_name}' cannot be None or empty")
                return value
            return validate_id
        
        elif col_type == "DATE":
            def validate_date(cls, value):
                if value is None:
                    return value
                try:
                    parsed_date = pd.to_datetime(value)
                    if parsed_date > datetime.now():
                        raise ValueError(
                            f"DATE field '{col_name}' cannot be in the future (got {value})"
                        )
                except Exception as e:
                    raise ValueError(f"DATE field '{col_name}' has invalid date: {e}")
                return value
            return validate_date
        
        elif col_type == "NUMERIC":
            # Check if column name allows negative values
            col_name_lower = col_name.lower()
            allows_negative = any(
                keyword in col_name_lower
                for keyword in self.NEGATIVE_ALLOWED_KEYWORDS
            )
            
            if not allows_negative:
                def validate_numeric(cls, value):
                    if value is not None and value < 0:
                        raise ValueError(
                            f"NUMERIC field '{col_name}' cannot be negative (got {value})"
                        )
                    return value
                return validate_numeric
        
        return None
    
    def validate_row(self, model_class: Type[BaseModel], row: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a single row of data using the provided model class.
        
        Args:
            model_class: Pydantic model class (from build())
            row: Dictionary containing row data
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
            - (True, '') if row is valid
            - (False, error_reason) if row is invalid
        """
        try:
            model_class(**row)
            return (True, "")
        except ValidationError as e:
            # Extract error messages from ValidationError
            errors = e.errors()
            error_messages = []
            for error in errors:
                field = error.get("loc", ("unknown",))[0]
                msg = error.get("msg", "Validation failed")
                error_messages.append(f"{field}: {msg}")
            
            error_reason = "; ".join(error_messages)
            return (False, error_reason)
        except Exception as e:
            return (False, f"Unexpected validation error: {str(e)}")


# Import pandas for datetime parsing (needed in validators)
try:
    import pandas as pd
except ImportError:
    pd = None
