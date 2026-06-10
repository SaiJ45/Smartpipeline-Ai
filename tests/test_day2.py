from pathlib import Path
import sys

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from core.schema_detector import SchemaDetector
from core.validator_factory import ValidatorFactory
from ingestion.quality_report import DataQualityReporter
from ingestion.transformer import DataTransformer


def _build_validator(schema):
    return ValidatorFactory().build(schema)


def _price_schema():
    return {
        "dataset_name": "mock_dataset",
        "columns": [
            {
                "name": "price",
                "detected_type": "NUMERIC",
            }
        ],
    }


def _mock_load_results():
    return [
        {
            "table_name": "order_items",
            "records_in": 3,
            "records_out": 2,
            "records_rejected": 1,
            "rejected_rows": [
                {
                    "row_index": 2,
                    "rejection_reason": "negative value",
                }
            ],
            "df_sample": pd.DataFrame(
                {
                    "shipping_limit_date": ["2024-01-01", "2024-01-02", None],
                    "price": [10.0, 29.99, None],
                }
            ),
        }
    ]


def test_transformer_accepts_valid_rows():
    df = pd.read_csv("data/raw/olist_order_items_dataset.csv", nrows=50)
    schema = SchemaDetector().detect(df, "order_items")
    validator_model = _build_validator(schema)

    valid_df, rejected = DataTransformer().transform(
        df,
        "order_items",
        schema,
        validator_model,
    )

    assert len(valid_df) > 0
    assert len(valid_df) + len(rejected) == 50


def test_transformer_rejects_negative_price():
    df = pd.DataFrame([{"price": -5.0}])
    schema = _price_schema()
    validator_model = _build_validator(schema)

    _, rejected_rows = DataTransformer().transform(
        df,
        "order_items",
        schema,
        validator_model,
    )

    assert any(row["row_data"]["price"] == -5.0 for row in rejected_rows)


def test_quality_report_generates_file(tmp_path):
    report_path = DataQualityReporter().generate(
        _mock_load_results(),
        output_dir=str(tmp_path),
    )

    assert Path(report_path).exists()
    assert report_path.endswith(".html")


def test_quality_report_contains_sections(tmp_path):
    report_path = DataQualityReporter().generate(
        _mock_load_results(),
        output_dir=str(tmp_path),
    )
    content = Path(report_path).read_text(encoding="utf-8")

    assert "Load Summary" in content
    assert "Null Analysis" in content
    assert "Rejection" in content


def test_scheduler_function_runs(monkeypatch):
    import scheduler.pipeline_scheduler as pipeline_scheduler
    from scheduler.pipeline_scheduler import run_pipeline

    class MockLoader:
        def load_all(self, config):
            return _mock_load_results()

    class MockReporter:
        def generate(self, load_results):
            return "reports/mock_quality_report.html"

    monkeypatch.setattr(
        pipeline_scheduler,
        "get_active_dataset",
        lambda: {"name": "mock_dataset"},
    )
    monkeypatch.setattr(pipeline_scheduler, "DataLoader", MockLoader)
    monkeypatch.setattr(pipeline_scheduler, "DataQualityReporter", MockReporter)

    run_pipeline()
