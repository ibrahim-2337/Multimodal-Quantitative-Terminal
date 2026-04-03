import duckdb
import pandas as pd
from sklearn.ensemble import IsolationForest
import numpy as np

def detect_anomalies():
    # 1. Load Data
    conn = duckdb.connect('whale_tracker.db')
    df = conn.execute("SELECT * FROM transfers").df()
    
    if len(df) < 100:
        print("Not enough data to train the model. Capture more transactions first.")
        return

    print(f"Analyzing {len(df)} transactions for anomalies...")

    # 2. Feature Engineering
    # For now, let's focus on the amount as the primary feature.
    # We'll reshape it for scikit-learn.
    X = df[['amount']].values

    # 3. Train Isolation Forest
    # contamination is the expected % of anomalies in the dataset.
    # Let's start with 1% (0.01) as whales are rare.
    model = IsolationForest(contamination=0.01, random_state=42)
    model.fit(X)

    # 4. Predict
    # -1 = anomaly, 1 = normal
    df['anomaly_score'] = model.decision_function(X)
    df['is_anomaly'] = model.predict(X)

    # 5. Output Results
    anomalies = df[df['is_anomaly'] == -1].sort_values(by='amount', ascending=False)
    
    print(f"\n--- Detected {len(anomalies)} Anomalies ---")
    if not anomalies.empty:
        print(anomalies[['token_name', 'amount', 'timestamp']].head(10))
    else:
        print("No anomalies detected with current parameters.")

    # 6. (Optional) Save the results back to DuckDB for future reference
    # conn.execute("CREATE TABLE IF NOT EXISTS anomalies AS SELECT * FROM df WHERE is_anomaly = -1")

if __name__ == "__main__":
    detect_anomalies()
