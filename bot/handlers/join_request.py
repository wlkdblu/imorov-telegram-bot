import logging

from aiogram import Router
from aiogram.types import ChatJoinRequest

from bot.database.repository import UserRepository
from bot.services.user_service import UserService

logger = logging.getLogger(__name__)

router = Router(name="join_request")


@router.chat_join_request()
async def on_chat_join_request(
    event: ChatJoinRequest,
    user_service: UserService,
    repo: UserRepository,
    channel_id: int,
) -> None:
    if event.chat.id != channel_id:
        return

    user = event.from_user
    logger.info(
        "Join request received: user_id=%s username=%s",
        user.id,
        user.username,
    )

    await user_service.send_join_request_message(
        repo=repo,
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )
