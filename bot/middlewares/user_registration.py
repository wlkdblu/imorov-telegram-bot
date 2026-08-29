import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser

from bot.database.repository import UserRepository
from bot.database.session import Database

logger = logging.getLogger(__name__)


class UserRegistrationMiddleware(BaseMiddleware):
    def __init__(self, database: Database) -> None:
        self._database = database

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TelegramUser | None = data.get("event_from_user")
        if tg_user is not None:
            async with self._database.session_factory() as session:
                repo = UserRepository(session)
                await repo.upsert_from_telegram(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                )
                await repo.commit()
        return await handler(event, data)
