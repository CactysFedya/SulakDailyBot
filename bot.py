import os
import traceback
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# -------------------------------
# ENV VARIABLES
# -------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://your-app.onrender.com/webhook
PORT = int(os.getenv("PORT", 10000))   # Render сам задаёт PORT

if not all([BOT_TOKEN, CHAT_ID, WEBHOOK_URL]):
    raise RuntimeError("Не заданы обязательные переменные окружения: BOT_TOKEN, CHAT_ID, WEBHOOK_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# -------------------------------
# HANDLERS
# -------------------------------
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Бот работает через webhook! Привет 👋")

@dp.message(Command("ping"))
async def ping_cmd(message: types.Message):
    await message.answer("Pong!")

# -------------------------------
# SCHEDULER
# -------------------------------
scheduler = AsyncIOScheduler()

async def send_notification():
    try:
        await bot.send_message(CHAT_ID, "Это уведомление от бота через webhook 🚀")
    except Exception as e:
        print("Ошибка при отправке уведомления:", e)
        traceback.print_exc()

scheduler.add_job(send_notification, "interval", minutes=10)

# -------------------------------
# WEBHOOK HANDLER
# -------------------------------
async def handle_webhook(request: web.Request):
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
    except Exception as e:
        print("Ошибка в webhook:", e)
        traceback.print_exc()
    return web.Response(text="ok")

# Health-check для Render
async def health(request):
    return web.Response(text="OK")

# -------------------------------
# STARTUP / SHUTDOWN
# -------------------------------
async def on_startup(app: web.Application):
    try:
        print("Настройка webhook...")
        info = await bot.get_webhook_info()
        if info.url != WEBHOOK_URL:
            # Удаляем старый webhook
            await bot.delete_webhook(drop_pending_updates=True)
            # Устанавливаем новый webhook
            await bot.set_webhook(WEBHOOK_URL)
            print("Webhook установлен ✅")
        else:
            print("Webhook уже установлен")
        # Запускаем scheduler
        scheduler.start()
        print("Scheduler запущен ✅")
    except Exception as e:
        print("Ошибка при старте бота:", e)
        traceback.print_exc()

async def on_shutdown(app: web.Application):
    print("Удаляем webhook и закрываем сессию")
    try:
        await bot.delete_webhook()
        await bot.session.close()
        scheduler.shutdown(wait=False)
    except Exception as e:
        print("Ошибка при shutdown:", e)
        traceback.print_exc()

# -------------------------------
# MAIN
# -------------------------------
def main():
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    app.router.add_get("/", health)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    print(f"Слушаем порт {PORT}...")
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
