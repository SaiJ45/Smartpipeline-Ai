import re
from typing import Dict, List, Any


class ChunkTemplateEngine:
    """Template engine for rendering text chunks with row data."""
    
    def render(self, row: Dict[str, Any], template: str) -> str:
        """
        Render a template by replacing {column_name} placeholders with row values.
        
        Rules:
        - Missing keys in row: replaced with 'N/A'
        - None values: replaced with 'N/A'
        - Float values: rounded to 2 decimal places
        - String values > 300 chars: truncated to 297 chars with '...' appended
        - Final output: extra whitespace stripped
        
        Args:
            row: Dictionary containing column data
            template: Template string with {column_name} placeholders
            
        Returns:
            Rendered template string with all placeholders filled
        """
        if not isinstance(template, str):
            return "N/A"
        
        # Find all placeholders {column_name}
        placeholders = re.findall(r"\{([^}]+)\}", template)
        
        result = template
        
        for placeholder in placeholders:
            # Get value from row, default to None
            value = row.get(placeholder, None)
            
            # Format the value
            formatted_value = self._format_value(value)
            
            # Replace placeholder with formatted value
            result = result.replace(f"{{{placeholder}}}", formatted_value)
        
        # Strip extra whitespace
        result = re.sub(r"\s+", " ", result).strip()
        
        return result
    
    def build_generic_chunk(self, row: Dict[str, Any], important_columns: List[str]) -> str:
        """
        Build a chunk by joining important columns without a template.
        
        Formats each column as 'column_name: value' pairs separated by ' . '
        
        Follows same rules as render():
        - Missing keys: 'N/A'
        - None values: 'N/A'
        - Float values: rounded to 2 decimals
        - Long strings: truncated to 297 chars with '...'
        
        Args:
            row: Dictionary containing column data
            important_columns: List of column names to include in chunk
            
        Returns:
            Formatted chunk string with column: value pairs
        """
        if not important_columns:
            return "N/A"
        
        chunk_parts = []
        
        for col_name in important_columns:
            # Get value from row, default to None
            value = row.get(col_name, None)
            
            # Format the value
            formatted_value = self._format_value(value)
            
            # Create 'column_name: value' pair
            chunk_part = f"{col_name}: {formatted_value}"
            chunk_parts.append(chunk_part)
        
        # Join with ' . '
        result = " . ".join(chunk_parts)
        
        # Strip extra whitespace
        result = re.sub(r"\s+", " ", result).strip()
        
        return result
    
    def _format_value(self, value: Any) -> str:
        """
        Format a value according to type-specific rules.
        
        Args:
            value: Value to format
            
        Returns:
            Formatted string value
        """
        # None values -> 'N/A'
        if value is None:
            return "N/A"
        
        # Float values -> round to 2 decimals
        if isinstance(value, float):
            return str(round(value, 2))
        
        # Convert to string
        str_value = str(value)
        
        # Long strings -> truncate to 297 chars and add '...'
        if len(str_value) > 300:
            return str_value[:297] + "..."
        
        return str_value
