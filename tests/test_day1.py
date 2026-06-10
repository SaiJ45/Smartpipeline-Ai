from pathlib import Path
import sys

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from core.chunk_template_engine import ChunkTemplateEngine
from core.schema_detector import SchemaDetector
from core.validator_factory import ValidatorFactory
from database.connection import test_connection as check_database_connection


def _column(schema, name):
    return next(col for col in schema["columns"] if col["name"] == name)


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


def test_schema_detector():
    csv_path = Path("data/raw/olist_orders_dataset.csv")
    df = pd.read_csv(csv_path)

    schema = SchemaDetector().detect(df, "olist_orders")

    assert _column(schema, "order_id")["detected_type"] == "ID"
    assert _column(schema, "order_purchase_timestamp")["detected_type"] == "DATE"
    assert _column(schema, "order_status")["detected_type"] == "CATEGORY"


def test_validator_factory_rejects_negative_price():
    factory = ValidatorFactory()
    validator = factory.build(_price_schema())

    is_valid, _ = factory.validate_row(validator, {"price": -10.0})

    assert is_valid is False


def test_validator_factory_accepts_valid_row():
    factory = ValidatorFactory()
    validator = factory.build(_price_schema())

    is_valid, _ = factory.validate_row(validator, {"price": 29.99})

    assert is_valid is True


def test_chunk_template_renders_missing_values():
    output = ChunkTemplateEngine().render(
        {"order_id": "abc123"},
        "Order {order_id} has status {missing_status}",
    )

    assert "N/A" in output


def test_database_connection():
    check_database_connection()
