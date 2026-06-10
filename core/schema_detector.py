import pandas as pd
import json
import os
from pathlib import Path
import logging


logger = logging.getLogger(__name__)


class SchemaDetector:
    """Detects column types from any DataFrame automatically."""

    def detect(self, df: pd.DataFrame, dataset_name: str) -> dict:
        """
        Detect schema from a DataFrame.

        Returns a dict with keys:
            dataset_name, columns (list of dicts with
            name, detected_type, null_count, null_pct,
            unique_count, sample_values)
        """
        columns = []

        for col_name in df.columns:
            series = df[col_name]
            detected_type = self._classify_column(series, col_name)

            null_count = int(series.isna().sum())
            total = max(len(series), 1)
            null_pct = round(null_count / total * 100, 2)
            unique_count = int(series.nunique())
            sample_values = series.dropna().head(3).tolist()

            columns.append({
                "name": col_name,
                "detected_type": detected_type,
                "null_count": null_count,
                "null_pct": null_pct,
                "unique_count": unique_count,
                "sample_values": [str(v) for v in sample_values],
            })

        schema = {
            "dataset_name": dataset_name,
            "columns": columns,
        }

        try:
            self.save_schema(schema, dataset_name)
        except OSError as e:
            logger.warning(f"Could not save schema for {dataset_name}: {e}")

        return schema

    def _classify_column(self, series: pd.Series, col_name: str) -> str:
        """Classify a single column into a type."""

        col_lower = col_name.lower()

        # Step 1 — ID by name pattern
        if col_lower.endswith('_id') or col_lower == 'id':
            if series.nunique() / max(len(series), 1) > 0.8:
                return 'ID'

        # Step 2 — NUMERIC first (before DATE)
        if pd.api.types.is_numeric_dtype(series):
            return 'NUMERIC'

        # Step 3 — BOOLEAN
        non_null = series.dropna()
        if non_null.nunique() <= 2:
            return 'BOOLEAN'

        # Step 4 — DATE only if name has date keywords AND dtype is object
        date_keywords = ['date', 'time', 'timestamp', 'at', 'day', 'month', 'year']
        has_date_keyword = any(kw in col_lower for kw in date_keywords)

        if has_date_keyword and series.dtype == object:
            sample = non_null.head(50)
            try:
                parsed = pd.to_datetime(sample, errors='coerce', format='mixed')
                success_rate = parsed.notna().sum() / max(len(sample), 1)
                if success_rate > 0.8:
                    return 'DATE'
            except Exception:
                pass

        # Step 5 — CATEGORY vs TEXT
        if series.dtype == object:
            if series.nunique() < 50:
                return 'CATEGORY'
            return 'TEXT'

        return 'TEXT'

    def save_schema(self, schema: dict, dataset_name: str) -> None:
        """Save schema to config/schema_registry/{dataset_name}_schema.json."""
        registry_dir = Path("config/schema_registry")
        registry_dir.mkdir(parents=True, exist_ok=True)

        output_path = registry_dir / f"{dataset_name}_schema.json"
        with open(output_path, "w") as f:
            json.dump(schema, f, indent=2)
