from fastapi import APIRouter

from ml.drift_monitor import check_forecast_drift
from ml.forecaster import SalesForecaster


router = APIRouter()


@router.get("")
def forecast():
    try:
        forecaster = SalesForecaster()
        result = forecaster.train_and_forecast(horizon_days=30)
        drift_result = check_forecast_drift(result["mape"])

        return {
            "status": "success",
            "mape": result["mape"],
            "training_rows": result["training_rows"],
            "forecast": result["forecast"],
            "drift_check": drift_result,
            "last_trained": result["last_trained"],
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@router.get("/config")
def forecast_config():
    return {
        "date_column": "order_purchase_timestamp",
        "target_column": "price",
        "horizon_days": 30,
        "model": "Prophet",
    }
