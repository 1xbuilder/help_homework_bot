from aiogram.dispatcher.filters.state import State, StatesGroup


class UserRegistration(StatesGroup):
    """Базовая регистрация: имя (+ подгруппа после вступления в группу)."""
    waiting_for_name     = State()
    waiting_for_subgroup = State()


class Onboarding(StatesGroup):
    """Онбординг через инвайт-ссылки."""
    # Пользователь без группы: предлагаем ввести код приглашения вручную.
    waiting_for_invite_code = State()
    # Ветка create_group: староста вводит название своей новой группы.
    waiting_for_group_name  = State()
