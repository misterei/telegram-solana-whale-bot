import os
from datetime import datetime, UTC
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from whale_finder import find_whales

# Environment variables (set via Railway)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 300))  # Default 5 minutes

# Global status tracker
scan_status = {
    "last_scan": None,
    "last_count": 0,
    "last_error": None
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is alive and running.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if scan_status["last_scan"]:
        last_time = scan_status["last_scan"].strftime('%Y-%m-%d %H:%M:%S')
        msg = f"📊 Last scan: {last_time}\nWhales found: {scan_status['last_count']}"
        if scan_status["last_error"]:
            msg += f"\n⚠️ Last error: {scan_status['last_error']}"
    else:
        msg = "⏳ Bot has not scanned yet."
    await update.message.reply_text(msg)

async def poll_whales(context: ContextTypes.DEFAULT_TYPE):
    try:
        whales = await find_whales()
        scan_status["last_scan"] = datetime.now(UTC)
        scan_status["last_count"] = len(whales)
        scan_status["last_error"] = None

        for whale in whales:
            msg = (
                f"🐋 *New Whale Detected!*\n"
                f"*Address:* `{whale['address']}`\n"
                f"*Balance:* ${whale['balance']:,}\n"
                f"*Wallet Age:* {whale['age_days']} days"
            )
            if whale['balance'] >= 5_000_000:
                msg += " 🔥💎"
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=msg,
                parse_mode="Markdown"
            )
    except Exception as e:
        scan_status["last_scan"] = datetime.now(UTC)
        scan_status["last_error"] = str(e)
        print(f"Error while fetching whales: {e}")

async def keep_alive(context: ContextTypes.DEFAULT_TYPE):
    if scan_status["last_scan"]:
        elapsed = (datetime.now(UTC) - scan_status["last_scan"]).seconds
        if scan_status["last_count"] == 0 and elapsed >= 1800:  # 30 mins
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text="✅ Still scanning... no whales detected yet."
            )

def main():
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID env vars")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))

    # Jobs
    app.job_queue.run_repeating(poll_whales, interval=POLL_INTERVAL, first=10)
    app.job_queue.run_repeating(keep_alive, interval=600, first=60)  # check every 10 min

    print("🤖 Bot started. Monitoring for Solana whales...")
    app.run_polling()

if __name__ == '__main__':
    main()
