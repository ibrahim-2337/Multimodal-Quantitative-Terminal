import os
import asyncio
import datetime
import traceback
import aiohttp
import logging
import numpy as np
from web3 import AsyncWeb3, AsyncHTTPProvider
from dotenv import load_dotenv
from config import TOKENS, EXCHANGES, ADDRESS_TO_NAME
from database import init_db, get_db_connection

load_dotenv()
logger = logging.getLogger("Ingestion")

ALCHEMY_URL = os.getenv("ALCHEMY_URL")
w3 = AsyncWeb3(AsyncHTTPProvider(ALCHEMY_URL))
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
PRICES = {name: 1.0 for name in TOKENS}

# Cache for dynamic thresholding
transfer_history = {name: [] for name in TOKENS}

async def fetch_prices():
    ids = ",".join([cg_id for name, (addr, dec, cg_id, sym) in TOKENS.items()])
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    for name, (addr, dec, cg_id, sym) in TOKENS.items():
                        if cg_id in data:
                            PRICES[name] = data[cg_id]['usd']
                    logger.info("Prices updated.")
    except Exception as e:
        logger.error(f"Price fetch error: {e}")

def is_whale_move(token_name, amount_usd):
    """
    Dynamic methodology: A move is a 'Whale' if it is:
    1. Over $1,000 (Base floor)
    2. AND in the top 5% of recent moves OR > 2 Standard Deviations from the mean.
    """
    history = transfer_history[token_name]
    
    # Base floor to avoid micro-cap noise
    if amount_usd < 1000:
        return False
        
    if len(history) < 20:
        # Not enough data yet, fallback to $5k as a conservative floor
        history.append(amount_usd)
        return amount_usd > 5000

    mean = np.mean(history)
    std = np.std(history)
    threshold = mean + (2 * std)
    
    # Update rolling history (keep last 100)
    history.append(amount_usd)
    if len(history) > 100:
        history.pop(0)
        
    # It's a whale if it's statistically significant
    return amount_usd > threshold

async def handle_event(event, db_conn):
    try:
        address = event['address'].lower()
        token_name = ADDRESS_TO_NAME.get(address)
        if not token_name:
            return

        _, decimals, _, _ = TOKENS[token_name]
        amount_raw = int(event['data'].hex(), 16)
        token_amount = amount_raw / 10**decimals
        amount_usd = token_amount * PRICES[token_name]
        
        # Methodology Upgrade: Dynamic Thresholding
        if not is_whale_move(token_name, amount_usd):
            return

        sender = "0x" + event['topics'][1].hex()[-40:]
        receiver = "0x" + event['topics'][2].hex()[-40:]
        sender_label = EXCHANGES.get(sender.lower())
        receiver_label = EXCHANGES.get(receiver.lower())
        
        direction, sentiment = "Transfer", "Neutral"
        if receiver_label and not sender_label:
            direction, sentiment = f"Inflow ({receiver_label})", "Bearish"
        elif sender_label and not receiver_label:
            direction, sentiment = f"Outflow ({sender_label})", "Bullish"

        ts = datetime.datetime.now().isoformat()
        tx = event['transactionHash'].hex()

        with db_conn:
            db_conn.execute(
                "INSERT INTO transfers VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                (token_name, sender, receiver, direction, amount_usd, sentiment, tx, ts)
            )
        logger.info(f"🚨 WHALE DETECTED: {direction} of ${amount_usd:,.2f} {token_name}")
    except Exception as e:
        logger.error(f"Event error: {e}")

async def log_loop(start_block, db_conn):
    current_block = start_block
    addresses = [addr for name, (addr, dec, cg_id, sym) in TOKENS.items()]
    
    while True:
        try:
            latest = await w3.eth.block_number
            if current_block > latest:
                await asyncio.sleep(2)
                continue
            
            logs = await w3.eth.get_logs({
                "fromBlock": current_block, 
                "toBlock": current_block, 
                "address": addresses, 
                "topics": [TRANSFER_TOPIC]
            })
            
            for log in logs:
                await handle_event(log, db_conn)
            
            current_block += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Block error {current_block}: {e}")
            current_block += 1
            await asyncio.sleep(1)

async def price_update_loop():
    while True:
        await fetch_prices()
        await asyncio.sleep(300)

async def main():
    init_db()
    db_conn = get_db_connection()
    await fetch_prices()
    latest = await w3.eth.block_number
    await asyncio.gather(log_loop(latest - 2, db_conn), price_update_loop())

if __name__ == "__main__":
    asyncio.run(main())
