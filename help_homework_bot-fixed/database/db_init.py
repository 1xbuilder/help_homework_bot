# init_db.py
from db_session import engine
from models import Base

print("Создаем таблицы в БД...")
Base.metadata.create_all(bind=engine)
print("Таблицы успешно созданы!")