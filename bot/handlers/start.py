import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.database.repository import UserRepository
from bot.services.user_service import UserService

logger = logging.getLogger(__name__)

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    user_service: UserService,
    repo: UserRepository,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    await user_service.register_user(repo, message.from_user)
    await user_service.approve_join_request(repo, message.from_user.id)
    await user_service.send_start_message(repo, message.from_user.id, state)
