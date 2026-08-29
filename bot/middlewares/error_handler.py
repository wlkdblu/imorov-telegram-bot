import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except TelegramAPIError as exc:
            logger.exception("Telegram API error: %s", exc)
            if isinstance(event, CallbackQuery):
                await self._safe_answer_callback(event, "Произошла ошибка. Попробуйте позже.")
            elif isinstance(event, Message):
                await self._safe_reply(event, "Произошла ошибка. Попробуйте позже.")
            return None
        except Exception:
            logger.exception("Unhandled error in handler")
            if isinstance(event, CallbackQuery):
                await self._safe_answer_callback(event, "Произошла ошибка. Попробуйте позже.")
            elif isinstance(event, Message):
                await self._safe_reply(event, "Произошла ошибка. Попробуйте позже.")
            return None

    @staticmethod
    async def _safe_answer_callback(callback: CallbackQuery, text: str) -> None:
        try:
            await callback.answer(text, show_alert=True)
        except TelegramAPIError:
            logger.exception("Failed to answer callback")

    @staticmethod
    async def _safe_reply(message: Message, text: str) -> None:
        try:
            await message.answer(text)
        except TelegramAPIError:
            logger.exception("Failed to send error reply")
