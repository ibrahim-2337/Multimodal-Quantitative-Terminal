import logging
from web3 import Web3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# Shared Tokens configuration
# (Address, Decimals, CoinGecko ID, Binance Symbol)
TOKENS = {
    "PEPE": (Web3.to_checksum_address("0x6982508145454Ce325dDbE47a25d4ec3d2311933"), 18, "pepe", "PEPE/USDT"),
    "SHIB": (Web3.to_checksum_address("0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE"), 18, "shiba-inu", "SHIB/USDT"),
    "FLOKI": (Web3.to_checksum_address("0xcf0C122c6b73ff809C693DB761e7BaEbe62b6a2E"), 9, "floki", "FLOKI/USDT"),
    "WIF": (Web3.to_checksum_address("0x32311397072E2E69F21517448B69c69D3b22A829"), 18, "dogwifcoin", "WIF/USDT"),
    "MOG": (Web3.to_checksum_address("0xaaee1A9723469885f799FD20E767E61a68292837"), 18, "mog-coin", "MOG/USDT"),
    "FET": (Web3.to_checksum_address("0xaea46A60368A7bD060eec7DF8CBa43b7EF41Ad85"), 18, "fetch-ai", "FET/USDT"),
    "LINK": (Web3.to_checksum_address("0x514910771AF9Ca656af840dff83E8264EcF986CA"), 18, "chainlink", "LINK/USDT"),
    "MATIC": (Web3.to_checksum_address("0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0"), 18, "matic-network", "POL/USDT"),
    "WETH": (Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"), 18, "ethereum", "ETH/USDT"),
    "RENDER": (Web3.to_checksum_address("0x6De037ef9aD2725EB40118Bb1702EBB27e4Aeb24"), 18, "render-token", "RENDER/USDT"),
    "UNI": (Web3.to_checksum_address("0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"), 18, "uniswap", "UNI/USDT"),
    "AAVE": (Web3.to_checksum_address("0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"), 18, "aave", "AAVE/USDT"),
    "CRV": (Web3.to_checksum_address("0xD533a949740bb3306d119CC777fa900bA034cd52"), 18, "curve-dao-token", "CRV/USDT"),
    "ENS": (Web3.to_checksum_address("0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72"), 18, "ethereum-name-service", "ENS/USDT"),
    "ARB": (Web3.to_checksum_address("0x912CE59144191C1204E64559FE8253a0e49E6548"), 18, "arbitrum", "ARB/USDT"),
    "OP": (Web3.to_checksum_address("0x4200000000000000000000000000000000000042"), 18, "optimism", "OP/USDT"),
    "GRT": (Web3.to_checksum_address("0xc944E90C64B2c07662A292be6244BDf05Cda44a7"), 18, "the-graph", "GRT/USDT"),
    "LPT": (Web3.to_checksum_address("0x58b6A8A3302369DAEc383334672404Ee733aB239"), 18, "livepeer", "LPT/USDT"),
    "TURBO": (Web3.to_checksum_address("0xA35923162C49cf95e6BF26623385eb431ad920D3"), 18, "turbo", "TURBO/USDT")
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
    "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B".lower(): "Vitalik Buterin"
}

ADDRESS_TO_NAME = {addr.lower(): name for name, (addr, dec, cg_id, sym) in TOKENS.items()}
