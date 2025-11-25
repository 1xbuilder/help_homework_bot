# handlers/delete_homework.py
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.start import get_main_keyboard
from database.db_session import SessionLocal
from database.db_operations import get_all_homeworks, delete_homework, get_homework_by_id, get_homework_by_date
from datetime import datetime, date
from collections import defaultdict
from states.delete_states import DeleteHomework

# Начинаем процесс удаления ДЗ
async def start_delete_homework(message: types.Message, state: FSMContext):
    db = SessionLocal()
    try:
        # Получаем все ДЗ и группируем по датам
        homeworks = get_all_homeworks(db)
        
        if not homeworks:
            await message.answer("❌ В базе нет домашних заданий для удаления.", 
                               reply_markup=get_main_keyboard(message.from_user.id))
            return
        
        # Группируем ДЗ по датам
        homework_by_date = defaultdict(list)
        for hw in homeworks:
            homework_by_date[hw.date_for].append(hw)
        
        # Сортируем даты по убыванию (самые свежие сначала)
        sorted_dates = sorted(homework_by_date.keys(), reverse=True)
        
        # Создаем клавиатуру с датами (максимум 10 последних дат)
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        
        for hw_date in sorted_dates[:10]:
            hw_count = len(homework_by_date[hw_date])
            date_str = hw_date.strftime('%d.%m.%Y')
            btn_text = f"📅 {date_str} ({hw_count} ДЗ)"
            keyboard.add(KeyboardButton(btn_text))
        
        keyboard.add(KeyboardButton("🔙 Назад"))
        
        await message.answer("📋 Выбери дату для удаления ДЗ:", reply_markup=keyboard)
        await DeleteHomework.waiting_for_date_selection.set()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", 
                           reply_markup=get_main_keyboard(message.from_user.id))
    finally:
        db.close()

# Обработка выбора даты
async def process_date_selection(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await message.answer("Главное меню:", reply_markup=get_main_keyboard(message.from_user.id))
        await state.finish()
        return
    
    if not message.text.startswith("📅"):
        await message.answer("❌ Пожалуйста, выбери дату из списка выше.")
        return
    
    # Извлекаем дату из текста кнопки
    try:
        date_text = message.text.split(" ")[1]  # Получаем "15.12.2024"
        selected_date = datetime.strptime(date_text, "%d.%m.%Y").date()
        
        # Получаем ДЗ на выбранную дату
        db = SessionLocal()
        try:
            homeworks = get_homework_by_date(db, selected_date)
            
            if not homeworks:
                await message.answer("❌ На выбранную дату ДЗ не найдено.")
                return
            
            # Создаем клавиатуру с ДЗ на эту дату
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            
            for hw in homeworks:
                task_preview = hw.task[:40] + "..." if len(hw.task) > 40 else hw.task
                btn_text = f"🗑️ {hw.subject}: {task_preview}"
                keyboard.add(KeyboardButton(btn_text))
            
            keyboard.add(KeyboardButton("🔙 К выбору даты"))
            keyboard.add(KeyboardButton("🔙 Назад"))
            
            # Сохраняем информацию о ДЗ в состоянии
            await state.update_data(
                selected_date=selected_date,
                homeworks_list=[hw.id for hw in homeworks],
                homeworks_data={hw.id: hw for hw in homeworks}
            )
            
            await message.answer(f"📚 ДЗ на {selected_date.strftime('%d.%m.%Y')}:\nВыбери задание для удаления:", reply_markup=keyboard)
            await DeleteHomework.waiting_for_homework_selection.set()
            
        except Exception as e:
            await message.answer(f"❌ Ошибка базы данных: {str(e)}")
        finally:
            db.close()
            
    except Exception as e:
        await message.answer("❌ Ошибка формата даты. Попробуй еще раз.")

# Обработка выбора конкретного ДЗ для удаления
async def process_homework_selection(message: types.Message, state: FSMContext):
    if message.text == "🔙 К выбору даты":
        # Возвращаемся к выбору даты
        await start_delete_homework(message, state)
        return
    
    if message.text == "🔙 Назад":
        await message.answer("Главное меню:", reply_markup=get_main_keyboard(message.from_user.id))
        await state.finish()
        return
    
    if not message.text.startswith("🗑️"):
        await message.answer("❌ Пожалуйста, выбери ДЗ из списка выше.")
        return
    
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        homeworks_data = data.get('homeworks_data', {})
        selected_date = data.get('selected_date')
        
        # Ищем выбранное ДЗ
        hw_description = message.text[2:].strip()
        selected_homework = None
        
        for hw_id, hw in homeworks_data.items():
            if hw_description.startswith(hw.subject):
                selected_homework = hw
                break
        
        if not selected_homework:
            await message.answer("❌ ДЗ не найдено. Попробуй выбрать снова.")
            return
        
        # Сохраняем ID выбранного ДЗ в состоянии
        await state.update_data(selected_homework_id=selected_homework.id)
        
        # Показываем подтверждение удаления
        confirmation_text = (
            f"❓ Ты уверен, что хочешь удалить это ДЗ?\n\n"
            f"📅 Дата: {selected_homework.date_for.strftime('%d.%m.%Y')}\n"
            f"📚 Предмет: {selected_homework.subject}\n"
            f"📝 Задание: {selected_homework.task}\n\n"
            f"⚠️ Это действие нельзя отменить!"
        )
        
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("✅ Да, удалить"))
        keyboard.add(KeyboardButton("❌ Нет, отменить"))
        
        await message.answer(confirmation_text, reply_markup=keyboard)
        await DeleteHomework.waiting_for_confirmation.set()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

# Подтверждение удаления
async def confirm_deletion(message: types.Message, state: FSMContext):
    if message.text == "✅ Да, удалить":
        data = await state.get_data()
        homework_id = data.get('selected_homework_id')
        
        if not homework_id:
            await message.answer("❌ Ошибка: ДЗ не выбрано.", 
                               reply_markup=get_main_keyboard(message.from_user.id))
            await state.finish()
            return
        
        db = SessionLocal()
        try:
            homework = get_homework_by_id(db, homework_id)
            
            if homework:
                success = delete_homework(db, homework_id)
                
                if success:
                    await message.answer(
                        f"✅ ДЗ успешно удалено!\n\n"
                        f"📅 {homework.date_for.strftime('%d.%m.%Y')}\n"
                        f"📚 {homework.subject}",
                        reply_markup=get_main_keyboard(message.from_user.id)
                    )
                else:
                    await message.answer("❌ Ошибка при удалении ДЗ.", 
                                       reply_markup=get_main_keyboard(message.from_user.id))
            else:
                await message.answer("❌ ДЗ не найдено.", 
                                   reply_markup=get_main_keyboard(message.from_user.id))
                
        except Exception as e:
            await message.answer(f"❌ Ошибка базы данных: {str(e)}", 
                               reply_markup=get_main_keyboard(message.from_user.id))
        finally:
            db.close()
        
        await state.finish()
    
    else:
        await message.answer("❌ Удаление отменено.", 
                           reply_markup=get_main_keyboard(message.from_user.id))
        await state.finish()