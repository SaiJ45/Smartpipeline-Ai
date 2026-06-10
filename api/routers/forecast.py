from fastapi import APIRouter


router = APIRouter()


@router.get("")
def forecast():
    return {
        "status": "pending",
        "message": "Forecasting model will be available after Day 4",
        "data": [],
    }


@router.get("/config")
def forecast_config():
    return {
        "date_column": "order_purchase_timestamp",
        "target_column": "price",
        "horizon_days": 30,
        "model": "Prophet",
    }
