import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy import text

from database.connection import engine
from ml.mlflow_logger import log_anomaly_run


class AnomalyDetector:
    """Detect daily sales anomalies using IsolationForest."""

    feature_columns = ["order_count", "daily_revenue", "avg_order_value"]

    def prepare_features(self) -> pd.DataFrame:
        query = text(
            """
            SELECT
                DATE(order_purchase_timestamp) as date,
                COUNT(*) as order_count,
                SUM(oi.price) as daily_revenue,
                AVG(oi.price) as avg_order_value
            FROM olist_orders o
            JOIN olist_order_items oi ON o.order_id = oi.order_id
            WHERE order_purchase_timestamp IS NOT NULL
            GROUP BY DATE(order_purchase_timestamp)
            ORDER BY date
            """
        )

        df = pd.read_sql_query(query, engine)
        if df.empty:
            return df

        df["date"] = pd.to_datetime(df["date"])
        for column in self.feature_columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

        return df

    def detect(self, contamination=0.05) -> list[dict]:
        df = self.prepare_features()
        if df.empty:
            log_anomaly_run(
                precision=0.0,
                recall=0.0,
                contamination=contamination,
                n_anomalies=0,
            )
            return []

        features = df[self.feature_columns]
        model = IsolationForest(contamination=contamination, random_state=42)
        predictions = model.fit_predict(features)

        anomaly_df = df[predictions == -1].copy()
        z_scores = self._calculate_z_scores(features)

        anomalies = []
        for index, row in anomaly_df.iterrows():
            extreme_count = int((np.abs(z_scores.loc[index]) > 2).sum())
            severity = "high" if extreme_count > 2 else "medium"

            anomalies.append(
                {
                    "date": row["date"].date().isoformat(),
                    "order_count": int(row["order_count"]),
                    "daily_revenue": float(row["daily_revenue"]),
                    "avg_order_value": float(row["avg_order_value"]),
                    "severity": severity,
                }
            )

        log_anomaly_run(
            precision=0.0,
            recall=0.0,
            contamination=contamination,
            n_anomalies=len(anomalies),
        )

        return anomalies

    def _calculate_z_scores(self, features: pd.DataFrame) -> pd.DataFrame:
        std = features.std(ddof=0).replace(0, 1)
        return (features - features.mean()) / std
