from database.connection import SessionLocal
from database.models import Dataset, SystemMetric


def check_forecast_drift(current_mape: float, threshold: float = 0.15) -> dict:
    drift_detected = current_mape > threshold

    if drift_detected:
        db = SessionLocal()
        try:
            dataset = db.query(Dataset).filter(Dataset.name == "ml_drift").first()
            if dataset is None:
                dataset = Dataset(
                    name="ml_drift",
                    display_name="ML Drift Metrics",
                    source_type="ml",
                )
                db.add(dataset)
                db.commit()
                db.refresh(dataset)

            db.add(
                SystemMetric(
                    dataset_id=dataset.id,
                    category="ml_drift",
                    metric_name="mape_alert",
                    metric_value=current_mape,
                )
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        return {
            "drift_detected": True,
            "current_mape": current_mape,
            "threshold": threshold,
            "message": "Model drift detected - consider retraining",
        }

    return {
        "drift_detected": False,
        "current_mape": current_mape,
        "threshold": threshold,
        "message": "Model performance within acceptable range",
    }
