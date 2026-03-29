import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise RuntimeError("Переменная DATABASE_URL не задана!")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

print(f"✅ Подключено к Supabase PostgreSQL")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
