from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd


class DataQualityReporter:
    """Generates HTML data quality reports for load results."""

    def generate(self, load_results: list, output_dir: str = "reports") -> str:
        """
        Generate a timestamped HTML data quality report.

        Args:
            load_results: List of table load result dictionaries.
            output_dir: Directory where the report should be saved.

        Returns:
            Path to the generated HTML report.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_path / f"quality_report_{timestamp}.html"

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Data Quality Report</title>
    <style>
        body {{
            margin: 0;
            background: #1a1a2e;
            color: #ffffff;
            font-family: Arial, sans-serif;
        }}
        main {{
            max-width: 1180px;
            margin: 0 auto;
            padding: 32px 24px;
        }}
        h1 {{
            margin: 0 0 24px;
            color: #ffffff;
        }}
        section {{
            background: #16213e;
            border-radius: 8px;
            margin-bottom: 24px;
            overflow: hidden;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.25);
        }}
        h2 {{
            margin: 0;
            padding: 16px 20px;
            background: #0f3460;
            color: #ffffff;
            font-size: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th,
        td {{
            padding: 12px 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.12);
            text-align: left;
        }}
        th {{
            color: #ffffff;
            background: rgba(15, 52, 96, 0.55);
        }}
        tr:last-child td {{
            border-bottom: 0;
        }}
        .highlight {{
            color: #e94560;
            font-weight: 700;
        }}
        .empty {{
            padding: 18px 20px;
            color: rgba(255, 255, 255, 0.78);
        }}
    </style>
</head>
<body>
    <main>
        <h1>Data Quality Report</h1>
        {self._render_load_summary(load_results)}
        {self._render_rejection_breakdown(load_results)}
        {self._render_null_analysis(load_results)}
        {self._render_data_range(load_results)}
    </main>
</body>
</html>
"""

        report_path.write_text(html, encoding="utf-8")
        return str(report_path)

    def _render_load_summary(self, load_results: list) -> str:
        rows = []

        for result in load_results:
            records_in = result.get("records_in", 0) or 0
            records_out = result.get("records_out", 0) or 0
            records_rejected = result.get("records_rejected", 0) or 0
            rejection_rate = (
                (records_rejected / records_in) * 100
                if records_in > 0
                else 0
            )

            rows.append(
                "<tr>"
                f"<td>{self._html(result.get('table_name', 'N/A'))}</td>"
                f"<td>{records_in:,}</td>"
                f"<td>{records_out:,}</td>"
                f"<td>{records_rejected:,}</td>"
                f"<td>{rejection_rate:.2f}%</td>"
                "</tr>"
            )

        return self._section(
            "Load Summary",
            self._table(
                ["Table Name", "Records In", "Records Out", "Records Rejected", "Rejection Rate"],
                rows,
            ),
        )

    def _render_rejection_breakdown(self, load_results: list) -> str:
        reasons = Counter()

        for result in load_results:
            for rejected_row in result.get("rejected_rows", []):
                reason = rejected_row.get("rejection_reason", "Unknown")
                reasons[reason] += 1

        rows = [
            f"<tr><td>{self._html(reason)}</td><td>{count:,}</td></tr>"
            for reason, count in reasons.most_common(5)
        ]

        return self._section(
            "Rejection Breakdown",
            self._table(["Rejection Reason", "Count"], rows),
        )

    def _render_null_analysis(self, load_results: list) -> str:
        rows = []

        for result in load_results:
            table_name = result.get("table_name", "N/A")
            df_sample = result.get("df_sample")

            if not isinstance(df_sample, pd.DataFrame) or df_sample.empty:
                continue

            null_percentages = df_sample.isnull().mean() * 100
            for column_name, null_pct in null_percentages.items():
                if null_pct > 0:
                    pct_value = f"{null_pct:.2f}%"
                    pct_html = (
                        f'<span class="highlight">{pct_value}</span>'
                        if null_pct > 5
                        else pct_value
                    )
                    rows.append(
                        "<tr>"
                        f"<td>{self._html(table_name)}</td>"
                        f"<td>{self._html(column_name)}</td>"
                        f"<td>{pct_html}</td>"
                        "</tr>"
                    )

        return self._section(
            "Null Analysis",
            self._table(["Table Name", "Column", "Null Percentage"], rows),
        )

    def _render_data_range(self, load_results: list) -> str:
        rows = []

        for result in load_results:
            table_name = result.get("table_name", "N/A")
            df_sample = result.get("df_sample")

            if not isinstance(df_sample, pd.DataFrame) or df_sample.empty:
                continue

            min_date, max_date = self._get_date_range(df_sample)

            numeric_df = df_sample.select_dtypes(include="number")
            for column_name in numeric_df.columns:
                column = numeric_df[column_name].dropna()
                if column.empty:
                    continue

                rows.append(
                    "<tr>"
                    f"<td>{self._html(table_name)}</td>"
                    f"<td>{self._html(column_name)}</td>"
                    f"<td>{self._html(min_date)}</td>"
                    f"<td>{self._html(max_date)}</td>"
                    f"<td>{self._format_value(column.min())}</td>"
                    f"<td>{self._format_value(column.max())}</td>"
                    "</tr>"
                )

        return self._section(
            "Data Range",
            self._table(["Table Name", "Numeric Column", "Min Date", "Max Date", "Min Value", "Max Value"], rows),
        )

    def _get_date_range(self, df: pd.DataFrame) -> tuple[str, str]:
        dates = []

        for column_name in df.columns:
            series = df[column_name]
            if pd.api.types.is_datetime64_any_dtype(series):
                parsed = series
            elif "date" in str(column_name).lower() or "timestamp" in str(column_name).lower():
                parsed = pd.to_datetime(series, errors="coerce")
            else:
                continue

            parsed = parsed.dropna()
            if not parsed.empty:
                dates.append((parsed.min(), parsed.max()))

        if not dates:
            return "N/A", "N/A"

        min_date = min(date_range[0] for date_range in dates)
        max_date = max(date_range[1] for date_range in dates)
        return str(min_date), str(max_date)

    def _section(self, title: str, body: str) -> str:
        return f"<section><h2>{self._html(title)}</h2>{body}</section>"

    def _table(self, headers: list[str], rows: list[str]) -> str:
        if not rows:
            return '<div class="empty">No records to display.</div>'

        header_html = "".join(f"<th>{self._html(header)}</th>" for header in headers)
        row_html = "".join(rows)
        return f"<table><thead><tr>{header_html}</tr></thead><tbody>{row_html}</tbody></table>"

    def _format_value(self, value: Any) -> str:
        if pd.isna(value):
            return "N/A"

        if isinstance(value, float):
            return f"{value:.2f}"

        return self._html(value)

    def _html(self, value: Any) -> str:
        if value is None:
            return "N/A"

        return escape(str(value))
