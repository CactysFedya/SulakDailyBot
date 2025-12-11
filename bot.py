import asyncio
from aiogram import Bot, Dispatcher, types, F
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Твой токен
CHAT_ID = os.getenv("CHAT_ID")      # Твой Telegram ID или ID группы

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Команда /start
    @dp.message(F.text == "/start")
    async def cmd_start(message: types.Message):
        await message.answer("Привет! Я тестовый бот с уведомлениями каждые 10 минут 😊")

    # Команда /ping
    @dp.message(F.text == "/ping")
    async def cmd_ping(message: types.Message):
        await message.answer("Pong!")

    # Настройка планировщика
    scheduler = AsyncIOScheduler()

    async def send_notification():
        try:
            await bot.send_message(CHAT_ID, "Это тестовое уведомление от бота 🚀")
        except Exception as e:
            print(f"Ошибка при отправке уведомления: {e}")

    # Запуск уведомлений каждые 10 минут
    scheduler.add_job(send_notification, 'interval', minutes=10)
    scheduler.start()

    # Запуск polling
    async def on_startup():
        print("Бот запущен...")

    async def on_shutdown():
        await bot.session.close()
        print("Бот остановлен")

    await dp.start_polling(bot, on_startup=on_startup, on_shutdown=on_shutdown)

if name == "__main__":
    asyncio.run(main())
