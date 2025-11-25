# database/models.py
from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Homework(Base):
    __tablename__ = 'homeworks'
    
    id = Column(Integer, primary_key=True)
    subject = Column(String(100), nullable=False)
    task = Column(Text, nullable=False)
    date_for = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    attachment_file_id = Column(String(255), nullable=True)
    attachment_type = Column(String(20), nullable=True)
    
    def __repr__(self):
        return f"Homework(id={self.id}, subject='{self.subject}', date_for='{self.date_for}')"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)  # Telegram ID пользователя
    username = Column(String(100), nullable=True)  # Юзернейм в Telegram
    first_name = Column(String(100), nullable=False)  # Имя пользователя
    last_name = Column(String(100), nullable=True)  # Фамилия пользователя
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"User(id={self.id}, user_id={self.user_id}, first_name='{self.first_name}')"