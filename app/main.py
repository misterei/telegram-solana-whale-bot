import asyncio
import os
from telegram import Bot
from whale_finder import find_whales

# Environment variables (set via Railway or hosting service)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # your target chat or channel ID

# Poll interval in seconds
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 300))  # default 5 minutes

async def main():
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in environment")

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    print("🤖 Bot started. Monitoring for Solana whales...")

    while True:
        try:
            whales = await find_whales()
            for whale in whales:
                msg = (
                    f"🐋 *New Whale Detected!*\n"
                    f"*Address:* `{whale['address']}`\n"
                    f"*Balance:* ${whale['balance']:,}\n"
                    f"*Wallet Age:* {whale['age_days']} days"
                )
                # emoji boost for super whales
                if whale['balance'] >= 5_000_000:
                    msg += " 🔥💎"
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=msg,
                    parse_mode="Markdown"
                )
        except Exception as e:
            print(f"Error while fetching whales: {e}")

        await asyncio.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    asyncio.run(main())