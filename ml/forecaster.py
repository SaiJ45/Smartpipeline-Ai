from datetime import datetime

import numpy as np
import pandas as pd
from prophet import Prophet
from sqlalchemy import text

from database.connection import engine
from ml.mlflow_logger import log_forecast_run


class SalesForecaster:
    """Train Prophet sales forecasts from loaded Olist order data."""

    def prepare_data(self) -> pd.DataFrame:
        query = text(
            """
            SELECT
                DATE(o.order_purchase_timestamp) as ds,
                SUM(oi.price) as y
            FROM olist_orders o
            JOIN olist_order_items oi ON o.order_id = oi.order_id
            WHERE o.order_purchase_timestamp IS NOT NULL
            GROUP BY DATE(o.order_purchase_timestamp)
            ORDER BY ds
            """
        )

        df = pd.read_sql_query(query, engine)
        df["ds"] = pd.to_datetime(df["ds"])
        df["y"] = pd.to_numeric(df["y"], errors="coerce").fillna(0)
        return df[["ds", "y"]]

    def train_and_forecast(self, horizon_days=30) -> dict:
        df = self.prepare_data()
        if df.empty:
            return {
                "mape": 0.0,
                "forecast": [],
                "training_rows": 0,
                "last_trained": datetime.now().isoformat(),
            }

        holdout_days = min(30, max(len(df) - 1, 0))
        train_df = df.iloc[:-holdout_days] if holdout_days > 0 else df
        holdout_df = df.iloc[-holdout_days:] if holdout_days > 0 else pd.DataFrame()

        model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
        model.fit(train_df)

        if not holdout_df.empty:
            holdout_forecast = model.predict(holdout_df[["ds"]])
            mape = self.calculate_mape(
                holdout_df["y"].to_numpy(),
                holdout_forecast["yhat"].to_numpy(),
            )
        else:
            mape = 0.0

        final_model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
        final_model.fit(df)

        future = final_model.make_future_dataframe(periods=horizon_days)
        forecast_df = final_model.predict(future).tail(horizon_days)

        forecast = [
            {
                "date": row.ds.date().isoformat(),
                "predicted": float(row.yhat),
                "lower": float(row.yhat_lower),
                "upper": float(row.yhat_upper),
            }
            for row in forecast_df.itertuples()
        ]

        log_forecast_run(
            mape=mape,
            training_rows=len(df),
            forecast_horizon=horizon_days,
            model=final_model,
        )

        return {
            "mape": float(mape),
            "forecast": forecast,
            "training_rows": len(df),
            "last_trained": datetime.now().isoformat(),
        }

    def calculate_mape(self, actual, predicted) -> float:
        actual = np.asarray(actual, dtype=float)
        predicted = np.asarray(predicted, dtype=float)
        non_zero_mask = actual != 0

        if not np.any(non_zero_mask):
            return 0.0

        mape = np.mean(
            np.abs((actual[non_zero_mask] - predicted[non_zero_mask]) / actual[non_zero_mask])
        ) * 100
        return round(float(mape), 4)
