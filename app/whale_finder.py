import aiohttp
from solana_utils import get_wallet_balance, get_wallet_age
import os

# Filters
MIN_BALANCE_USD = float(os.getenv("MIN_BALANCE_USD", 100000))  # $100k+
MIN_WALLET_AGE_DAYS = int(os.getenv("MIN_WALLET_AGE_DAYS", 5))  # 5 days+
DEX_PAIRS_LIMIT = int(os.getenv("DEX_PAIRS_LIMIT", 10))        # top N pools

DEX_SEARCH_URL = "https://api.dexscreener.com/latest/dex/search"
DEX_TRADES_URL = "https://api.dexscreener.com/latest/dex/trades?pairAddress={}"

async def find_whales():
    """
    Scan top Dexscreener pools, fetch recent trades, collect wallets,
    filter by balance and age, and return the qualified list.
    """
    wallets = set()

    # 1️⃣ Fetch top pairs
    async with aiohttp.ClientSession() as session:
        async with session.get(DEX_PAIRS_URL) as resp:
            data = await resp.json()
            pairs = data.get("pairs", [])[:DEX_PAIRS_LIMIT]

    # 2️⃣ For each pair, fetch recent trades
    async with aiohttp.ClientSession() as session:
        for pair in pairs:
            pair_addr = pair.get("pairAddress")
            if not pair_addr:
                continue
            url = DEX_TRADES_URL.format(pair_addr)
            async with session.get(url) as resp:
                trades_data = await resp.json()
                trades = trades_data.get("trades", [])
                for t in trades:
                    # collect both taker and maker
                    taker = t.get("takerAddress")
                    maker = t.get("makerAddress")
                    if taker:
                        wallets.add(taker)
                    if maker:
                        wallets.add(maker)

    # 3️⃣ Filter wallets
    qualified = []
    for addr in wallets:
        balance = await get_wallet_balance(addr)
        age_days = await get_wallet_age(addr)
        if balance >= MIN_BALANCE_USD and age_days >= MIN_WALLET_AGE_DAYS:
            qualified.append({
                "address": addr,
                "balance": balance,
                "age_days": age_days
            })

    return qualified