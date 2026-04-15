import os
import asyncio
import datetime
import traceback
import aiohttp
import logging
from web3 import AsyncWeb3, AsyncHTTPProvider
from dotenv import load_dotenv
from config import TOKENS, EXCHANGES, ADDRESS_TO_NAME
from database import init_db, get_db_connection

load_dotenv()
logger = logging.getLogger("Ingestion")

ALCHEMY_URL = os.getenv("ALCHEMY_URL")
if not ALCHEMY_URL:
    logger.warning("ALCHEMY_URL is not set. Ingestion might fail if relying on it.")

w3 = AsyncWeb3(AsyncHTTPProvider(ALCHEMY_URL))
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
PRICES = {name: 1.0 for name in TOKENS}

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
                    logger.info("Prices updated successfully.")
                else:
                    logger.warning(f"Failed to fetch prices. Status: {response.status}")
    except Exception as e:
        logger.error(f"Error fetching prices: {e}")

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
        
        if amount_usd < 1000:
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
        logger.info(f"Logged {direction} of ${amount_usd:,.2f} {token_name}")
    except Exception as e:
        logger.error(f"Error handling event: {e}\n{traceback.format_exc()}")

async def log_loop(start_block, db_conn):
    current_block = start_block
    addresses = [addr for name, (addr, dec, cg_id, sym) in TOKENS.items()]
    
    logger.info(f"Starting log loop from block {start_block}")
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
            logger.error(f"Error fetching logs for block {current_block}: {e}")
            current_block += 1
            await asyncio.sleep(1)

async def price_update_loop():
    while True:
        await fetch_prices()
        await asyncio.sleep(300) # Update prices every 5 minutes

async def main():
    init_db()
    db_conn = get_db_connection()
    await fetch_prices() # Initial fetch
    
    try:
        latest = await w3.eth.block_number
        start_block = latest - 5
    except Exception as e:
        logger.error(f"Failed to connect to Ethereum node: {e}")
        return

    # Run log_loop and price_update_loop concurrently
    await asyncio.gather(
        log_loop(start_block, db_conn),
        price_update_loop()
    )

if __name__ == "__main__":
    asyncio.run(main())
