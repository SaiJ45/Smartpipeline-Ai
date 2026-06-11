import mlflow
import mlflow.sklearn

from config.settings import get_settings


def _get_tracking_uri() -> str:
    try:
        return get_settings().MLFLOW_TRACKING_URI
    except Exception:
        return "http://localhost:5000"


mlflow.set_tracking_uri(_get_tracking_uri())


def log_forecast_run(
    mape: float,
    training_rows: int,
    forecast_horizon: int,
    model,
) -> str:
    mlflow.set_experiment("smartpipeline_forecast")

    with mlflow.start_run() as run:
        mlflow.log_params(
            {
                "training_rows": training_rows,
                "forecast_horizon": forecast_horizon,
                "model_type": "Prophet",
            }
        )
        mlflow.log_metric("mape", mape)
        mlflow.sklearn.log_model(model, "model")

        return run.info.run_id


def log_anomaly_run(
    precision: float,
    recall: float,
    contamination: float,
    n_anomalies: int,
) -> str:
    mlflow.set_experiment("smartpipeline_anomaly")

    with mlflow.start_run() as run:
        mlflow.log_metrics(
            {
                "precision": precision,
                "recall": recall,
                "contamination": contamination,
                "n_anomalies": n_anomalies,
            }
        )

        return run.info.run_id
