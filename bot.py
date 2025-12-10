import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from aiohttp import web

from sheets_api import (
    get_user,
    get_all_users,
    check_in,
    check_out,
    get_tasks,
    create_daily_report,
    get_reports_for_admin
)

from scheduler import start_scheduler_async   # используем async scheduler

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = os.getenv("WEBHOOK_URL") + WEBHOOK_PATH

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========================== Reply клавиатуры ==========================
def admin_bottom_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пользователи"), KeyboardButton(text="Задачи")],
            [KeyboardButton(text="Отчеты"), KeyboardButton(text="Начало работы")],
            [KeyboardButton(text="Конец работы")]
        ],
        resize_keyboard=True
    )

def user_bottom_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мои задачи"), KeyboardButton(text="Создать отчет")],
            [KeyboardButton(text="Начало работы"), KeyboardButton(text="Конец работы")]
        ],
        resize_keyboard=True
    )

# ========================== Команда /start ==========================
@dp.message(Command("start"))
async def start(message: types.Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Вы не зарегистрированы. Обратитесь к администратору.")
        return

    text = f"Привет, {user['name']}! Ваша роль: {user['role']}"
    if user["role"] == "admin":
        await message.answer(text, reply_markup=admin_bottom_menu())
    else:
        await message.answer(text, reply_markup=user_bottom_menu())

# ========================== Обработка текста ==========================
@dp.message()
async def handle_text(message: types.Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Вы не зарегистрированы.")
        return

    text = message.text

    try:
        # ================= Начало работы =================
        if text == "Начало работы":
            if check_in(user["user_id"]):
                await message.answer("Вы отметились как начавший работу.")
            else:
                await message.answer("Вы уже отметились сегодня.")
            return

        # ================= Конец работы =================
        if text == "Конец работы":
            if check_out(user["user_id"]):
                await message.answer("Вы отметились как закончивший работу.")
            else:
                await message.answer("Вы ещё не начали работу или уже отметились.")
            return

        # ================= Пользователи =================
        if text == "Пользователи":
            if user["role"] != "admin":
                await message.answer("Доступ только для админов.")
                return
            users = get_all_users()
            resp = "Список пользователей:\n"
            for u in users:
                resp += f"{u['user_id']}: {u['name']} ({u['role']})\n"
            await message.answer(resp)
            return

        # ================= Задачи =================
        if text == "Задачи":
            if user["role"] != "admin":
                await message.answer("Доступ только для админов.")
                return
            tasks = get_tasks(None)
            resp = "Список задач:\n"
            for t in tasks:
                resp += (
                    f"{t['task_id']}: {t['title']} - {t['status']} "
                    f"| Исполнители: {t.get('assigned_to', 'не назначен')}\n"
                )
            await message.answer(resp)
            return

        # ================= Мои задачи =================
        if text == "Мои задачи":
            tasks = get_tasks(user["user_id"])
            resp = "Ваши задачи:\n"
            for t in tasks:
                resp += (
                    f"{t['task_id']}: {t['title']} - {t['status']} "
                    f"| Исполнители: {t.get('assigned_to', 'не назначен')}\n"
                )
            await message.answer(resp)
            return

        # ================= Отчёты =================
        if text == "Отчеты":
            if user["role"] != "admin":
                await message.answer("Доступ только для админов.")
                return

            reports = get_reports_for_admin()
            if not reports:
                await message.answer("Нет отчетов на согласование.")
                return

            resp = "Отчеты на согласование:\n"
            for r in reports:
                resp += (
                    f"ID: {r['report_id']} | Пользователь: {r['user_id']} | Дата: {r['date']}\n"
                    f"Задачи: {r['tasks_done']}\n"
                    f"Проблемы: {r['problems']}\n\n"
                )
            await message.answer(resp)
            return

        if text == "Создать отчет":
            await message.answer(
                "Введите отчет в формате:\n"
                "task_ids | problems\n"
                "Пример:\n"
                "1,2 | баг в меню"
            )
            return

        # ================= Создание отчёта =================
        if "|" in text:
            task_ids_str, problems = text.split("|")
            task_ids = [int(tid.strip()) for tid in task_ids_str.split(",")]

            report_id = create_daily_report(
                user_id=user["user_id"],
                task_ids=task_ids,
                problems=problems.strip()
            )

            await message.answer(
                f"Daily Report создан и отправлен на согласование! ID: {report_id}"
            )

    except Exception as e:
        await message.answer(f"Ошибка: {e}")

# ========================== Webhook ==========================
async def handle_webhook(request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot, update)
    return web.Response()

# ========================== Heartbeat ==========================
async def heartbeat():
    while True:
        print("❤️ Bot alive on Render")
        await asyncio.sleep(120)

# ========================== Startup ==========================
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    await start_scheduler_async()
    asyncio.create_task(heartbeat())
    print("Бот запущен!")

async def on_shutdown(app):
    await bot.delete_webhook()
    print("Бот остановлен")

# ========================== AIOHTTP App ==========================
app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
