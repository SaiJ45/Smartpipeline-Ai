import json
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import numpy as np


class SchemaDetector:
    """Detects and analyzes schema information for DataFrames."""
    
    def detect(self, df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
        """
        Detect schema of a DataFrame by classifying each column.
        
        Classification rules (in order):
        - ID: column name ends with '_id' and unique_ratio > 0.8
        - DATE: pd.to_datetime succeeds on >80% of non-null sample values
        - BOOLEAN: unique non-null values <= 2
        - NUMERIC: dtype is int64 or float64
        - CATEGORY: dtype is object and unique values < 50
        - TEXT: dtype is object and unique values >= 50
        
        Args:
            df: Input DataFrame to analyze
            dataset_name: Name of the dataset
            
        Returns:
            Dictionary with keys:
                - dataset_name: Name of the dataset
                - columns: List of column info dicts with keys:
                    - name: Column name
                    - detected_type: Detected type (ID, DATE, NUMERIC, BOOLEAN, CATEGORY, TEXT)
                    - null_count: Number of null values
                    - null_pct: Percentage of null values
                    - unique_count: Number of unique values
                    - sample_values: Up to 5 sample non-null values
        """
        columns_info = []
        
        for col in df.columns:
            col_data = df[col]
            
            # Calculate basic statistics
            null_count = col_data.isnull().sum()
            total_rows = len(df)
            null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0
            unique_count = col_data.nunique()
            
            # Get sample values (up to 5 non-null values)
            sample_values = col_data.dropna().unique()[:5].tolist()
            
            # Classify column type
            detected_type = self._classify_column(col, col_data)
            
            columns_info.append({
                "name": col,
                "detected_type": detected_type,
                "null_count": int(null_count),
                "null_pct": null_pct,
                "unique_count": int(unique_count),
                "sample_values": sample_values
            })
        
        return {
            "dataset_name": dataset_name,
            "columns": columns_info
        }
    
    def _classify_column(self, col_name: str, col_data: pd.Series) -> str:
        """
        Classify a column based on its characteristics.
        
        Args:
            col_name: Name of the column
            col_data: Series containing the column data
            
        Returns:
            Classification string (ID, DATE, NUMERIC, BOOLEAN, CATEGORY, TEXT)
        """
        # Rule 1: ID - column name ends with '_id' and high uniqueness
        if col_name.lower().endswith("_id"):
            total_rows = len(col_data)
            unique_count = col_data.nunique()
            if total_rows > 0 and (unique_count / total_rows) > 0.8:
                return "ID"
        
        # Rule 2: DATE - pd.to_datetime succeeds on >80% of non-null values
        if self._is_datetime_type(col_data):
            return "DATE"
        
        # Rule 3: BOOLEAN - <= 2 unique non-null values
        unique_non_null = col_data.dropna().nunique()
        if unique_non_null <= 2:
            return "BOOLEAN"
        
        # Rule 4: NUMERIC - int64 or float64 dtype
        if col_data.dtype in ["int64", "int32", "int16", "int8", "float64", "float32"]:
            return "NUMERIC"
        
        # Rule 5 & 6: CATEGORY vs TEXT - for object dtype
        if col_data.dtype == "object":
            unique_count = col_data.nunique()
            if unique_count < 50:
                return "CATEGORY"
            else:
                return "TEXT"
        
        # Default fallback
        return "TEXT"
    
    def _is_datetime_type(self, col_data: pd.Series) -> bool:
        """
        Check if a column contains datetime values.
        
        Tries to parse values with pd.to_datetime and succeeds if
        >80% of non-null sample values are successfully parsed.
        
        Args:
            col_data: Series to check
            
        Returns:
            True if column likely contains dates, False otherwise
        """
        non_null_data = col_data.dropna()
        
        if len(non_null_data) == 0:
            return False
        
        # Sample up to 100 values for performance
        sample_size = min(100, len(non_null_data))
        sample = non_null_data.sample(n=sample_size, random_state=42)
        
        success_count = 0
        for value in sample:
            try:
                pd.to_datetime(value)
                success_count += 1
            except (ValueError, TypeError, pd.errors.ParserError):
                pass
        
        success_ratio = success_count / sample_size if sample_size > 0 else 0
        return success_ratio > 0.8
    
    def save_schema(self, schema: Dict[str, Any], dataset_name: str) -> None:
        """
        Save schema to JSON file in config/schema_registry/.
        
        Args:
            schema: Schema dictionary from detect() method
            dataset_name: Name of the dataset (used for filename)
            
        Raises:
            IOError: If unable to write the schema file
        """
        schema_registry_dir = Path(__file__).parent.parent / "config" / "schema_registry"
        
        # Create directory if it doesn't exist
        schema_registry_dir.mkdir(parents=True, exist_ok=True)
        
        # Construct filename
        schema_file = schema_registry_dir / f"{dataset_name}_schema.json"
        
        try:
            with open(schema_file, "w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2, default=str)
        except IOError as e:
            raise IOError(f"Failed to save schema to {schema_file}: {e}")
