import os
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hello! Your bot is alive and running.")

# --- Webhook Handler ---
async def telegram_webhook(request):
    try:
        data = await request.json()
        update = Update.de_json(data, request.app["bot"].bot)
        await request.app["bot"].process_update(update)
        print("🔥 Webhook received:", data)
        return web.Response(status=200, text="OK")
    except Exception as e:
        print("🚨 Webhook error:", e)
        return web.Response(status=500, text="Error")

# --- Healthcheck ---
async def healthcheck(request):
    return web.Response(text="OK", status=200)

# --- Startup Event ---
async def on_startup(app):
    await app["bot"].initialize()
    await app["bot"].start()
    await app["bot"].bot.set_webhook(url=WEBHOOK_URL)
    print(f"✅ Webhook set to {WEBHOOK_URL}")

# --- Cleanup Event ---
async def on_cleanup(app):
    await app["bot"].stop()
    print("🛑 Bot stopped.")

# --- Main Entrypoint ---
def main():
    if not TELEGRAM_BOT_TOKEN or not WEBHOOK_URL:
        raise Exception("Missing TELEGRAM_BOT_TOKEN or WEBHOOK_URL!")

    bot_app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))

    web_app = web.Application()
    web_app["bot"] = bot_app
    web_app.router.add_post("/", telegram_webhook)
    web_app.router.add_get("/ping", healthcheck)

    web_app.on_startup.append(on_startup)
    web_app.on_cleanup.append(on_cleanup)

    print(f"🚀 Server running on port {PORT}")
    web.run_app(web_app, port=PORT)

if __name__ == "__main__":
    main()
