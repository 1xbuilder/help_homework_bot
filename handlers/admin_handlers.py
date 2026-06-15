from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.start import get_main_keyboard 

async def show_help_menu(message: types.Message):
    help_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    help_keyboard.add(KeyboardButton("ℹ️ Как работает бот?"))
    help_keyboard.add(KeyboardButton("🐛 Нашел ошибку"))
    help_keyboard.add(KeyboardButton("👨‍💼 Хочу заполнять ДЗ"))
    help_keyboard.add(KeyboardButton("💬 Написать в поддержку"))
    help_keyboard.add(KeyboardButton("🔙 Назад"))
    
    help_text = (
        "🆘 <b>Центр помощи</b>\n\n"
        "Здесь ты можешь:\n"
        "• 📖 Узнать как пользоваться ботом\n"
        "• 🐛 Сообщить об ошибке\n" 
        "• 👨‍💼 Получить права на заполнение ДЗ\n"
        "• 💬 Написать в поддержку\n\n"
        "<i>Выбери нужный вариант ниже 👇</i>"
    )
    
    await message.answer(help_text, reply_markup=help_keyboard, parse_mode="HTML")

async def how_working_bot(message: types.Message):
    back_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)    
    back_keyboard.add(KeyboardButton("🔙 Назад"))
    
    explanation = (
        "🤖 <b>Как работает бот?</b>\n\n"
        
        "• Нажми <b>📚 Посмотреть ДЗ</b> чтобы увидеть задания\n"
        "• Выбери период: сегодня, завтра или конкретную дату\n"
        "• Получай ДЗ с файлами и описаниями\n\n"
        
        "• Нажми <b>➕ Добавить ДЗ</b> для нового задания\n"
        "• Укажи дату, предмет и описание\n"
        "• Прикрепи файлы (фото, документы, аудио)\n"
        "• Подтверди добавление\n\n"
        
        "🗑️ <b>Управление заданиями:</b>\n"
        "• Администраторы могут удалять ДЗ через <b>❌ Удалить ДЗ</b>\n"
        "• Просматривать все существующие задания\n\n"
        
        "📅 <b>Календарь:</b>\n"
        "• Используй календарь для выбора дат\n"
        "• Смотри ДЗ на любую дату\n\n"

        "⚙️ <b>Для старост:</b>\n"
        "• Команда /group — управление своей группой\n"
        "• Пригласить одногруппников, назначить помощников\n\n"

        "<i>Бот автоматически сохраняет все данные!</i>"
    )
    
    await message.answer(explanation, reply_markup=back_keyboard, parse_mode="HTML")

async def find_mistacke_bot(message: types.Message):
    back_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)    
    back_keyboard.add(KeyboardButton("🔙 Назад"))
    
    error_text = (
        "🐛 <b>Сообщение об ошибке</b>\n\n"
        "Спасибо, что помогаете улучшать бота! 🙏\n\n"
        "<b>Чтобы мы могли быстро исправить проблему, опишите:</b>\n"
        "• 📱 Что вы делали когда произошла ошибка?\n"
        "• ⏰ Когда это случилось?\n"
        "• 📝 Какое сообщение об ошибке вы увидели?\n"
        "• 🖼️ Если есть скриншот - пришлите его\n\n"
        "<b>Напишите разработчику:</b> @zobuk\n\n"
        "<i>Мы постараемся исправить ошибку в кратчайшие сроки! ⚡</i>"
    )
    
    await message.answer(error_text, reply_markup=back_keyboard, parse_mode="HTML")

async def Wanna_create_homework(message: types.Message):
    back_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)    
    back_keyboard.add(KeyboardButton("🔙 Назад"))
    
    admin_text = (
        "👨‍💼 <b>Стать редактором ДЗ</b>\n\n"
        "Отлично! Мы всегда рады новым помощникам! 🎉\n\n"
        "<b>Что нужно сделать:</b>\n"
        "1. 📨 Напишите @zobuk\n"
        "2. 📝 Представьтесь (скажите под каким именем вы регестрировались в боте)\n"
        "3. ✅ Попросите права администратора\n\n"
        "<b>После получения прав вы сможете:</b>\n"
        "• ➕ Добавлять новые домашние задания\n"
        "• ❌ Удалять старые или ошибочные ДЗ\n"
        "• 📊 Просматривать все существующие задания\n\n"
        "<i>Обычно мы выдаем права в течение 24 часов ⏰</i>"
    )
    
    await message.answer(admin_text, reply_markup=back_keyboard, parse_mode="HTML")

async def write_me(message: types.Message):
    back_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)    
    back_keyboard.add(KeyboardButton("🔙 Назад"))
    
    support_text = (
        "💬 <b>Поддержка</b>\n\n"
        "Есть вопросы или нужна помощь? Мы на связи! 🤝\n\n"
        "<b>По всем вопросам обращайтесь:</b>\n"
        "👨‍💻 Разработчик: @zobuk\n\n"
        "<b>Мы поможем с:</b>\n"
        "• 🔧 Техническими проблемами\n"
        "• 📚 Вопросами по работе с ДЗ\n"
        "• 👨‍💼 Получением прав доступа\n"
        "• 💡 Предложениями по улучшению\n\n"
        "<i>Обычно отвечаем в течение нескольких часов 🚀</i>"
    )
    
    await message.answer(support_text, reply_markup=back_keyboard, parse_mode="HTML")