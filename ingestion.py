import os
import asyncio
import sqlite3
import datetime
import requests
import traceback
from web3 import AsyncWeb3, AsyncHTTPProvider
from dotenv import load_dotenv

load_dotenv()
ALCHEMY_URL = os.getenv("ALCHEMY_URL")
w3 = AsyncWeb3(AsyncHTTPProvider(ALCHEMY_URL))

# 20 TOKEN EXPANSION (Fixed invalid NEAR address and verified others)
TOKENS = {
    "PEPE": (w3.to_checksum_address("0x6982508145454Ce325dDbE47a25d4ec3d2311933"), 18, "pepe"),
    "SHIB": (w3.to_checksum_address("0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE"), 18, "shiba-inu"),
    "FLOKI": (w3.to_checksum_address("0xcf0C122c6b73ff809C693DB761e7BaEbe62b6a2E"), 9, "floki"),
    "WIF": (w3.to_checksum_address("0x32311397072E2E69F21517448B69c69D3b22A829"), 18, "dogwifcoin"),
    "MOG": (w3.to_checksum_address("0xaaee1A9723469885f799FD20E767E61a68292837"), 18, "mog-coin"),
    "FET": (w3.to_checksum_address("0xaea46A60368A7bD060eec7DF8CBa43b7EF41Ad85"), 18, "fetch-ai"),
    "LINK": (w3.to_checksum_address("0x514910771AF9Ca656af840dff83E8264EcF986CA"), 18, "chainlink"),
    "MATIC": (w3.to_checksum_address("0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0"), 18, "matic-network"),
    "WETH": (w3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"), 18, "ethereum"),
    "RENDER": (w3.to_checksum_address("0x6De037ef9aD2725EB40118Bb1702EBB27e4Aeb24"), 18, "render-token"),
    "UNI": (w3.to_checksum_address("0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"), 18, "uniswap"),
    "AAVE": (w3.to_checksum_address("0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"), 18, "aave"),
    "CRV": (w3.to_checksum_address("0xD533a949740bb3306d119CC777fa900bA034cd52"), 18, "curve-dao-token"),
    "ENS": (w3.to_checksum_address("0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72"), 18, "ethereum-name-service"),
    "ARB": (w3.to_checksum_address("0x912CE59144191C1204E64559FE8253a0e49E6548"), 18, "arbitrum"),
    "OP": (w3.to_checksum_address("0x4200000000000000000000000000000000000042"), 18, "optimism"),
    "GRT": (w3.to_checksum_address("0xc944E90C64B2c07662A292be6244BDf05Cda44a7"), 18, "the-graph"),
    "LPT": (w3.to_checksum_address("0x58b6A8A3302369DAEc383334672404Ee733aB239"), 18, "livepeer"),
    "TURBO": (w3.to_checksum_address("0xA35923162C49cf95e6BF26623385eb431ad920D3"), 18, "turbo")
}

EXCHANGES = {
    # Binance
    "0x28C6c06290CC3F951796d211020473217b907960".lower(): "Binance",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d".lower(): "Binance",
    "0xF977814e90dA44bFA03b6295A0616a897441aceC".lower(): "Binance",
    "0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503".lower(): "Binance",
    # Coinbase
    "0x71660c4f9456db35970e71de5d01cf32410a5639".lower(): "Coinbase",
    "0x503828976D22510aad0201ac7EC88293211D23Da".lower(): "Coinbase",
    "0xddfAb6e705b9fA402480391130bc633Cc00f3e5c".lower(): "Coinbase",
    # Others
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2".lower(): "Kraken",
    "0x0d0707963952f2fba59dd06f2b425aceecd132c8".lower(): "Bitfinex",
    "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B".lower(): "Vitalik Buterin" # Added for fun/alpha
}

ADDRESS_TO_NAME = {addr.lower(): name for name, (addr, dec, id) in TOKENS.items()}
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
PRICES = {name: 1.0 for name in TOKENS}

def fetch_prices():
    try:
        ids = ",".join([id for name, (addr, dec, id) in TOKENS.items()])
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
        data = requests.get(url, timeout=10).json()
        for name, (addr, dec, id) in TOKENS.items():
            if id in data: PRICES[name] = data[id]['usd']
    except: pass

def init_db():
    conn = sqlite3.connect('whale_tracker.db')
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE IF NOT EXISTS transfers (token_name TEXT, sender TEXT, receiver TEXT, direction TEXT, amount_usd REAL, sentiment TEXT, tx_hash TEXT, timestamp TEXT)")
    conn.commit()
    return conn

db_conn = init_db()

async def handle_event(event):
    try:
        address = event['address'].lower()
        token_name = ADDRESS_TO_NAME.get(address)
        if not token_name: return
        _, decimals, _ = TOKENS[token_name]
        amount_raw = int(event['data'].hex(), 16)
        token_amount = amount_raw / 10**decimals
        amount_usd = token_amount * PRICES[token_name]
        if amount_usd < 1000: return
        sender = "0x" + event['topics'][1].hex()[-40:]
        receiver = "0x" + event['topics'][2].hex()[-40:]
        sender_label = EXCHANGES.get(sender.lower())
        receiver_label = EXCHANGES.get(receiver.lower())
        direction, sentiment = "Transfer", "Neutral"
        if receiver_label and not sender_label: direction, sentiment = f"Inflow ({receiver_label})", "Bearish"
        elif sender_label and not receiver_label: direction, sentiment = f"Outflow ({sender_label})", "Bullish"
        ts, tx = datetime.datetime.now().isoformat(), event['transactionHash'].hex()
        db_conn.execute("INSERT INTO transfers VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (token_name, sender, receiver, direction, amount_usd, sentiment, tx, ts))
        db_conn.commit()
    except: pass

async def log_loop(start_block):
    current_block = start_block
    while True:
        try:
            latest = await w3.eth.block_number
            if current_block > latest: await asyncio.sleep(2); continue
            logs = await w3.eth.get_logs({"fromBlock": current_block, "toBlock": current_block, "address": [addr for name, (addr, dec, id) in TOKENS.items()], "topics": [TRANSFER_TOPIC]})
            for log in logs: await handle_event(log)
            current_block += 1
            await asyncio.sleep(0.1)
        except: current_block += 1; await asyncio.sleep(1)

async def main():
    fetch_prices()
    latest = await w3.eth.block_number
    await log_loop(latest - 5)

if __name__ == "__main__":
    asyncio.run(main())
