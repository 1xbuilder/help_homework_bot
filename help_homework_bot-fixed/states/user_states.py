# states/user_states.py
from aiogram.dispatcher.filters.state import State, StatesGroup

class UserRegistration(StatesGroup):
    waiting_for_name = State()