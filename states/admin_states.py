from aiogram.fsm.state import State, StatesGroup

class AddTestState(StatesGroup):
    waiting_for_subject = State()
    waiting_for_question = State()
    waiting_for_option_a = State()
    waiting_for_option_b = State()
    waiting_for_option_c = State()
    waiting_for_option_d = State()
    waiting_for_correct = State()
    waiting_for_explanation = State()