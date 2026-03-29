# database/db_operations.py
from database.db_session import supabase
from datetime import date, datetime, timedelta
import json


# DTO-класс — имитирует ORM-объект, чтобы не менять handlers
class HomeworkDTO:
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.subject = data.get('subject', '')
        self.task = data.get('task', '')
        raw_date = data.get('date_for')
        if isinstance(raw_date, str):
            self.date_for = date.fromisoformat(raw_date)
        else:
            self.date_for = raw_date
        self.attachment_file_id = data.get('attachment_file_id')
        self.attachment_type = data.get('attachment_type')
        self.created_at = data.get('created_at')


class UserDTO:
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.username = data.get('username')
        self.first_name = data.get('first_name', '')
        self.last_name = data.get('last_name')
        self.subgroup = data.get('subgroup')
        self.created_at = data.get('created_at')


# ── Homework операции ──────────────────────────────────────────────────────────

def add_homework_to_db(db=None, subject='', task='', date_for=None, attachment_file_id=None):
    try:
        if attachment_file_id and isinstance(attachment_file_id, list):
            attachment_file_id = json.dumps(attachment_file_id, ensure_ascii=False)
        data = {
            "subject": subject,
            "task": task,
            "date_for": str(date_for),
            "attachment_file_id": attachment_file_id,
        }
        result = supabase.table("homeworks").insert(data).execute()
        if result.data:
            return HomeworkDTO(result.data[0])
        return None
    except Exception as e:
        print(f"Ошибка при добавлении ДЗ: {e}")
        return None


def get_homework_by_date(db=None, target_date=None):
    try:
        result = supabase.table("homeworks").select("*").eq("date_for", str(target_date)).execute()
        return [HomeworkDTO(r) for r in result.data]
    except Exception as e:
        print(f"Ошибка при получении ДЗ: {e}")
        return []


def get_today_homework(db=None):
    return get_homework_by_date(target_date=date.today())


def get_tomorrow_homework(db=None):
    return get_homework_by_date(target_date=date.today() + timedelta(days=1))


def get_week_homework(db=None):
    try:
        today = date.today()
        end = today + timedelta(days=7)
        result = supabase.table("homeworks").select("*") \
            .gte("date_for", str(today)) \
            .lte("date_for", str(end)) \
            .order("date_for").execute()
        return [HomeworkDTO(r) for r in result.data]
    except Exception as e:
        print(f"Ошибка при получении ДЗ на неделю: {e}")
        return []


def get_homework_for_week(db=None, start_date=None):
    try:
        end = start_date + timedelta(days=6)
        result = supabase.table("homeworks").select("*") \
            .gte("date_for", str(start_date)) \
            .lte("date_for", str(end)) \
            .order("date_for").execute()
        return [HomeworkDTO(r) for r in result.data]
    except Exception as e:
        print(f"Ошибка при получении ДЗ на неделю: {e}")
        return []


def get_all_homeworks(db=None):
    try:
        result = supabase.table("homeworks").select("*").order("date_for", desc=True).execute()
        return [HomeworkDTO(r) for r in result.data]
    except Exception as e:
        print(f"Ошибка при получении всех ДЗ: {e}")
        return []


def delete_homework(db=None, homework_id=None):
    try:
        result = supabase.table("homeworks").delete().eq("id", homework_id).execute()
        return True
    except Exception as e:
        print(f"Ошибка при удалении ДЗ: {e}")
        return False


def get_homework_by_id(db=None, homework_id=None):
    try:
        result = supabase.table("homeworks").select("*").eq("id", homework_id).execute()
        if result.data:
            return HomeworkDTO(result.data[0])
        return None
    except Exception as e:
        print(f"Ошибка при получении ДЗ по ID: {e}")
        return None


def update_homework(db=None, homework_id=None, subject=None, task=None, date_for=None, attachment_file_id=None):
    try:
        updates = {"updated_at": datetime.now().isoformat()}
        if subject is not None:
            updates["subject"] = subject
        if task is not None:
            updates["task"] = task
        if date_for is not None:
            updates["date_for"] = str(date_for)
        if attachment_file_id is not None:
            if isinstance(attachment_file_id, list):
                attachment_file_id = json.dumps(attachment_file_id, ensure_ascii=False)
            updates["attachment_file_id"] = attachment_file_id
        result = supabase.table("homeworks").update(updates).eq("id", homework_id).execute()
        if result.data:
            return HomeworkDTO(result.data[0])
        return None
    except Exception as e:
        print(f"Ошибка при обновлении ДЗ: {e}")
        return None


def get_attachments_from_homework(homework):
    if homework.attachment_file_id:
        try:
            return json.loads(homework.attachment_file_id)
        except:
            return []
    return []


# ── User операции ──────────────────────────────────────────────────────────────

def get_user_by_telegram_id(db=None, telegram_id=None):
    try:
        result = supabase.table("users").select("*").eq("user_id", telegram_id).execute()
        if result.data:
            return UserDTO(result.data[0])
        return None
    except Exception as e:
        print(f"Ошибка при получении пользователя: {e}")
        return None


def create_user(db=None, telegram_id=None, username=None, first_name=None, last_name=None):
    try:
        data = {
            "user_id": telegram_id,
            "username": username,
            "first_name": first_name or "",
            "last_name": last_name,
        }
        result = supabase.table("users").insert(data).execute()
        if result.data:
            return UserDTO(result.data[0])
        return None
    except Exception as e:
        print(f"Ошибка при создании пользователя: {e}")
        return None


def update_user_subgroup(db=None, telegram_id=None, subgroup=None):
    try:
        result = supabase.table("users").update({"subgroup": subgroup}).eq("user_id", telegram_id).execute()
        if result.data:
            return UserDTO(result.data[0])
        return None
    except Exception as e:
        print(f"Ошибка при обновлении подгруппы: {e}")
        return None
