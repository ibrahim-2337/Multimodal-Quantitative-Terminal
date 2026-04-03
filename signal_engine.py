import ccxt
import pandas as pd
import pandas_ta as ta
import sqlite3
import time
import datetime
import traceback

# Map 20 tokens to Binance symbols
SYMBOL_MAP = {
    "PEPE": "PEPE/USDT", "LINK": "LINK/USDT", "MATIC": "POL/USDT", "WETH": "ETH/USDT",
    "FET": "FET/USDT", "SHIB": "SHIB/USDT", "FLOKI": "FLOKI/USDT", "WIF": "WIF/USDT",
    "MOG": "MOG/USDT", "RENDER": "RENDER/USDT", "UNI": "UNI/USDT", "AAVE": "AAVE/USDT",
    "CRV": "CRV/USDT", "ENS": "ENS/USDT", "ARB": "ARB/USDT", "OP": "OP/USDT",
    "GRT": "GRT/USDT", "LPT": "LPT/USDT", "TURBO": "TURBO/USDT"
}

EXCHANGE = ccxt.binance()

def init_db():
    conn = sqlite3.connect('whale_tracker.db')
    conn.execute("CREATE TABLE IF NOT EXISTS ai_signals (token TEXT, entry_price REAL, signal TEXT, confidence INTEGER, rsi REAL, whale_context TEXT, timestamp TEXT, price_15m REAL, status TEXT DEFAULT 'PENDING')")
    conn.commit()
    conn.close()

def fetch_ohlcv(token_name):
    symbol = SYMBOL_MAP.get(token_name)
    if not symbol: return None
    try:
        bars = EXCHANGE.fetch_ohlcv(symbol, timeframe='1m', limit=100)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except: return None

def calculate_indicators(df):
    try:
        df['RSI'] = ta.rsi(df['close'], length=14)
        bbands = ta.bbands(df['close'], length=20, std=2)
        df = pd.concat([df, bbands], axis=1)
        return df
    except: return df

def get_recent_whale_signal(token_name):
    try:
        conn = sqlite3.connect('whale_tracker.db')
        fifteen_ago = (datetime.datetime.now() - datetime.timedelta(minutes=15)).isoformat()
        query = f"SELECT sentiment FROM transfers WHERE token_name = '{token_name}' AND timestamp > '{fifteen_ago}' ORDER BY timestamp DESC LIMIT 1"
        res = conn.execute(query).fetchone()
        conn.close()
        return res
    except: return None

def update_backtests():
    try:
        conn = sqlite3.connect('whale_tracker.db')
        fifteen_ago = (datetime.datetime.now() - datetime.timedelta(minutes=15)).isoformat()
        pending = conn.execute("SELECT rowid, token, signal, entry_price FROM ai_signals WHERE status = 'PENDING' AND timestamp < ?", (fifteen_ago,)).fetchall()
        for rowid, token, signal, entry_price in pending:
            df = fetch_ohlcv(token)
            if df is not None:
                curr = df.iloc[-1]['close']
                roi = ((curr - entry_price) / entry_price) * 100
                if signal == "BUY": status = "WIN" if roi > 0.1 else "LOSS"
                else: status = "WIN" if roi < -0.1 else "LOSS"
                conn.execute("UPDATE ai_signals SET price_15m = ?, status = ? WHERE rowid = ?", (curr, status, rowid))
        conn.commit()
        conn.close()
    except: pass

def generate_signal():
    print(f"\n--- 20-Token Multi-Scan: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    signals = []
    for token in SYMBOL_MAP.keys():
        try:
            df = fetch_ohlcv(token)
            if df is None or len(df) < 50: continue
            df = calculate_indicators(df)
            last = df.iloc[-1]
            price, rsi, lower_bb, upper_bb = last['close'], last['RSI'], last['BBL_20_2.0'], last['BBU_20_2.0']
            whale = get_recent_whale_signal(token)
            sig, conf = "HOLD", 0
            if price <= lower_bb and rsi < 35:
                sig, conf = "BUY", 70
                if whale and whale[0] == 'Bullish': conf = 95
            elif price >= upper_bb and rsi > 65:
                sig, conf = "SELL", 70
                if whale and whale[0] == 'Bearish': conf = 95
            if sig != "HOLD":
                signals.append({'token': token, 'price': price, 'signal': sig, 'conf': conf, 'rsi': rsi, 'whale': whale[0] if whale else "None"})
                print(f"🎯 {token} {sig} ({conf}%)")
        except: pass
    return signals

def save_signals(signals):
    if not signals: return
    try:
        conn = sqlite3.connect('whale_tracker.db')
        ts = datetime.datetime.now().isoformat()
        for s in signals:
            conn.execute("INSERT INTO ai_signals (token, entry_price, signal, confidence, rsi, whale_context, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)", (s['token'], s['price'], s['signal'], s['conf'], s['rsi'], s['whale'], ts))
        conn.commit()
        conn.close()
    except: pass

if __name__ == "__main__":
    init_db()
    while True:
        try:
            signals = generate_signal()
            save_signals(signals)
            update_backtests()
        except: pass
        time.sleep(60)
