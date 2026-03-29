# database/db_session.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Строка подключения к Supabase PostgreSQL.
# Берётся из переменной окружения DATABASE_URL в файле .env
# Формат: postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise RuntimeError("Переменная DATABASE_URL не задана в .env файле!")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Создаёт таблицы если их ещё нет (безопасно при повторных запусках)
Base.metadata.create_all(bind=engine)

print(f"✅ Подключено к Supabase PostgreSQL")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
