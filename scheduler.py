from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from sheets_api import get_all_users
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
scheduler = AsyncIOScheduler()


# ====== Уведомления ======
async def send_start_work_notification():
    users = [u for u in get_all_users() if u["role"] == "employee"]
    for user in users:
        await bot.send_message(user["user_id"], "Доброе утро! Не забудьте отметить начало работы.")


async def send_end_work_notification():
    users = [u for u in get_all_users() if u["role"] == "employee"]
    for user in users:
        await bot.send_message(user["user_id"], "Время заканчивать работу! Не забудьте составить Daily Report.")


# ====== Синхронный запуск scheduler (старый вариант) ======
def start_scheduler():
    scheduler.add_job(lambda: asyncio.create_task(send_start_work_notification()), 
                      'cron', day_of_week='mon-fri', hour=8, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(send_end_work_notification()), 
                      'cron', day_of_week='mon-fri', hour=16, minute=0)
    scheduler.start()


# ====== Асинхронный запуск scheduler для bot.py ======
async def start_scheduler_async():
    scheduler.add_job(send_start_work_notification, 'cron', day_of_week='mon-fri', hour=8, minute=0)
    scheduler.add_job(send_end_work_notification, 'cron', day_of_week='mon-fri', hour=16, minute=0)
    scheduler.start()
