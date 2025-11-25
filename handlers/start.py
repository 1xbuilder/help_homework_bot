# handlers/start.py
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
# from config import ADMIN_IDS
from database.db_session import SessionLocal
from database.db_operations import get_user_by_telegram_id, create_user
from states.user_states import UserRegistration

# Временное хранилище для данных пользователей во время регистрации
temp_users = {}

def get_main_keyboard(user_id: int):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📚 Посмотреть ДЗ"))
    keyboard.add(KeyboardButton("❓ Помощь"))
    
    # if user_id in ADMIN_IDS:
    if True:
        keyboard.add(KeyboardButton("➕ Добавить ДЗ"))
        keyboard.add(KeyboardButton("❌ Удалить ДЗ"))
    
    return keyboard

async def process_start_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    db = SessionLocal()
    
    try:
        # Проверяем, есть ли пользователь в базе
        user = get_user_by_telegram_id(db, user_id)
        
        if user:
            # Пользователь уже зарегистрирован
            welcome_text = (
                f"С возвращением, {user.first_name}! 👋\n"
                f"Я бот для отслеживания домашних заданий.\n"
                f"Выбери нужную опцию в меню ниже:"
            )
            await message.answer(welcome_text, reply_markup=get_main_keyboard(user_id))
        else:
            # Новый пользователь - начинаем регистрацию
            welcome_text = (
                "Привет! 👋\n"
                "Я бот для отслеживания домашних заданий.\n"
                "Давай познакомимся! Как тебя зовут?"
            )
            
            # Сохраняем временные данные пользователя
            temp_users[user_id] = {
                'username': message.from_user.username,
                'tg_first_name': message.from_user.first_name,
                'tg_last_name': message.from_user.last_name
            }
            
            # Создаем клавиатуру с предложением использовать имя из Telegram
            if message.from_user.first_name:
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
                keyboard.add(KeyboardButton(f"Использовать '{message.from_user.first_name}'"))
                keyboard.add(KeyboardButton("Ввести другое имя"))
                
                await message.answer(
                    f"{welcome_text}\n\n"
                    f"Я вижу, что в Telegram тебя зовут {message.from_user.first_name}. "
                    f"Хочешь использовать это имя?",
                    reply_markup=keyboard
                )
            else:
                await message.answer(welcome_text)
            
            await UserRegistration.waiting_for_name.set()
            
    except Exception as e:
        await message.answer("❌ Произошла ошибка. Попробуй еще раз /start")
        print(f"Ошибка в process_start_command: {e}")
    finally:
        db.close()

async def process_user_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    db = SessionLocal()
    
    try:
        if user_id not in temp_users:
            await message.answer("❌ Что-то пошло не так. Напиши /start еще раз")
            await state.finish()
            return
        
        user_data = temp_users[user_id]
        first_name = ""
        
        if message.text.startswith("Использовать '"):
            # Пользователь выбрал имя из Telegram
            first_name = user_data['tg_first_name']
        elif message.text == "Ввести другое имя":
            await message.answer(
                "Хорошо! Напиши свое имя:",
                reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Отмена"))
            )
            return
        else:
            # Пользователь ввел свое имя
            if message.text == "Отмена":
                await message.answer("Регистрация отменена. Напиши /start чтобы начать заново.")
                if user_id in temp_users:
                    del temp_users[user_id]
                await state.finish()
                return
            
            first_name = message.text.strip()
            if len(first_name) < 2:
                await message.answer("❌ Имя слишком короткое. Введите имя еще раз:")
                return
        
        # Создаем пользователя в базе
        new_user = create_user(
            db=db,
            telegram_id=user_id,
            username=user_data['username'],
            first_name=first_name,
            last_name=user_data['tg_last_name']
        )
        
        if new_user:
            welcome_text = (
                f"Отлично, {first_name}! 🎉\n"
                f"Теперь ты зарегистрирован в системе.\n\n"
                f"Что я умею:\n"
                f"• 📚 Показывать домашние задания\n"
                f"• ➕ Добавлять новые ДЗ (для администраторов)\n"
                f"• ❌ Удалять ДЗ (для администраторов)\n\n"
                f"Выбери нужную опцию в меню ниже:"
            )
            await message.answer(welcome_text, reply_markup=get_main_keyboard(user_id))
        else:
            await message.answer("❌ Ошибка при регистрации. Попробуй /start еще раз")
        
        # Очищаем временные данные и состояние
        if user_id in temp_users:
            del temp_users[user_id]
        await state.finish()
        
    except Exception as e:
        await message.answer("❌ Произошла ошибка. Попробуй еще раз")
        print(f"Ошибка в process_user_name: {e}")
    finally:
        db.close()

# Функция для получения информации о пользователе (для других модулей)
def get_user_info(user_id: int):
    db = SessionLocal()
    try:
        user = get_user_by_telegram_id(db, user_id)
        if user:
            return {
                'id': user.id,
                'first_name': user.first_name,
                'username': user.username
            }
        return None
    finally:
        db.close()