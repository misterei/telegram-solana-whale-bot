import aiohttp
import os
from solana_utils import get_wallet_balance, get_wallet_age

MIN_BALANCE_USD = float(os.getenv("MIN_BALANCE_USD", 100000))
MIN_WALLET_AGE_DAYS = int(os.getenv("MIN_WALLET_AGE_DAYS", 5))
DEX_PAIRS_LIMIT = int(os.getenv("DEX_PAIRS_LIMIT", 10))
SEARCH_QUERY = os.getenv("SEARCH_QUERY", "SOL")

DEX_SEARCH_URL = "https://api.dexscreener.com/latest/dex/search"
DEX_TRADES_URL = "https://api.dexscreener.com/latest/dex/trades?pairAddress={}"

async def find_whales():
    wallets = set()

    # 1️⃣ Search for token pairs
    async with aiohttp.ClientSession() as session:
        try:
            resp = await session.get(DEX_SEARCH_URL, params={"q": SEARCH_QUERY})
            if resp.status != 200:
                print(f"Warning: search endpoint returned HTTP {resp.status}")
                return []
            data = await resp.json()
        except Exception as e:
            print(f"Error fetching pairs: {e}")
            return []

        pairs = data.get("pairs", [])[:DEX_PAIRS_LIMIT]

    # 2️⃣ Fetch recent trades from those pairs
    async with aiohttp.ClientSession() as session:
        for pair in pairs:
            pair_addr = pair.get("pairAddress")
            if not pair_addr:
                continue
            try:
                r = await session.get(DEX_TRADES_URL.format(pair_addr))
                if r.status != 200:
                    continue
                trades_data = await r.json()
            except Exception:
                continue

            trades = trades_data.get("trades", [])
            for t in trades:
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
