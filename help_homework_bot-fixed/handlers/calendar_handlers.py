from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, date, timedelta
from database.db_session import SessionLocal
from database.db_operations import get_homework_by_date
from handlers.homework import send_homework_with_files
import calendar

# Показ календаря для выбора даты
async def show_calendar(message: types.Message):
    current_date = datetime.now()
    await show_calendar_for_month(message, current_date.year, current_date.month)

# Показ календаря за конкретный месяц
async def show_calendar_for_month(message: types.Message, year: int, month: int):
    # Создаем клавиатуру календаря
    keyboard = InlineKeyboardMarkup(row_width=7)
    
    # Заголовок с месяцем и годом
    month_name = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                 "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"][month-1]
    header_buttons = [
        InlineKeyboardButton(f"{month_name} {year}", callback_data="ignore")
    ]
    keyboard.row(*header_buttons)
    
    # Кнопки для навигации
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    nav_buttons = [
        InlineKeyboardButton("◀️", callback_data=f"calendar_prev_{prev_year}_{prev_month}"),
        InlineKeyboardButton("❌ Закрыть", callback_data="calendar_close"),
        InlineKeyboardButton("▶️", callback_data=f"calendar_next_{next_year}_{next_month}")
    ]
    keyboard.row(*nav_buttons)
    
    # Дни недели
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    keyboard.row(*[InlineKeyboardButton(day, callback_data="ignore") for day in week_days])
    
    # Получаем календарь на месяц
    cal = calendar.monthcalendar(year, month)
    today = datetime.now().date()
    
    # Заполняем числами
    for week in cal:
        row_buttons = []
        for day in week:
            if day == 0:
                # Пустые дни
                row_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                # Активные дни
                current_day = date(year, month, day)
                day_text = str(day)
                
                # Помечаем сегодняшний день
                if current_day == today:
                    day_text = f"🔸{day}"
                # Помечаем прошедшие дни
                elif current_day < today:
                    day_text = f"⚫️{day}"
                
                row_buttons.append(
                    InlineKeyboardButton(
                        day_text, 
                        callback_data=f"date_select_{year}-{month:02d}-{day:02d}"
                    )
                )
        keyboard.row(*row_buttons)
    
    # Кнопка "Сегодня"
    keyboard.row(InlineKeyboardButton("📅 Сегодня", callback_data=f"date_select_{today.year}-{today.month:02d}-{today.day:02d}"))
    
    await message.answer("📅 Выбери дату для просмотра ДЗ:", reply_markup=keyboard)

# Обработка нажатий на календаре
async def handle_calendar_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    
    if data == "calendar_close":
        await callback_query.message.delete()
        await callback_query.answer("Календарь закрыт")
        return
    
    elif data.startswith("calendar_prev_"):
        # Листаем на предыдущий месяц
        _, _, year, month = data.split("_")
        await callback_query.message.delete()
        await show_calendar_for_month(callback_query.message, int(year), int(month))
    
    elif data.startswith("calendar_next_"):
        # Листаем на следующий месяц
        _, _, year, month = data.split("_")
        await callback_query.message.delete()
        await show_calendar_for_month(callback_query.message, int(year), int(month))
    
    elif data.startswith("date_select_"):
        # Выбрана дата
        selected_date_str = data.replace("date_select_", "")
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        
        await callback_query.answer(f"Загружаем ДЗ на {selected_date.strftime('%d.%m.%Y')}")
        
        # Получаем ДЗ на выбранную дату
        db = SessionLocal()
        try:
            homeworks = get_homework_by_date(db, selected_date)
            
            if not homeworks:
                await callback_query.message.answer(
                    f"📝 На {selected_date.strftime('%d.%m.%Y')} домашних заданий нет!"
                )
            else:
                await callback_query.message.answer(
                    f"📚 Домашние задания на {selected_date.strftime('%d.%m.%Y')}:"
                )
                
                for homework in homeworks:
                    await send_homework_with_files(callback_query.message, homework)
                    
        except Exception as e:
            await callback_query.message.answer(f"❌ Ошибка при загрузке ДЗ: {str(e)}")
        finally:
            db.close()
        
        # Удаляем календарь после выбора даты
        await callback_query.message.delete()
    
    else:
        await callback_query.answer()

# Функция для обработки команды выбора даты
async def show_date_selection(message: types.Message):
    await show_calendar(message)