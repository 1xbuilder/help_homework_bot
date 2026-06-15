from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.start import get_main_keyboard
from database.db_operations import (
    get_user_by_telegram_id, get_group_by_id,
    list_group_members, can_edit_homework,
)


def _help_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("ℹ️ Как работает бот?"))
    kb.add(KeyboardButton("🐛 Нашел ошибку"))
    kb.add(KeyboardButton("👨‍💼 Хочу заполнять ДЗ"))
    kb.add(KeyboardButton("💬 Написать в поддержку"))
    kb.add(KeyboardButton("🔙 Назад"))
    return kb


def _back_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🔙 Назад"))
    return kb


def _get_owner_contact(user_id: int):
    """Возвращает (имя, @username|None) старосты активной группы пользователя
    или None, если пользователь не в группе / старосты нет."""
    user = get_user_by_telegram_id(telegram_id=user_id)
    if not user or not user.active_group_id:
        return None
    group = get_group_by_id(user.active_group_id)
    if not group:
        return None
    owners = list_group_members(user.active_group_id, role="owner")
    if not owners:
        return (group.name, None, None)
    owner_member = owners[0]
    owner_user = get_user_by_telegram_id(telegram_id=owner_member.user_id)
    if not owner_user:
        return (group.name, None, None)
    handle = f"@{owner_user.username}" if owner_user.username else None
    return (group.name, owner_user.first_name, handle)


def _owner_line(user_id: int) -> str:
    """Строка с контактом старосты для вставки в тексты."""
    info = _get_owner_contact(user_id)
    if info is None:
        return ("Ты пока не в группе. Попроси у старосты своей группы "
                "ссылку-приглашение или напиши /start.")
    group_name, owner_name, handle = info
    if handle:
        return f"Обратись к старосте группы «{group_name}»: {owner_name} ({handle})."
    elif owner_name:
        return (f"Староста группы «{group_name}» — {owner_name}. "
                "Напиши ему в общем чате группы (у него не задан username).")
    else:
        return (f"В группе «{group_name}» пока не назначен староста с контактом. "
                "Спроси одногруппников.")


async def show_help_menu(message: types.Message):
    help_text = (
        "🆘 <b>Центр помощи</b>\n\n"
        "Здесь ты можешь:\n"
        "• 📖 Узнать, как пользоваться ботом\n"
        "• 🐛 Сообщить об ошибке\n"
        "• 👨‍💼 Узнать, как получить права на заполнение ДЗ\n"
        "• 💬 Связаться со старостой\n\n"
        "<i>Выбери нужный вариант ниже 👇</i>"
    )
    await message.answer(help_text, reply_markup=_help_keyboard(), parse_mode="HTML")


async def how_working_bot(message: types.Message):
    explanation = (
        "🤖 <b>Как работает бот?</b>\n\n"
        "• Нажми <b>📚 Посмотреть ДЗ</b>, чтобы увидеть задания своей группы\n"
        "• Выбери период: сегодня, завтра или конкретную дату\n"
        "• Получай ДЗ с файлами и описаниями\n\n"
        "✏️ <b>Заполнение ДЗ</b> доступно старосте и его помощникам:\n"
        "• <b>➕ Добавить ДЗ</b> — дата, предмет, описание, файлы\n"
        "• <b>❌ Удалить ДЗ</b> — убрать ошибочное задание\n\n"
        "📅 <b>Календарь</b> — смотри ДЗ на любую дату.\n\n"
        "⚙️ <b>Для старост</b> — команда /group:\n"
        "• пригласить одногруппников по ссылке\n"
        "• назначить помощников\n\n"
        "<i>Каждый видит ДЗ только своей группы.</i>"
    )
    await message.answer(explanation, reply_markup=_back_keyboard(), parse_mode="HTML")


async def find_mistacke_bot(message: types.Message):
    error_text = (
        "🐛 <b>Нашёл ошибку?</b>\n\n"
        "Спасибо, что помогаешь! 🙏\n\n"
        "<b>Опиши, что случилось:</b>\n"
        "• 📱 Что ты делал, когда возникла ошибка?\n"
        "• 📝 Какое сообщение увидел?\n"
        "• 🖼️ Если есть скриншот — приложи его\n\n"
        f"{_owner_line(message.from_user.id)}\n"
        "Староста передаст проблему дальше, если нужно."
    )
    await message.answer(error_text, reply_markup=_back_keyboard(), parse_mode="HTML")


async def Wanna_create_homework(message: types.Message):
    admin_text = (
        "👨‍💼 <b>Хочешь заполнять ДЗ?</b>\n\n"
        "Права на добавление и удаление ДЗ выдаёт <b>староста твоей группы</b> — "
        "он может назначить тебя помощником.\n\n"
        "<b>Что делать:</b>\n"
        f"1. {_owner_line(message.from_user.id)}\n"
        "2. Попроси назначить тебя помощником.\n\n"
        "<b>После этого ты сможешь:</b>\n"
        "• ➕ Добавлять домашние задания\n"
        "• ❌ Удалять ошибочные ДЗ\n\n"
        "<i>Староста делает это в своей панели командой /group.</i>"
    )
    await message.answer(admin_text, reply_markup=_back_keyboard(), parse_mode="HTML")


async def write_me(message: types.Message):
    support_text = (
        "💬 <b>Связь со старостой</b>\n\n"
        "По вопросам про ДЗ, расписание и доступ обращайся к старосте своей группы.\n\n"
        f"{_owner_line(message.from_user.id)}\n\n"
        "<i>Староста управляет группой и помощниками.</i>"
    )
    await message.answer(support_text, reply_markup=_back_keyboard(), parse_mode="HTML")
