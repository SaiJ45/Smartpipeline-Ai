import pandas as pd

from core.validator_factory import ValidatorFactory


class DataTransformer:
    """Transforms DataFrames by validating rows and separating rejects."""

    def __init__(self) -> None:
        self.validator_factory = ValidatorFactory()

    def transform(
        self,
        df: pd.DataFrame,
        table_name: str,
        schema: dict,
        validator_model,
    ) -> tuple[pd.DataFrame, list]:
        """
        Validate rows and split them into valid and rejected collections.

        Args:
            df: Source DataFrame to transform.
            table_name: Name of the table being transformed.
            schema: Schema dictionary for the table.
            validator_model: Pydantic model created by ValidatorFactory.

        Returns:
            Tuple of (valid_rows_df, rejected_rows).
        """
        df_copy = df.copy()
        valid_rows = []
        rejected_rows = []

        for row_index, row in df_copy.iterrows():
            row_data = row.to_dict()
            is_valid, rejection_reason = self.validator_factory.validate_row(
                validator_model,
                row_data,
            )

            if is_valid:
                valid_rows.append(row_data)
            else:
                rejected_rows.append(
                    {
                        "row_index": row_index,
                        "row_data": row_data,
                        "rejection_reason": rejection_reason,
                    }
                )

        return pd.DataFrame(valid_rows), rejected_rows

    def get_rejection_summary(self, rejected_rows: list) -> dict:
        """
        Count rejected rows by rejection reason.

        Args:
            rejected_rows: List of rejected row dictionaries from transform().

        Returns:
            Dict mapping rejection reason to rejection count.
        """
        summary = {}

        for rejected_row in rejected_rows:
            reason = rejected_row.get("rejection_reason", "Unknown")
            summary[reason] = summary.get(reason, 0) + 1

        return summary
