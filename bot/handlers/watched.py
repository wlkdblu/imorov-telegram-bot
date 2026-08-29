import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.database.repository import UserRepository
from bot.services.user_service import UserService

logger = logging.getLogger(__name__)

router = Router(name="watched")


@router.message(Command("watched"))
async def cmd_watched(
    message: Message,
    user_service: UserService,
    repo: UserRepository,
    state: FSMContext,
) -> None:
    """Резервная команда для режима video_mode: url."""
    if message.from_user is None:
        return

    success = await user_service.handle_video_click(repo, message.from_user.id, state)
    if success:
        await message.answer("Отлично! Скоро пришлю информацию о консультации.")
    else:
        await message.answer("Сначала нажми /start")
