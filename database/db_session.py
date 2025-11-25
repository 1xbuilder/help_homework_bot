# database/db_session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Создаем движок БД
engine = create_engine('sqlite:///homework_bot.db', echo=True)
SessionLocal = sessionmaker(bind=engine)

# Создаем таблицы
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()