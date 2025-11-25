from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ContentType
from states.homework_states import AddHomework
from handlers.start import get_main_keyboard
from datetime import datetime, timedelta, date
from database.db_session import SessionLocal
from database.db_operations import add_homework_to_db
import json

# Словарь для временного хранения файлов пользователя
user_files = {}

# Начинаем процесс добавления ДЗ
async def start_add_homework(message: types.Message):
    # Очищаем временные файлы пользователя
    user_id = message.from_user.id
    if user_id in user_files:
        del user_files[user_id]
    
    await message.answer("📝 Давайте добавим новое ДЗ!\n\n"
                        "На какую дату задано ДЗ?\n"
                        "Можешь написать в формате ДД.ММ.ГГГГ (например, 15.12.2025)\n"
                        "или просто 'завтра', 'послезавтра', 'через 2 дня'",
                        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Отмена")))
    await AddHomework.waiting_for_date.set()

# Обработка ввода даты
async def process_date(message: types.Message, state: FSMContext):
    date_text = message.text.lower()
    print(date_text)
    if date_text == "завтра":
        selected_date = datetime.now() + timedelta(days=1)
    elif date_text == "послезавтра":
        selected_date = datetime.now() + timedelta(days=2)
    match date_text:
        case "завтра":
            selected_date = datetime.now() + timedelta(days=1)
        case "послезавтра":
            selected_date = datetime.now() + timedelta(days=2)
        case "через 2 дня":
            selected_date = datetime.now() + timedelta(days=3)
        case "через 3 дня":
            selected_date = datetime.now() + timedelta(days=4)
        case "через 4 дня":
            selected_date = datetime.now() + timedelta(days=5)
        case "через 5 дней":
            selected_date = datetime.now() + timedelta(days=6)
        case "через 6 дней":
            selected_date = datetime.now() + timedelta(days=7)
        case "через 7 дней":
            selected_date = datetime.now() + timedelta(days=8)
        case "через 8 дней":
            selected_date = datetime.now() + timedelta(days=9)
        case "через 9 дней":
            selected_date = datetime.now() + timedelta(days=1)
        case "через 10 дней":
            selected_date = datetime.now() + timedelta(days=11)
        case _:
            try:
                selected_date = datetime.strptime(date_text, "%d.%m.%Y")
            except ValueError:
                await message.answer("❌ Неверный формат даты. Попробуй еще раз в формате ДД.ММ.ГГГГ")
                return
    
    await state.update_data(date_for=selected_date.strftime("%Y-%m-%d"))
    
    await message.answer(f"✅ Дата сохранена: {selected_date.strftime('%d.%m.%Y')}\n\n"
                        "Теперь введи название предмета:")
    await AddHomework.waiting_for_subject.set()

# Обработка ввода предмета
async def process_subject(message: types.Message, state: FSMContext):
    await state.update_data(subject=message.text)
    
    await message.answer("📝 Теперь введи текст задания:")
    await AddHomework.waiting_for_task.set()

# Обработка ввода задания
async def process_task(message: types.Message, state: FSMContext):
    await state.update_data(task=message.text)
    
    # Инициализируем список файлов для пользователя
    user_id = message.from_user.id
    user_files[user_id] = []
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Пропустить"))
    keyboard.add(KeyboardButton("Отмена"))
    
    await message.answer("📎 Хочешь прикрепить файл или фото к заданию?\n"
                        "Можешь отправить:\n"
                        "• Фото 📷\n"
                        "• Документ 📄\n"
                        "• Видео 🎥\n"
                        "• Аудио 🎵\n"
                        "• Голосовое сообщение 🎤\n\n"
                        "Или нажми 'Пропустить' чтобы продолжить без файлов",
                        reply_markup=keyboard)
    await AddHomework.waiting_for_attachment.set()

# Обработка текстовых команд в состоянии вложений
async def process_attachment_text(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    if message.text == "Пропустить":
        # Переходим к подтверждению
        await show_preview(message, state)
    
    elif message.text == "Завершить добавление файлов":
        # Сохраняем файлы в состоянии и переходим к подтверждению
        if user_id in user_files and user_files[user_id]:
            await state.update_data(attachments=user_files[user_id].copy())
        
        await show_preview(message, state)
        
        # Очищаем временные данные
        if user_id in user_files:
            del user_files[user_id]

# Обработка медиафайлов
async def process_attachment_media(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Создаем данные о файле
    file_data = {}
    
    if message.photo:
        # Берем фото самого высокого качества
        file_id = message.photo[-1].file_id
        file_data = {
            'type': 'photo',
            'file_id': file_id,
            'caption': message.caption or ''
        }
    
    elif message.document:
        file_data = {
            'type': 'document',
            'file_id': message.document.file_id,
            'file_name': message.document.file_name,
            'caption': message.caption or ''
        }
    
    elif message.video:
        file_data = {
            'type': 'video',
            'file_id': message.video.file_id,
            'caption': message.caption or ''
        }
    
    elif message.audio:
        file_data = {
            'type': 'audio',
            'file_id': message.audio.file_id,
            'caption': message.caption or ''
        }
    
    elif message.voice:
        file_data = {
            'type': 'voice',
            'file_id': message.voice.file_id
        }
    
    # Добавляем файл в список пользователя
    if user_id not in user_files:
        user_files[user_id] = []
    
    user_files[user_id].append(file_data)
    
    # Создаем клавиатуру с опциями
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Добавить еще файл"))
    keyboard.add(KeyboardButton("Завершить добавление файлов"))
    keyboard.add(KeyboardButton("Отмена"))
    
    files_count = len(user_files[user_id])
    file_type_emoji = {
        'photo': '📷',
        'document': '📄', 
        'video': '🎥',
        'audio': '🎵',
        'voice': '🎤'
    }
    
    await message.answer(
        f"✅ {file_type_emoji.get(file_data['type'], '📎')} Файл добавлен!\n"
        f"📁 Всего файлов: {files_count}\n\n"
        "Хочешь добавить еще файл или завершить?",
        reply_markup=keyboard
    )

# Показ превью и подтверждение (обновленная версия)
async def show_preview(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Получаем информацию о файлах
    attachments_info = ""
    attachments_count = 0
    
    user_id = message.from_user.id
    if user_id in user_files and user_files[user_id]:
        attachments_count = len(user_files[user_id])
        attachments_info = f"📎 Вложений: {attachments_count}\n"
        for i, file_data in enumerate(user_files[user_id], 1):
            file_type = file_data['type']
            type_names = {
                'photo': 'Фото',
                'document': 'Документ',
                'video': 'Видео', 
                'audio': 'Аудио',
                'voice': 'Голосовое'
            }
            attachments_info += f"  {i}. {type_names.get(file_type, file_type)}\n"
    else:
        attachments_info = "📎 Вложений: нет\n"
    
    preview_text = (
        "📋 Предпросмотр ДЗ:\n\n"
        f"📅 Дата: {datetime.strptime(data['date_for'], '%Y-%m-%d').strftime('%d.%m.%Y')}\n"
        f"📚 Предмет: {data['subject']}\n"
        f"📝 Задание: {data['task']}\n"
        f"{attachments_info}\n"
        "Всё верно? Подтверди добавление:"
    )
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("✅ Да, добавить"))
    keyboard.add(KeyboardButton("❌ Нет, отменить"))
    
    await message.answer(preview_text, reply_markup=keyboard)
    await AddHomework.waiting_for_confirmation.set()

# Подтверждение добавления (обновленная версия)
async def confirm_add_homework(message: types.Message, state: FSMContext):
    if message.text == "✅ Да, добавить":
        data = await state.get_data()
        
        # Сохраняем файлы из временного хранилища в состояние
        user_id = message.from_user.id
        if user_id in user_files and user_files[user_id]:
            data['attachments'] = user_files[user_id]
        
        # Сохраняем в БД
        db = SessionLocal()
        try:
            # Преобразуем строку даты в объект date
            date_for = datetime.strptime(data['date_for'], "%Y-%m-%d").date()
            
            # Преобразуем вложения в строку для БД
            attachment_data = None
            if 'attachments' in data and data['attachments']:
                attachment_data = json.dumps(data['attachments'])
            
            homework = add_homework_to_db(
                db=db,
                subject=data['subject'],
                task=data['task'],
                date_for=date_for,
                attachment_file_id=attachment_data
            )
            
            if homework:
                attachments_count = len(data.get('attachments', []))
                success_text = f"✅ ДЗ успешно добавлено в базу данных!"
                if attachments_count > 0:
                    success_text += f"\n📎 Прикреплено файлов: {attachments_count}"
                
                await message.answer(success_text, 
                                   reply_markup=get_main_keyboard(message.from_user.id))
            else:
                await message.answer("❌ Ошибка при добавлении ДЗ в базу", 
                                   reply_markup=get_main_keyboard(message.from_user.id))
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}", 
                               reply_markup=get_main_keyboard(message.from_user.id))
        finally:
            db.close()
            
        # Очищаем временные данные
        if user_id in user_files:
            del user_files[user_id]
            
    else:
        # Очищаем временные данные при отмене
        user_id = message.from_user.id
        if user_id in user_files:
            del user_files[user_id]
            
        await message.answer("❌ Добавление отменено", 
                           reply_markup=get_main_keyboard(message.from_user.id))
    
    await state.finish()

# Отмена процесса (обновленная версия)
async def cancel_add_homework(message: types.Message, state: FSMContext):
    # Очищаем временные данные
    user_id = message.from_user.id
    if user_id in user_files:
        del user_files[user_id]
        
    await message.answer("❌ Добавление ДЗ отменено", 
                       reply_markup=get_main_keyboard(message.from_user.id))
    await state.finish()