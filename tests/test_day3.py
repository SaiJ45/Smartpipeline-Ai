from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from api.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_data_summary_returns_data():
    response = client.get("/data/summary")

    assert response.status_code == 200
    assert "total_orders" in response.json()


def test_ask_endpoint_accepts_question():
    response = client.post("/ask", json={"question": "test"})

    assert response.status_code == 200
    assert "answer" in response.json()


def test_metrics_endpoint():
    response = client.get("/metrics")

    assert response.status_code == 200


def test_datasets_endpoint():
    response = client.get("/datasets")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
