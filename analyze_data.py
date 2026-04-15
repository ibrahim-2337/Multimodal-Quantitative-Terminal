import pandas as pd
from database import get_db_connection

def analyze():
    conn = get_db_connection()
    
    count = conn.execute("SELECT COUNT(*) FROM transfers").fetchone()[0]
    print(f"Total Transactions Captured: {count}")
    
    if count == 0:
        print("No transactions captured yet. Please let the ingestion script run for a bit.")
        conn.close()
        return

    df = pd.read_sql_query("SELECT * FROM transfers", conn)
    conn.close()
    
    print("\n--- Basic Statistics ---")
    print(f"Max Transaction: ${df['amount_usd'].max():,.2f}")
    print(f"Mean Transaction: ${df['amount_usd'].mean():,.2f}")
    
    print("\n--- Transactions by Token ---")
    print(df['token_name'].value_counts())

    print("\n--- Most Recent Transfers ---")
    print(df.tail(5))

if __name__ == "__main__":
    analyze()
