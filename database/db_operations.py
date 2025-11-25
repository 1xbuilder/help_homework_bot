# database/db_operations.py
from sqlalchemy.orm import Session
from database.models import Homework
from datetime import datetime, date, timedelta
import json

# Добавление ДЗ в БД (обновленная версия с поддержкой JSON файлов)
def add_homework_to_db(db: Session, subject: str, task: str, date_for: date, attachment_file_id: str = None):
    try:
        # Если attachment_file_id является списком (файлы), преобразуем в JSON
        if attachment_file_id and isinstance(attachment_file_id, list):
            attachment_file_id = json.dumps(attachment_file_id, ensure_ascii=False)
        
        new_homework = Homework(
            subject=subject,
            task=task,
            date_for=date_for,
            attachment_file_id=attachment_file_id,
            created_at=datetime.now()
        )
        db.add(new_homework)
        db.commit()
        db.refresh(new_homework)
        return new_homework
    except Exception as e:
        db.rollback()
        print(f"Ошибка при добавлении ДЗ: {e}")
        return None

# Получение ДЗ на конкретную дату
def get_homework_by_date(db: Session, target_date: date):
    try:
        homeworks = db.query(Homework).filter(Homework.date_for == target_date).all()
        return homeworks
    except Exception as e:
        print(f"Ошибка при получении ДЗ: {e}")
        return []

# Получение ДЗ на сегодня
def get_today_homework(db: Session):
    try:
        today = date.today()
        homeworks = db.query(Homework).filter(Homework.date_for == today).all()
        return homeworks
    except Exception as e:
        print(f"Ошибка при получении ДЗ на сегодня: {e}")
        return []

# Получение ДЗ на завтра
def get_tomorrow_homework(db: Session):
    try:
        tomorrow = date.today() + timedelta(days=1)
        homeworks = db.query(Homework).filter(Homework.date_for == tomorrow).all()
        return homeworks
    except Exception as e:
        print(f"Ошибка при получении ДЗ на завтра: {e}")
        return []

# Получение ДЗ на неделю (текущую, начиная с сегодня)
def get_week_homework(db: Session):
    try:
        today = date.today()
        end_date = today + timedelta(days=7)
        homeworks = db.query(Homework).filter(
            Homework.date_for >= today,
            Homework.date_for <= end_date
        ).order_by(Homework.date_for).all()
        return homeworks
    except Exception as e:
        print(f"Ошибка при получении ДЗ на неделю: {e}")
        return []

# Получение ДЗ на неделю от определенной даты (твоя оригинальная функция)
def get_homework_for_week(db: Session, start_date: date):
    end_date = start_date + timedelta(days=6)
    try:
        homeworks = db.query(Homework).filter(
            Homework.date_for >= start_date,
            Homework.date_for <= end_date
        ).order_by(Homework.date_for).all()
        return homeworks
    except Exception as e:
        print(f"Ошибка при получении ДЗ на неделю: {e}")
        return []

# Получение всех ДЗ (для админов)
def get_all_homeworks(db: Session):
    try:
        homeworks = db.query(Homework).order_by(Homework.date_for.desc()).all()
        return homeworks
    except Exception as e:
        print(f"Ошибка при получении всех ДЗ: {e}")
        return []

# Удаление ДЗ по ID
def delete_homework(db: Session, homework_id: int):
    try:
        homework = db.query(Homework).filter(Homework.id == homework_id).first()
        if homework:
            db.delete(homework)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Ошибка при удалении ДЗ: {e}")
        return False

# Получение ДЗ по ID
def get_homework_by_id(db: Session, homework_id: int):
    try:
        homework = db.query(Homework).filter(Homework.id == homework_id).first()
        return homework
    except Exception as e:
        print(f"Ошибка при получении ДЗ по ID: {e}")
        return None

# Обновление ДЗ
def update_homework(db: Session, homework_id: int, subject: str = None, task: str = None, date_for: date = None, attachment_file_id: str = None):
    try:
        homework = db.query(Homework).filter(Homework.id == homework_id).first()
        if homework:
            if subject is not None:
                homework.subject = subject
            if task is not None:
                homework.task = task
            if date_for is not None:
                homework.date_for = date_for
            if attachment_file_id is not None:
                # Если attachment_file_id является списком, преобразуем в JSON
                if isinstance(attachment_file_id, list):
                    attachment_file_id = json.dumps(attachment_file_id, ensure_ascii=False)
                homework.attachment_file_id = attachment_file_id
            
            homework.updated_at = datetime.now()
            db.commit()
            db.refresh(homework)
            return homework
        return None
    except Exception as e:
        db.rollback()
        print(f"Ошибка при обновлении ДЗ: {e}")
        return None

# Функция для получения файлов из JSON
def get_attachments_from_homework(homework):
    """
    Извлекает список файлов из объекта домашнего задания
    """
    if homework.attachment_file_id:
        try:
            return json.loads(homework.attachment_file_id)
        except:
            return []
    return []
from database.models import User

# Функции для работы с пользователями
def get_user_by_telegram_id(db: Session, telegram_id: int):
    try:
        user = db.query(User).filter(User.user_id == telegram_id).first()
        return user
    except Exception as e:
        print(f"Ошибка при получении пользователя: {e}")
        return None

def create_user(db: Session, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None):
    try:
        new_user = User(
            user_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        print(f"Ошибка при создании пользователя: {e}")
        return None