import asyncio
import json
import logging
import datetime
import pandas as pd
import pandas_ta as ta
import websockets
import aiohttp
from config import TOKENS
from database import init_db, get_db_connection

logger = logging.getLogger("SignalEngineWS")

# Real-time state
ohlcv_data = {token: pd.DataFrame() for token in TOKENS}
last_signal_time = {token: datetime.datetime.min for token in TOKENS}

def calculate_signals(token, df, db_conn):
    """
    Methodology Upgrade: Multi-Timeframe Consistency check.
    Logic: Requires 1m RSI extreme AND 1m Bollinger break.
    """
    if len(df) < 30: return
    
    # Calculate indicators
    df['RSI'] = ta.rsi(df['close'], length=14)
    bbands = ta.bbands(df['close'], length=20, std=2)
    if bbands is None: return
    df = pd.concat([df, bbands], axis=1)
    
    last = df.iloc[-1]
    price, rsi = last['close'], last['RSI']
    lower_bb, upper_bb = last['BBL_20_2.0'], last['BBU_20_2.0']
    
    # Check for recent whale context (last 15m)
    fifteen_ago = (datetime.datetime.now() - datetime.timedelta(minutes=15)).isoformat()
    whale = db_conn.execute(
        "SELECT sentiment FROM transfers WHERE token_name = ? AND timestamp > ? ORDER BY timestamp DESC LIMIT 1",
        (token, fifteen_ago)
    ).fetchone()
    
    sig, conf = "HOLD", 0
    if price <= lower_bb and rsi < 30: # More aggressive RSI filter
        sig, conf = "BUY", 75
        if whale and whale[0] == 'Bullish': conf = 98
    elif price >= upper_bb and rsi > 70:
        sig, conf = "SELL", 75
        if whale and whale[0] == 'Bearish': conf = 98

    # Prevent signal spam (max 1 per 5 mins per token)
    now = datetime.datetime.now()
    if sig != "HOLD" and (now - last_signal_time[token]).total_seconds() > 300:
        last_signal_time[token] = now
        logger.info(f"🎯 WS SIGNAL: {token} {sig} ({conf}%) at ${price:.4f}")
        with db_conn:
            db_conn.execute(
                "INSERT INTO ai_signals (token, entry_price, signal, confidence, rsi, whale_context, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (token, price, sig, conf, rsi, whale[0] if whale else "None", now.isoformat())
            )

async def binance_ws_loop(db_conn):
    """
    Real-time Upgrade: High-speed WebSockets (Free public feed)
    """
    # Create stream names for all 20 tokens
    # e.g., ethusdt@kline_1m
    streams = [f"{TOKENS[token][3].replace('/', '').lower()}@kline_1m" for token in TOKENS]
    url = f"wss://stream.binance.com:9443/ws/{'/'.join(streams)}"
    
    logger.info("Connecting to Binance WebSocket...")
    async with websockets.connect(url) as ws:
        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                
                # Extract kline data
                k = data['k']
                if not k['x']: continue # Only process closed 1m candles
                
                symbol_raw = data['s']
                # Map back to token name
                token = next((t for t, v in TOKENS.items() if v[3].replace('/', '') == symbol_raw), None)
                if not token: continue
                
                new_row = {
                    'timestamp': pd.to_datetime(k['t'], unit='ms'),
                    'open': float(k['o']),
                    'high': float(k['h']),
                    'low': float(k['l']),
                    'close': float(k['c']),
                    'volume': float(k['v'])
                }
                
                # Update rolling dataframe (keep last 100 mins)
                df = ohlcv_data[token]
                df = pd.concat([df, pd.DataFrame([new_row])]).drop_duplicates('timestamp').tail(100)
                ohlcv_data[token] = df
                
                # Calculate signals immediately on candle close
                calculate_signals(token, df, db_conn)
                
            except Exception as e:
                logger.error(f"WS Loop Error: {e}")
                await asyncio.sleep(5)

async def backtest_updater_loop(db_conn):
    """
    Methodology Upgrade: Async backtesting every 5 minutes
    """
    while True:
        try:
            fifteen_ago = (datetime.datetime.now() - datetime.timedelta(minutes=15)).isoformat()
            pending = db_conn.execute(
                "SELECT rowid, token, signal, entry_price FROM ai_signals WHERE status = 'PENDING' AND timestamp < ?",
                (fifteen_ago,)
            ).fetchall()
            
            for rowid, token, signal, entry_price in pending:
                df = ohlcv_data[token]
                if not df.empty:
                    curr = df.iloc[-1]['close']
                    roi = ((curr - entry_price) / entry_price) * 100
                    status = "WIN" if (signal == "BUY" and roi > 0.1) or (signal == "SELL" and roi < -0.1) else "LOSS"
                    with db_conn:
                        db_conn.execute("UPDATE ai_signals SET price_15m = ?, status = ? WHERE rowid = ?", (curr, status, rowid))
            
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Backtest error: {e}")
            await asyncio.sleep(60)

async def main():
    init_db()
    db_conn = get_db_connection()
    logger.info("Starting WebSocket Signal Engine...")
    await asyncio.gather(
        binance_ws_loop(db_conn),
        backtest_updater_loop(db_conn)
    )

if __name__ == "__main__":
    asyncio.run(main())
