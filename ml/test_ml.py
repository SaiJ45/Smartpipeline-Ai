from ml.forecaster import SalesForecaster
from ml.anomaly import AnomalyDetector

print("Testing forecaster...")
forecaster = SalesForecaster()
df = forecaster.prepare_data()
print(f"Training data shape: {df.shape}")
print(f"Date range: {df['ds'].min()} to {df['ds'].max()}")
print(f"Revenue range: R${df['y'].min():.2f} to R${df['y'].max():.2f}")

print("\nTesting anomaly detector...")
detector = AnomalyDetector()
features = detector.prepare_features()
print(f"Feature shape: {features.shape}")
print(f"Columns: {list(features.columns)}")