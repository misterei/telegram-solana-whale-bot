import aiohttp
import os
from datetime import datetime, UTC

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
HELIUS_BASE = f"https://api.helius.xyz/v0"
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
COINGECKO_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"

# === Utility ===
async def get_sol_price():
    async with aiohttp.ClientSession() as session:
        async with session.get(COINGECKO_PRICE_URL) as resp:
            data = await resp.json()
            return data.get("solana", {}).get("usd", 0)

# === Get Balance ===
async def get_wallet_balance(wallet_address: str) -> float:
    if HELIUS_API_KEY:
        helius_url = f"{HELIUS_BASE}/addresses/{wallet_address}/balances?api-key={HELIUS_API_KEY}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(helius_url) as resp:
                    data = await resp.json()
                    sol_lamports = data.get("nativeBalance", {}).get("lamports", 0)
                    sol = sol_lamports / 1e9
                    price = await get_sol_price()
                    return sol * price
        except Exception as e:
            print(f"[Helius] Balance fetch failed, fallback to RPC. Reason: {e}")

    # fallback to RPC
    payload = {"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [wallet_address]}
    async with aiohttp.ClientSession() as session:
        async with session.post(SOLANA_RPC_URL, json=payload) as resp:
            res = await resp.json()
            lamports = res.get("result", {}).get("value", 0)
            sol = lamports / 1e9
    price = await get_sol_price()
    return sol * price

# === Get Wallet Age ===
async def get_wallet_age(wallet_address: str) -> int:
    if HELIUS_API_KEY:
        helius_url = f"{HELIUS_BASE}/addresses/{wallet_address}/transactions?api-key={HELIUS_API_KEY}&limit=1&sort=asc"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(helius_url) as resp:
                    txs = await resp.json()
                    if txs and txs[0].get("timestamp"):
                        first_time = datetime.fromtimestamp(txs[0]["timestamp"], UTC)
                        return (datetime.now(UTC) - first_time).days
        except Exception as e:
            print(f"[Helius] Age fetch failed, fallback to RPC. Reason: {e}")

    # fallback to RPC
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [wallet_address, {"limit": 1, "commitment": "confirmed"}]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(SOLANA_RPC_URL, json=payload) as resp:
            res = await resp.json()
            sigs = res.get("result", [])
            if not sigs:
                return 0
            ts = sigs[-1].get("blockTime")
            if not ts:
                return 0
            first_date = datetime.fromtimestamp(ts, UTC)
            return (datetime.now(UTC) - first_date).days
