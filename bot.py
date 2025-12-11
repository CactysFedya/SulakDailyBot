import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ----------------------------------------
# ENV VARIABLES
# ----------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-app.onrender.com/webhook

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ----------------------------------------
# HANDLERS
# ----------------------------------------
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Бот работает через webhook! Привет 👋")

@dp.message(Command("ping"))
async def ping_cmd(message: types.Message):
    await message.answer("Pong!")

# ----------------------------------------
# SCHEDULER (каждые 10 минут)
# ----------------------------------------
scheduler = AsyncIOScheduler()

async def send_notification():
    try:
        await bot.send_message(CHAT_ID, "Это уведомление от бота через webhook 🚀")
    except Exception as e:
        print("Ошибка при отправке уведомления:", e)

scheduler.add_job(send_notification, "interval", minutes=10)

# ----------------------------------------
# WEBHOOK HANDLER
# ----------------------------------------
async def handle_webhook(request: web.Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return web.Response(text="ok")

# Render health-check route
async def health(request):
    return web.Response(text="OK")

# ----------------------------------------
# STARTUP / SHUTDOWN
# ----------------------------------------
async def on_startup(app: web.Application):
    print("Setting webhook:", WEBHOOK_URL)
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    scheduler.start()

async def on_shutdown(app: web.Application):
    print("Removing webhook")
    await bot.delete_webhook()
    await bot.session.close()

# ----------------------------------------
# MAIN
# ----------------------------------------
def main():
    app = web.Application()

    # Webhook endpoint
    app.router.add_post("/webhook", handle_webhook)

    # Health-check for Render
    app.router.add_get("/", health)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Render sets PORT automatically
    port = int(os.getenv("PORT"))
    print(f"Listening on port {port}")

    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
