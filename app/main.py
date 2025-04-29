import os
from datetime import datetime, UTC
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from whale_finder import find_whales
from aiohttp import web

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PORT = int(os.getenv("PORT", "8443"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 300))  # 5 min default

# Global scan status
scan_status = {
    "last_scan": None,
    "last_count": 0,
    "last_error": None
}

# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is alive and running via webhook!")

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
        if scan_status["last_count"] == 0 and elapsed >= 1800:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text="✅ Still scanning... no whales detected yet."
            )

# Create aiohttp server manually
async def on_startup(app):
    await app.bot.set_webhook(url=WEBHOOK_URL)
    print(f"✅ Webhook registered: {WEBHOOK_URL}")

def main():
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID or not WEBHOOK_URL:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN, CHAT_ID, or WEBHOOK_URL")

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(on_startup)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    application.job_queue.run_repeating(poll_whales, interval=POLL_INTERVAL, first=10)
    application.job_queue.run_repeating(keep_alive, interval=600, first=60)

    web_app = web.Application()
    web_app.router.add_post("/", application.webhook_handler)

    print(f"🚀 Starting aiohttp server on port {PORT}")
    web.run_app(web_app, port=PORT)

if __name__ == "__main__":
    main()
