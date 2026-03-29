from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_IDS
from database.db_session import supabase
from database.db_operations import get_user_by_telegram_id, create_user, update_user_subgroup
from states.user_states import UserRegistration

temp_users = {}

def get_main_keyboard(user_id: int):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📚 Посмотреть ДЗ"))
    keyboard.add(KeyboardButton("❓ Помощь"))
    keyboard.add(KeyboardButton("➕ Добавить ДЗ"))
    keyboard.add(KeyboardButton("❌ Удалить ДЗ"))
    return keyboard

def subgroup_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("1 подгруппа"), KeyboardButton("2 подгруппа"))
    return kb

async def process_start_command(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    try:
        user = get_user_by_telegram_id(telegram_id=user_id)
        if user:
            # Уже зарегистрирован — проверяем подгруппу
            if not user.subgroup:
                await message.answer(
                    f"С возвращением, {user.first_name}! 👋\n\n"
                    "Для точного расписания укажи свою подгруппу:",
                    reply_markup=subgroup_keyboard()
                )
                await UserRegistration.waiting_for_subgroup.set()
            else:
                await message.answer(
                    f"С возвращением, {user.first_name}! 👋\n"
                    f"Подгруппа: {user.subgroup}\n\nВыбери нужную опцию:",
                    reply_markup=get_main_keyboard(user_id)
                )
        else:
            temp_users[user_id] = {
                'username': message.from_user.username,
                'tg_first_name': message.from_user.first_name,
                'tg_last_name': message.from_user.last_name
            }
            welcome = "Привет! 👋 Я бот для отслеживания домашних заданий.\nКак тебя зовут?"
            if message.from_user.first_name:
                kb = ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add(KeyboardButton(f"Использовать '{message.from_user.first_name}'"))
                kb.add(KeyboardButton("Ввести другое имя"))
                await message.answer(
                    f"{welcome}\n\nВижу тебя зовут {message.from_user.first_name}. Использовать это имя?",
                    reply_markup=kb
                )
            else:
                await message.answer(welcome)
            await UserRegistration.waiting_for_name.set()
    except Exception as e:
        await message.answer("❌ Ошибка. Попробуй ещё раз /start")
        print(f"Ошибка start: {e}")

async def process_user_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        if user_id not in temp_users:
            await message.answer("❌ Что-то пошло не так. Напиши /start ещё раз")
            await state.finish()
            return

        user_data = temp_users[user_id]
        if message.text == "Отмена":
            del temp_users[user_id]
            await state.finish()
            return
        elif message.text.startswith("Использовать '"):
            first_name = user_data['tg_first_name']
        elif message.text == "Ввести другое имя":
            kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Отмена"))
            await message.answer("Напиши своё имя:", reply_markup=kb)
            return
        else:
            first_name = message.text.strip()
            if len(first_name) < 2:
                await message.answer("❌ Имя слишком короткое. Попробуй ещё раз:")
                return

        temp_users[user_id]['first_name'] = first_name

        # Спрашиваем подгруппу
        await message.answer(
            f"Отлично, {first_name}! 🎉\n\nТеперь укажи свою подгруппу:",
            reply_markup=subgroup_keyboard()
        )
        await UserRegistration.waiting_for_subgroup.set()

    except Exception as e:
        await message.answer("❌ Ошибка. Попробуй /start")
        print(f"Ошибка name: {e}")

async def process_user_subgroup(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()

    if "1" in text:
        subgroup = "1"
    elif "2" in text:
        subgroup = "2"
    else:
        await message.answer("Выбери: 1 подгруппа или 2 подгруппа", reply_markup=subgroup_keyboard())
        return

    try:
        user = get_user_by_telegram_id(telegram_id=user_id)

        if user:
            # Обновляем подгруппу существующего пользователя
            update_user_subgroup(telegram_id=user_id, subgroup=subgroup)
            await message.answer(
                f"✅ Подгруппа {subgroup} сохранена!",
                reply_markup=get_main_keyboard(user_id)
            )
        else:
            # Новый пользователь — создаём
            user_data = temp_users.get(user_id, {})
            first_name = user_data.get('first_name', message.from_user.first_name or 'Пользователь')
            new_user = create_user(
                telegram_id=user_id,
                username=user_data.get('username', message.from_user.username),
                first_name=first_name,
                last_name=user_data.get('tg_last_name', message.from_user.last_name)
            )
            if new_user:
                update_user_subgroup(telegram_id=user_id, subgroup=subgroup)
                await message.answer(
                    f"Готово, {first_name}! Подгруппа {subgroup} сохранена. 🎉\n\n"
                    "Теперь расписание будет показываться по твоей подгруппе.",
                    reply_markup=get_main_keyboard(user_id)
                )
            else:
                await message.answer("❌ Ошибка при регистрации. Попробуй /start")
                await state.finish()
                return

        if user_id in temp_users:
            del temp_users[user_id]
        await state.finish()

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        print(f"Ошибка subgroup: {e}")

async def check_subgroup(message: types.Message) -> bool:
    """Проверяет наличие подгруппы. Возвращает True если всё ок, False если нужно заполнить."""
    user = get_user_by_telegram_id(telegram_id=message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйся — напиши /start")
        return False
    if not user.subgroup:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("1 подгруппа"), KeyboardButton("2 подгруппа"))
        await message.answer(
            "⚠️ Для точного расписания нужно указать подгруппу.\nВыбери свою подгруппу:",
            reply_markup=kb
        )
        return False
    return True

def get_user_info(user_id: int):
    try:
        user = get_user_by_telegram_id(telegram_id=user_id)
        if user:
            return {'id': user.id, 'first_name': user.first_name, 'username': user.username, 'subgroup': user.subgroup}
        return None
    except Exception as e:
        print(f"Ошибка get_user_info: {e}")
        return None
