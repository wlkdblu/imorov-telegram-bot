import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.database.repository import UserRepository
from bot.database.session import Database
from bot.services.user_service import UserService
from config.settings import EnvSettings, MessagesConfig

logger = logging.getLogger(__name__)


class DependenciesMiddleware(BaseMiddleware):
    def __init__(
        self,
        database: Database,
        user_service: UserService,
        env: EnvSettings,
        messages: MessagesConfig,
    ) -> None:
        self._database = database
        self._user_service = user_service
        self._env = env
        self._messages = messages

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["user_service"] = self._user_service
        data["channel_id"] = self._env.channel_id
        data["messages"] = self._messages

        async with self._database.session_factory() as session:
            data["repo"] = UserRepository(session)
            result = await handler(event, data)
            await session.commit()
            return result
