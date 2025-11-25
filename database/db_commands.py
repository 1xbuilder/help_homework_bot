from sqlalchemy.orm import sessionmaker
from database.models import Homework, engine

# Создаем сессию для работы с БД
Session = sessionmaker(bind=engine)

async def add_homework(subject_name, task_text, date_for, attachment_file_id=None):
    session = Session()
    try:
        new_homework = Homework(
            subject_name=subject_name,
            task_text=task_text,
            date_for=date_for,
            attachment_file_id=attachment_file_id
        )
        session.add(new_homework)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        return False
    finally:
        session.close()

async def get_homework_by_date(date):
    session = Session()
    try:
        homeworks = session.query(Homework).filter(Homework.date_for == date).all()
        return homeworks
    finally:
        session.close()