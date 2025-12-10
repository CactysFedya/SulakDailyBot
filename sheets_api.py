import os
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SERVICE_ACCOUNT_INFO = json.loads(os.getenv("GOOGLE_CREDS_JSON"))

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(SERVICE_ACCOUNT_INFO, scope)
client = gspread.authorize(creds)

USERS_SHEET = client.open("SulakBotDB").worksheet("Users")
TASKS_SHEET = client.open("SulakBotDB").worksheet("Tasks")
REPORTS_SHEET = client.open("SulakBotDB").worksheet("Reports")
WORKLOG_SHEET = client.open("SulakBotDB").worksheet("WorkLog")

# ========================== Пользователи ==========================
def get_user(user_id):
    records = USERS_SHEET.get_all_records()
    for u in records:
        if str(u["user_id"]) == str(user_id):
            return u
    return None

def get_all_users():
    return USERS_SHEET.get_all_records()

# ========================== Отметки работы ==========================
def check_in(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    logs = WORKLOG_SHEET.get_all_records()
    for log in logs:
        if str(log["user_id"]) == str(user_id) and log["date"] == today:
            return False  # Уже отметился
    WORKLOG_SHEET.append_row([len(logs)+1, user_id, today, datetime.now().strftime("%H:%M"), ""])
    return True

def check_out(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    logs = WORKLOG_SHEET.get_all_records()
    for i, log in enumerate(logs):
        if str(log["user_id"]) == str(user_id) and log["date"] == today:
            if log["check_out"]:
                return False
            WORKLOG_SHEET.update_cell(i+2, 5, datetime.now().strftime("%H:%M"))
            return True
    return False

# ========================== Задачи ==========================
def get_tasks(user_id=None):
    records = TASKS_SHEET.get_all_records()
    if user_id:
        return [t for t in records if str(user_id) in str(t["assigned_to"]).split(",")]
    return records

def add_task(title, description, assigned_to, creator_id):
    tasks = TASKS_SHEET.get_all_records()
    task_id = len(tasks)+1
    TASKS_SHEET.append_row([task_id, title, description, assigned_to, "in_progress", datetime.now().strftime("%Y-%m-%d"), "False"])
    return task_id

def update_task_status(task_id, status):
    tasks = TASKS_SHEET.get_all_records()
    for i, t in enumerate(tasks):
        if t["task_id"] == task_id:
            TASKS_SHEET.update_cell(i+2, 5, status)
            return True
    return False

# ========================== Reports ==========================
def create_daily_report(user_id, task_ids, tasks_done_details, problems, plan):
    records = REPORTS_SHEET.get_all_records()
    report_id = len(records)+1
    REPORTS_SHEET.append_row([
        report_id,
        user_id,
        datetime.now().strftime("%Y-%m-%d"),
        ",".join(map(str, task_ids)),
        tasks_done_details,
        problems,
        plan,
        "pending"
    ])
    return report_id

def get_reports_for_admin():
    records = REPORTS_SHEET.get_all_records()
    return [r for r in records if r["status"] == "pending"]

def approve_report(report_id):
    records = REPORTS_SHEET.get_all_records()
    for i, r in enumerate(records):
        if r["report_id"] == report_id:
            REPORTS_SHEET.update_cell(i+2, 8, "approved")
            return True
    return False
