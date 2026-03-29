from aiogram.dispatcher.filters.state import State, StatesGroup

class UserRegistration(StatesGroup):
    waiting_for_name     = State()
    waiting_for_subgroup = State()  # новый шаг регистрации
