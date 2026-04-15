import pandas as pd
from sklearn.ensemble import IsolationForest
from database import get_db_connection

def detect_anomalies():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transfers", conn)
    conn.close()
    
    if len(df) < 100:
        print("Not enough data to train the model. Capture more transactions first.")
        return

    print(f"Analyzing {len(df)} transactions for anomalies...")

    X = df[['amount_usd']].values

    model = IsolationForest(contamination=0.01, random_state=42)
    model.fit(X)

    df['anomaly_score'] = model.decision_function(X)
    df['is_anomaly'] = model.predict(X)

    anomalies = df[df['is_anomaly'] == -1].sort_values(by='amount_usd', ascending=False)
    
    print(f"\n--- Detected {len(anomalies)} Anomalies ---")
    if not anomalies.empty:
        print(anomalies[['token_name', 'amount_usd', 'timestamp']].head(10))
    else:
        print("No anomalies detected with current parameters.")

if __name__ == "__main__":
    detect_anomalies()
