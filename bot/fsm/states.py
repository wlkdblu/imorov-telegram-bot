from aiogram.fsm.state import State, StatesGroup


class UserFlow(StatesGroup):
    waiting_video = State()
    watched_video = State()
    consultation_offered = State()


class ConsultationSurvey(StatesGroup):
    who = State()
    income = State()
    age = State()
    request = State()
