import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.database.migrations import run_migrations
from bot.database.session import Database
from bot.handlers import setup_routers
from bot.middlewares.dependencies import DependenciesMiddleware
from bot.middlewares.error_handler import ErrorHandlerMiddleware
from bot.middlewares.user_registration import UserRegistrationMiddleware
from bot.services.scheduler_service import ReminderScheduler
from bot.services.user_service import UserService
from bot.utils.logging import setup_logging
from config.settings import load_settings

logger = logging.getLogger(__name__)


async def on_startup(
    database: Database,
    scheduler: ReminderScheduler,
) -> None:
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    await database.create_tables()
    await run_migrations(database.engine)
    scheduler.start()
    logger.info("Bot started")


async def on_shutdown(database: Database, scheduler: ReminderScheduler) -> None:
    scheduler.shutdown()
    await database.dispose()
    logger.info("Bot stopped")


async def main() -> None:
    env, messages, app_config = load_settings()
    setup_logging(env.log_level, env.log_file)

    bot = Bot(
        token=env.bot_token,
        default=DefaultBotProperties(),
    )
    database = Database(env.database_url)
    user_service = UserService(bot, env, messages, app_config)
    scheduler = ReminderScheduler(bot, database, user_service, messages, app_config)

    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(ErrorHandlerMiddleware())
    dp.update.middleware(UserRegistrationMiddleware(database))
    dp.update.middleware(DependenciesMiddleware(database, user_service, env, messages))

    dp.include_router(setup_routers())

    async def _startup() -> None:
        await on_startup(database, scheduler)

    async def _shutdown() -> None:
        await on_shutdown(database, scheduler)

    dp.startup.register(_startup)
    dp.shutdown.register(_shutdown)

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
