import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.database.repository import UserRepository
from bot.services.user_service import UserService
from config.settings import MessagesConfig

logger = logging.getLogger(__name__)

router = Router(name="callbacks")


@router.callback_query(F.data == "watch_video")
async def on_watch_video(
    callback: CallbackQuery,
    user_service: UserService,
    repo: UserRepository,
    state: FSMContext,
) -> None:
    if callback.from_user is None:
        return

    await callback.answer()
    await user_service.handle_video_click(repo, callback.from_user.id, state)


@router.callback_query(F.data == "start_consultation")
async def on_start_consultation(
    callback: CallbackQuery,
    user_service: UserService,
    repo: UserRepository,
    state: FSMContext,
) -> None:
    if callback.from_user is None:
        return

    await callback.answer()
    await user_service.start_consultation_survey(
        repo,
        callback.from_user.id,
        state,
    )


@router.callback_query(F.data.startswith("sv_who:"))
async def on_survey_who(
    callback: CallbackQuery,
    user_service: UserService,
    repo: UserRepository,
    state: FSMContext,
    messages: MessagesConfig,
) -> None:
    if callback.from_user is None or callback.data is None:
        return

    await callback.answer()
    index = int(callback.data.split(":")[1])
    answer = UserService.get_survey_answer(messages.survey_who, index)
    if answer is None:
        return

    await user_service.handle_survey_who(
        repo,
        callback.from_user.id,
        state,
        answer,
    )


@router.callback_query(F.data.startswith("sv_income:"))
async def on_survey_income(
    callback: CallbackQuery,
    user_service: UserService,
    repo: UserRepository,
    state: FSMContext,
    messages: MessagesConfig,
) -> None:
    if callback.from_user is None or callback.data is None:
        return

    await callback.answer()
    index = int(callback.data.split(":")[1])
    answer = UserService.get_survey_answer(messages.survey_income, index)
    if answer is None:
        return

    await user_service.handle_survey_income(
        repo,
        callback.from_user.id,
        state,
        answer,
    )


@router.callback_query(F.data.startswith("sv_age:"))
async def on_survey_age(
    callback: CallbackQuery,
    user_service: UserService,
    repo: UserRepository,
    state: FSMContext,
    messages: MessagesConfig,
) -> None:
    if callback.from_user is None or callback.data is None:
        return

    await callback.answer()
    index = int(callback.data.split(":")[1])
    answer = UserService.get_survey_answer(messages.survey_age, index)
    if answer is None:
        return

    await user_service.handle_survey_age(
        repo,
        callback.from_user.id,
        state,
        answer,
    )
