from aiogram.fsm.state import StatesGroup, State


class EditLink(StatesGroup):
    l_id = State()
    url = State()
    label = State()


class CreateLink(StatesGroup):
    key = State()
    url = State()
    label = State()

