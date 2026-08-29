import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.database.repository import UserRepository
from bot.fsm.states import ConsultationSurvey
from bot.services.user_service import UserService

logger = logging.getLogger(__name__)

router = Router(name="consultation_survey")


@router.message(ConsultationSurvey.request)
async def on_survey_request_text(
    message: Message,
    user_service: UserService,
    repo: UserRepository,
    state: FSMContext,
) -> None:
    if message.from_user is None or not message.text:
        await message.answer("Пожалуйста, напиши текстом свой запрос на консультацию.")
        return

    await user_service.handle_survey_request(
        repo,
        message.from_user.id,
        state,
        message.text.strip(),
    )
