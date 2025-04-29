import aiohttp
import os
from datetime import datetime

SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
COINGECKO_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"

async def get_sol_price():
    async with aiohttp.ClientSession() as session:
        async with session.get(COINGECKO_PRICE_URL) as resp:
            data = await resp.json()
            return data.get("solana", {}).get("usd", 0)

async def get_wallet_balance(wallet_address: str) -> float:
    """
    Returns the USD value of SOL balance for the given address.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [wallet_address]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(SOLANA_RPC_URL, json=payload) as resp:
            res = await resp.json()
            lamports = res.get("result", {}).get("value", 0)
            sol = lamports / 1e9

    price = await get_sol_price()
    return sol * price

async def get_wallet_age(wallet_address: str) -> int:
    """
    Returns wallet age in days based on the first confirmed transaction.
    """
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
            # fetch the oldest of the returned signatures
            sig = sigs[-1]
            ts = sig.get("blockTime")
            if not ts:
                return 0
            first_date = datetime.utcfromtimestamp(ts)
            delta = datetime.utcnow() - first_date
            return delta.days