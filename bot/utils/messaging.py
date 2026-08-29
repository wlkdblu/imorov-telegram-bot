import logging
from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError
from aiogram.types import FSInputFile, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_image(path: str | None) -> FSInputFile | None:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = PROJECT_ROOT / file_path
    if file_path.exists():
        return FSInputFile(file_path)
    if path:
        logger.warning("Image file not found: %s", file_path)
    return None


async def send_content_message(
    bot: Bot,
    chat_id: int,
    text: str,
    image_path: str | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    image = resolve_image(image_path)
    try:
        if image:
            await bot.send_photo(
                chat_id,
                photo=image,
                caption=text,
                reply_markup=reply_markup,
            )
        else:
            await bot.send_message(chat_id, text, reply_markup=reply_markup)
        return True
    except TelegramForbiddenError:
        logger.warning("User blocked bot: chat_id=%s", chat_id)
        return False
    except TelegramAPIError:
        logger.exception("Failed to send message: chat_id=%s", chat_id)
        return False
