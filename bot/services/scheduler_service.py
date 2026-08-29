import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.database.repository import UserRepository
from bot.database.session import Database
from bot.services.user_service import UserService
from config.settings import AppConfig, MessagesConfig

logger = logging.getLogger(__name__)


class ReminderScheduler:
    def __init__(
        self,
        bot: Bot,
        database: Database,
        user_service: UserService,
        messages: MessagesConfig,
        app_config: AppConfig,
    ) -> None:
        self._bot = bot
        self._database = database
        self._user_service = user_service
        self._messages = messages
        self._app_config = app_config
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        interval = self._app_config.scheduler_check_interval_seconds
        self._scheduler.add_job(
            self._process_pending_tasks,
            trigger="interval",
            seconds=interval,
            id="process_pending_tasks",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("Reminder scheduler started (interval=%ss)", interval)

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Reminder scheduler stopped")

    async def _process_pending_tasks(self) -> None:
        async with self._database.session_factory() as session:
            repo = UserRepository(session)
            await self._process_consultation_delays(repo)
            await self._process_video_reminders(repo)
            await self._process_consultation_reminders(repo)
            await session.commit()

    async def _process_consultation_delays(self, repo: UserRepository) -> None:
        delay_minutes = self._messages.consultation_delay_minutes
        users = await repo.get_users_for_consultation()

        for user in users:
            elapsed = self._user_service.minutes_since(user.video_clicked_at)
            if elapsed >= delay_minutes:
                await self._user_service.send_consultation_message(
                    repo,
                    user.telegram_id,
                )

    async def _process_video_reminders(self, repo: UserRepository) -> None:
        delays = self._messages.video_reminder_delays_minutes
        messages = self._messages.video_reminder_messages
        if not delays or not messages:
            return

        users = await repo.get_users_for_video_reminders()
        for user in users:
            if not self._user_service.should_send_scheduled_reminder(
                user.video_reminder_started_at,
                user.reminder_index,
                delays,
            ):
                continue

            text = messages[user.reminder_index]
            sent = await self._user_service.send_reminder(
                user.telegram_id,
                text,
                reminder_type="video",
                reminder_index=user.reminder_index,
            )
            if sent:
                await repo.update_reminder_sent(
                    user.telegram_id,
                    user.reminder_index + 1,
                )

    async def _process_consultation_reminders(self, repo: UserRepository) -> None:
        delays = self._messages.consultation_reminder_delays_minutes
        messages = self._messages.consultation_reminder_messages
        if not delays or not messages:
            return

        users = await repo.get_users_for_consultation_reminders()
        for user in users:
            if not self._user_service.should_send_scheduled_reminder(
                user.consultation_sent_at,
                user.reminder_index,
                delays,
            ):
                continue

            text = messages[user.reminder_index]
            sent = await self._user_service.send_reminder(
                user.telegram_id,
                text,
                reminder_type="consultation",
                reminder_index=user.reminder_index,
            )
            if sent:
                await repo.update_reminder_sent(
                    user.telegram_id,
                    user.reminder_index + 1,
                )
