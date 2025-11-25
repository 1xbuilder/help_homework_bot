# Импорты вспомогательных библиотек
import asyncio
import logging
import sqlite3
import random 
import os

# Импорты основных библиотек aiogram
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

# Импорты вспомогательных библиотек aiogram
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import ContentType
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Импорты файлов
from config import TOKEN

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

from handlers.start import process_start_command, get_main_keyboard, process_user_name
from handlers.homework import show_homework_menu, back_to_main_menu, show_date_selection, show_today_homework, show_tomorrow_homework, show_week_homework
from handlers.admin_handlers import show_help_menu, how_working_bot, find_mistacke_bot, Wanna_create_homework, write_me
from handlers.calendar_handlers import handle_calendar_callback, show_date_selection
from handlers.add_homework import (
    start_add_homework, process_date, process_subject, process_task, 
    process_attachment_text, process_attachment_media, confirm_add_homework, cancel_add_homework
)
from handlers.delete_homework import start_delete_homework,process_date_selection, process_homework_selection, confirm_deletion
from states.homework_states import AddHomework
from states.user_states import UserRegistration
from states.delete_states import DeleteHomework

# Обработчик команды /start
dp.register_message_handler(process_start_command, commands=['start'])

# Обработчики главного меню
dp.register_message_handler(show_homework_menu, lambda message: message.text == "📚 Посмотреть ДЗ")
dp.register_message_handler(start_add_homework, lambda message: message.text == "➕ Добавить ДЗ")
dp.register_message_handler(start_delete_homework, lambda message: message.text == "❌ Удалить ДЗ")

# Обработчики раздела помощи
dp.register_message_handler(show_help_menu, lambda message: message.text == "❓ Помощь")
dp.register_message_handler(how_working_bot, lambda message: message.text == "ℹ️ Как работает бот?")
dp.register_message_handler(find_mistacke_bot, lambda message: message.text == "🐛 Нашел ошибку")
dp.register_message_handler(Wanna_create_homework, lambda message: message.text == "👨‍💼 Хочу заполнять ДЗ")
dp.register_message_handler(write_me, lambda message: message.text == "💬 Написать в поддержку")

# Обработчики просмотра ДЗ
dp.register_message_handler(show_today_homework, lambda message: message.text == "Сегодня")
dp.register_message_handler(show_tomorrow_homework, lambda message: message.text == "Завтра")
dp.register_message_handler(show_date_selection, lambda message: message.text == "Выбрать дату")

# Обработчики для удаления ДЗ
dp.register_message_handler(start_delete_homework, lambda message: message.text == "❌ Удалить ДЗ", state="*")
dp.register_message_handler(process_date_selection, state=DeleteHomework.waiting_for_date_selection)
dp.register_message_handler(process_homework_selection, state=DeleteHomework.waiting_for_homework_selection)
dp.register_message_handler(confirm_deletion, state=DeleteHomework.waiting_for_confirmation)

# Обработчик календаря
dp.register_callback_query_handler(handle_calendar_callback, lambda c: c.data.startswith(('calendar_', 'date_select_', 'ignore')))

# Обработчики для добавления ДЗ (FSM)
dp.register_message_handler(cancel_add_homework, lambda message: message.text == "Отмена", state="*")
dp.register_message_handler(process_date, state=AddHomework.waiting_for_date)
dp.register_message_handler(process_subject, state=AddHomework.waiting_for_subject)
dp.register_message_handler(process_task, state=AddHomework.waiting_for_task)

# Обработчики для файлов в процессе добавления ДЗ
dp.register_message_handler(
    process_attachment_text, 
    lambda message: message.text in ["Пропустить", "Завершить добавление файлов"],
    state=AddHomework.waiting_for_attachment
)

dp.register_message_handler(
    process_attachment_media, 
    content_types=[ContentType.PHOTO, ContentType.DOCUMENT, ContentType.VIDEO, ContentType.AUDIO, ContentType.VOICE],
    state=AddHomework.waiting_for_attachment
)

dp.register_message_handler(confirm_add_homework, state=AddHomework.waiting_for_confirmation)

# Обработчик для регистрации пользователя
dp.register_message_handler(process_user_name, state=UserRegistration.waiting_for_name)

# Обработчик возврата в главное меню
dp.register_message_handler(back_to_main_menu, lambda message: message.text == "🔙 Назад")
dp.register_message_handler(back_to_main_menu, lambda message: message.text == "Назад")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Бот запущен...")
    executor.start_polling(dp, skip_updates=True)