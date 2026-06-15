from aiogram.dispatcher.filters.state import State, StatesGroup


class GroupAdmin(StatesGroup):
    """Админка старосты (owner) над своей группой."""
    menu = State()


class GlobalAdmin(StatesGroup):
    """Глобальная админка (admin): выдача create_group-ссылок, модераторы."""
    menu = State()
    waiting_for_institution_choice = State()  # к какому заведению привязать создаваемую группу
    waiting_for_new_institution = State()     # ввод названия нового заведения
    waiting_for_moderator_id = State()        # назначение модератора по Telegram ID
