from pathlib import Path
import sys

import pandas as pd
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from api.main import app
from ml.anomaly import AnomalyDetector
from ml.drift_monitor import check_forecast_drift
from ml.forecaster import SalesForecaster


def test_forecaster_prepares_data():
    forecaster = SalesForecaster()
    df = forecaster.prepare_data()

    assert isinstance(df, pd.DataFrame)
    assert "ds" in df.columns
    assert "y" in df.columns
    assert len(df) > 100


def test_anomaly_detector_prepares_features():
    detector = AnomalyDetector()
    df = detector.prepare_features()

    assert isinstance(df, pd.DataFrame)
    assert "order_count" in df.columns
    assert "daily_revenue" in df.columns
    assert len(df) > 100


def test_drift_monitor_detects_high_mape():
    result = check_forecast_drift(0.20, threshold=0.15)

    assert result["drift_detected"] is True


def test_drift_monitor_passes_low_mape():
    result = check_forecast_drift(0.10, threshold=0.15)

    assert result["drift_detected"] is False


def test_forecast_endpoint():
    client = TestClient(app)
    response = client.get("/forecast")

    assert response.status_code == 200
    assert "mape" in response.json() or "error" in response.json()
