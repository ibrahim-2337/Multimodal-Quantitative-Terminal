import sqlite3
import logging

logger = logging.getLogger("Database")

def get_db_connection(db_name='whale_tracker.db'):
    conn = sqlite3.connect(db_name, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db(db_name='whale_tracker.db'):
    try:
        with get_db_connection(db_name) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transfers (
                    token_name TEXT, 
                    sender TEXT, 
                    receiver TEXT, 
                    direction TEXT, 
                    amount_usd REAL, 
                    sentiment TEXT, 
                    tx_hash TEXT, 
                    timestamp TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_signals (
                    token TEXT, 
                    entry_price REAL, 
                    signal TEXT, 
                    confidence INTEGER, 
                    rsi REAL, 
                    whale_context TEXT, 
                    timestamp TEXT, 
                    price_15m REAL, 
                    status TEXT DEFAULT 'PENDING'
                )
            """)
            conn.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
