import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-app-name.onrender.com/webhook

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --------------------------
#   Хендлеры
# --------------------------
@dp.message(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer("Бот работает через webhook! Привет 👋")

@dp.message(commands=["ping"])
async def ping_cmd(message: types.Message):
    await message.answer("Pong!")


# --------------------------
#   ПЛАНИРОВЩИК
# --------------------------
scheduler = AsyncIOScheduler()

async def send_notification():
    try:
        await bot.send_message(CHAT_ID, "Это уведомление от бота через webhook 🚀")
    except Exception as e:
        print("Ошибка при отправке уведомления:", e)

scheduler.add_job(send_notification, "interval", minutes=10)


# --------------------------
#   WEBHOOK SERVER
# --------------------------
async def handle_webhook(request: web.Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return web.Response(text="ok")


async def on_startup(app: web.Application):
    print("Setting webhook:", WEBHOOK_URL)
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    scheduler.start()


async def on_shutdown(app: web.Application):
    print("Removing webhook")
    await bot.delete_webhook()
    await bot.session.close()


def main():
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))


if __name__ == "__main__":
    main()
