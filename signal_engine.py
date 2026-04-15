import ccxt
import pandas as pd
import pandas_ta as ta
import time
import datetime
import traceback
import logging
from config import TOKENS
from database import init_db, get_db_connection

logger = logging.getLogger("SignalEngine")
EXCHANGE = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

def fetch_ohlcv(symbol):
    try:
        bars = EXCHANGE.fetch_ohlcv(symbol, timeframe='1m', limit=100)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        logger.error(f"Error fetching OHLCV for {symbol}: {e}")
        return None

def calculate_indicators(df):
    try:
        df['RSI'] = ta.rsi(df['close'], length=14)
        bbands = ta.bbands(df['close'], length=20, std=2)
        df = pd.concat([df, bbands], axis=1)
        return df
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return df

def get_recent_whale_signal(token_name, db_conn):
    try:
        fifteen_ago = (datetime.datetime.now() - datetime.timedelta(minutes=15)).isoformat()
        query = "SELECT sentiment FROM transfers WHERE token_name = ? AND timestamp > ? ORDER BY timestamp DESC LIMIT 1"
        res = db_conn.execute(query, (token_name, fifteen_ago)).fetchone()
        return res
    except Exception as e:
        logger.error(f"Error fetching whale signal for {token_name}: {e}")
        return None

def update_backtests(db_conn):
    try:
        fifteen_ago = (datetime.datetime.now() - datetime.timedelta(minutes=15)).isoformat()
        pending = db_conn.execute(
            "SELECT rowid, token, signal, entry_price FROM ai_signals WHERE status = 'PENDING' AND timestamp < ?", 
            (fifteen_ago,)
        ).fetchall()
        
        for rowid, token, signal, entry_price in pending:
            symbol = TOKENS.get(token)[3] if token in TOKENS else None
            if not symbol:
                continue

            df = fetch_ohlcv(symbol)
            if df is not None and not df.empty:
                curr = df.iloc[-1]['close']
                roi = ((curr - entry_price) / entry_price) * 100
                if signal == "BUY": 
                    status = "WIN" if roi > 0.1 else "LOSS"
                else: 
                    status = "WIN" if roi < -0.1 else "LOSS"
                
                with db_conn:
                    db_conn.execute("UPDATE ai_signals SET price_15m = ?, status = ? WHERE rowid = ?", (curr, status, rowid))
                logger.info(f"Updated backtest for {token}: {status} (ROI: {roi:.2f}%)")
    except Exception as e:
        logger.error(f"Error updating backtests: {e}\n{traceback.format_exc()}")

def generate_signal(db_conn):
    logger.info(f"--- 20-Token Multi-Scan: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    signals = []
    
    for token, (_, _, _, symbol) in TOKENS.items():
        try:
            df = fetch_ohlcv(symbol)
            if df is None or len(df) < 50: 
                continue
            
            df = calculate_indicators(df)
            if 'RSI' not in df.columns or 'BBL_20_2.0' not in df.columns:
                continue

            last = df.iloc[-1]
            price, rsi, lower_bb, upper_bb = last['close'], last['RSI'], last['BBL_20_2.0'], last['BBU_20_2.0']
            whale = get_recent_whale_signal(token, db_conn)
            
            sig, conf = "HOLD", 0
            if price <= lower_bb and rsi < 35:
                sig, conf = "BUY", 70
                if whale and whale[0] == 'Bullish': 
                    conf = 95
            elif price >= upper_bb and rsi > 65:
                sig, conf = "SELL", 70
                if whale and whale[0] == 'Bearish': 
                    conf = 95
            
            if sig != "HOLD":
                signals.append({
                    'token': token, 
                    'price': price, 
                    'signal': sig, 
                    'conf': conf, 
                    'rsi': rsi, 
                    'whale': whale[0] if whale else "None"
                })
                logger.info(f"🎯 {token} {sig} ({conf}%) at ${price}")
        except Exception as e:
            logger.error(f"Error processing {token}: {e}")
            
    return signals

def save_signals(signals, db_conn):
    if not signals: 
        return
    try:
        ts = datetime.datetime.now().isoformat()
        with db_conn:
            for s in signals:
                db_conn.execute(
                    "INSERT INTO ai_signals (token, entry_price, signal, confidence, rsi, whale_context, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                    (s['token'], s['price'], s['signal'], s['conf'], s['rsi'], s['whale'], ts)
                )
    except Exception as e:
        logger.error(f"Error saving signals: {e}")

def main():
    init_db()
    db_conn = get_db_connection()
    
    while True:
        try:
            signals = generate_signal(db_conn)
            save_signals(signals, db_conn)
            update_backtests(db_conn)
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        time.sleep(60)

if __name__ == "__main__":
    main()
