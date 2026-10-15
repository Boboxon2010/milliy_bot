from aiogram.fsm.state import State, StatesGroup

class TestStates(StatesGroup):
    choosing_subject = State()
    taking_test = State()

class EssayStates(StatesGroup):
    choosing_topic_mode = State()
    waiting_for_custom_topic = State()
    waiting_for_essay_text = State()