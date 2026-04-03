import duckdb
import pandas as pd

def analyze():
    # Connect to DuckDB
    conn = duckdb.connect('whale_tracker.db')
    
    # Check total count
    count = conn.execute("SELECT COUNT(*) FROM transfers").fetchone()[0]
    print(f"Total Transactions Captured: {count}")
    
    if count == 0:
        print("No transactions captured yet. Please let the ingestion script run for a bit.")
        return

    # Load into Pandas for more analysis
    df = conn.execute("SELECT * FROM transfers").df()
    
    print("\n--- Basic Statistics ---")
    print(f"Max Transaction: ${df['amount'].max():,.2f}")
    print(f"Mean Transaction: ${df['amount'].mean():,.2f}")
    
    # Identify top tokens
    print("\n--- Transactions by Token ---")
    print(df['token_name'].value_counts())

    # Show last 5 transactions
    print("\n--- Most Recent Transfers ---")
    print(df.tail(5))

if __name__ == "__main__":
    analyze()
