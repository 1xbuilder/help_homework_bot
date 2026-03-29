from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ContentType
from states.homework_states import AddHomework
from handlers.start import get_main_keyboard
from datetime import datetime, timedelta, date
from database.db_operations import add_homework_to_db
import json

# Начинаем процесс добавления ДЗ
async def start_add_homework(message: types.Message, state: FSMContext):
    await state.finish()  # сбрасываем старое состояние если было
    await message.answer(
        "📝 Давайте добавим новое ДЗ!\n\n"
        "На какую дату задано ДЗ?\n"
        "Формат: ДД.ММ.ГГГГ (например, 15.03.2026)\n"
        "или: завтра, послезавтра, через 2 дня",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Отмена"))
    )
    await AddHomework.waiting_for_date.set()


# Обработка ввода даты
async def process_date(message: types.Message, state: FSMContext):
    date_text = message.text.lower().strip()
    offsets = {
        "завтра": 1, "послезавтра": 2,
        "через 2 дня": 2, "через 3 дня": 3, "через 4 дня": 4,
        "через 5 дней": 5, "через 6 дней": 6, "через 7 дней": 7,
    }
    if date_text in offsets:
        selected_date = datetime.now() + timedelta(days=offsets[date_text])
    else:
        try:
            selected_date = datetime.strptime(date_text, "%d.%m.%Y")
        except ValueError:
            await message.answer("❌ Неверный формат. Попробуй ДД.ММ.ГГГГ или 'завтра'")
            return

    await state.update_data(date_for=selected_date.strftime("%Y-%m-%d"))
    await message.answer(
        f"✅ Дата: {selected_date.strftime('%d.%m.%Y')}\n\nВведи название предмета:"
    )
    await AddHomework.waiting_for_subject.set()


# Обработка ввода предмета
async def process_subject(message: types.Message, state: FSMContext):
    await state.update_data(subject=message.text.strip())
    await message.answer("📝 Теперь введи текст задания:")
    await AddHomework.waiting_for_task.set()


# Обработка ввода задания
async def process_task(message: types.Message, state: FSMContext):
    await state.update_data(task=message.text.strip(), attachments=[])
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Пропустить"))
    keyboard.add(KeyboardButton("Отмена"))
    await message.answer(
        "📎 Прикрепи файл или фото (можно несколько):\n"
        "• Фото 📷\n• Документ 📄\n• Видео 🎥\n• Голосовое 🎤\n\n"
        "Или нажми Пропустить",
        reply_markup=keyboard
    )
    await AddHomework.waiting_for_attachment.set()


# Обработка текстовых команд в состоянии вложений
async def process_attachment_text(message: types.Message, state: FSMContext):
    if message.text in ("Пропустить", "Завершить добавление файлов"):
        await show_preview(message, state)


# Обработка медиафайлов — файлы теперь хранятся в FSM state
async def process_attachment_media(message: types.Message, state: FSMContext):
    try:
        if message.photo:
            file_data = {"type": "photo", "file_id": message.photo[-1].file_id, "caption": message.caption or ""}
        elif message.document:
            file_data = {"type": "document", "file_id": message.document.file_id, "file_name": message.document.file_name or "файл", "caption": message.caption or ""}
        elif message.video:
            file_data = {"type": "video", "file_id": message.video.file_id, "caption": message.caption or ""}
        elif message.audio:
            file_data = {"type": "audio", "file_id": message.audio.file_id, "caption": message.caption or ""}
        elif message.voice:
            file_data = {"type": "voice", "file_id": message.voice.file_id}
        else:
            await message.answer("❌ Неподдерживаемый тип файла")
            return

        # Сохраняем файл прямо в FSM state
        data = await state.get_data()
        attachments = data.get("attachments", [])
        attachments.append(file_data)
        await state.update_data(attachments=attachments)

        emoji = {"photo": "📷", "document": "📄", "video": "🎥", "audio": "🎵", "voice": "🎤"}
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("Завершить добавление файлов"))
        keyboard.add(KeyboardButton("Отмена"))

        await message.answer(
            f"✅ {emoji.get(file_data['type'], '📎')} Файл добавлен! Всего: {len(attachments)}\n\n"
            "Отправь ещё файл или нажми Завершить",
            reply_markup=keyboard
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении файла: {e}")


# Показ превью
async def show_preview(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()

        attachments = data.get("attachments", [])
        if attachments:
            names = {"photo": "Фото", "document": "Документ", "video": "Видео", "audio": "Аудио", "voice": "Голосовое"}
            att_info = f"📎 Вложений: {len(attachments)}\n"
            att_info += "".join(f"  {i+1}. {names.get(f['type'], f['type'])}\n" for i, f in enumerate(attachments))
        else:
            att_info = "📎 Вложений: нет\n"

        preview = (
            "📋 Предпросмотр ДЗ:\n\n"
            f"📅 Дата: {datetime.strptime(data['date_for'], '%Y-%m-%d').strftime('%d.%m.%Y')}\n"
            f"📚 Предмет: {data['subject']}\n"
            f"📝 Задание: {data['task']}\n"
            f"{att_info}\n"
            "Всё верно? Подтверди добавление:"
        )

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("✅ Да, добавить"))
        keyboard.add(KeyboardButton("❌ Нет, отменить"))

        await message.answer(preview, reply_markup=keyboard)
        await AddHomework.waiting_for_confirmation.set()

    except KeyError as e:
        await message.answer(
            f"❌ Потерялись данные ({e}). Начни заново — нажми '➕ Добавить ДЗ'",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        await state.finish()
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {e}\nНачни заново — нажми '➕ Добавить ДЗ'",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        await state.finish()


# Подтверждение добавления
async def confirm_add_homework(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text == "✅ Да, добавить":
        try:
            data = await state.get_data()
            date_for = datetime.strptime(data['date_for'], "%Y-%m-%d").date()
            attachments = data.get("attachments", [])
            attachment_data = json.dumps(attachments, ensure_ascii=False) if attachments else None

            homework = add_homework_to_db(
                subject=data['subject'],
                task=data['task'],
                date_for=date_for,
                attachment_file_id=attachment_data
            )

            if homework:
                text = "✅ ДЗ успешно добавлено!"
                if attachments:
                    text += f"\n📎 Файлов: {len(attachments)}"
                await message.answer(text, reply_markup=get_main_keyboard(user_id))
            else:
                await message.answer("❌ Ошибка при сохранении в базу. Попробуй ещё раз.",
                                     reply_markup=get_main_keyboard(user_id))
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}", reply_markup=get_main_keyboard(user_id))
    else:
        await message.answer("❌ Добавление отменено", reply_markup=get_main_keyboard(user_id))

    await state.finish()


# Отмена
async def cancel_add_homework(message: types.Message, state: FSMContext):
    await message.answer("❌ Добавление ДЗ отменено", reply_markup=get_main_keyboard(message.from_user.id))
    await state.finish()
