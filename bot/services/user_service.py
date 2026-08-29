import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import User as TelegramUser

from bot.database.models import User, UserStage
from bot.database.repository import UserRepository
from bot.fsm.states import ConsultationSurvey, UserFlow
from bot.keyboards.inline import (
    consultation_keyboard,
    consultation_link_keyboard,
    survey_options_keyboard,
    video_keyboard,
    youtube_link_keyboard,
)
from bot.utils.messaging import send_content_message
from config.settings import AppConfig, EnvSettings, MessagesConfig, SurveyQuestion

logger = logging.getLogger(__name__)


class UserService:
    def __init__(
        self,
        bot: Bot,
        env: EnvSettings,
        messages: MessagesConfig,
        app_config: AppConfig,
    ) -> None:
        self._bot = bot
        self._env = env
        self._messages = messages
        self._app_config = app_config

    async def register_user(
        self,
        repo: UserRepository,
        tg_user: TelegramUser,
    ) -> None:
        await repo.upsert_from_telegram(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        await repo.commit()
        logger.info("User registered: telegram_id=%s", tg_user.id)

    async def approve_join_request(
        self,
        repo: UserRepository,
        telegram_id: int,
    ) -> bool:
        user = await repo.get_by_telegram_id(telegram_id)
        if user is None or not user.join_request_pending:
            return False

        try:
            await self._bot.approve_chat_join_request(
                chat_id=self._env.channel_id,
                user_id=telegram_id,
            )
            await repo.clear_join_request_pending(telegram_id)
            await repo.commit()
            logger.info("Join request approved: telegram_id=%s", telegram_id)
            return True
        except TelegramBadRequest as exc:
            logger.warning(
                "Could not approve join request for telegram_id=%s: %s",
                telegram_id,
                exc,
            )
            await repo.clear_join_request_pending(telegram_id)
            await repo.commit()
            return False
        except TelegramAPIError:
            logger.exception(
                "Failed to approve join request: telegram_id=%s", telegram_id
            )
            return False

    async def send_join_request_message(
        self,
        repo: UserRepository,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
    ) -> bool:
        await repo.upsert_from_telegram(telegram_id, username, first_name)
        await repo.mark_join_request(telegram_id)
        await repo.commit()

        start_link = self._app_config.bot_start_link(self._env.bot_username)
        text = f"{self._messages.join_request_text}\n\n{start_link}"

        sent = await send_content_message(
            self._bot,
            telegram_id,
            text,
            image_path=self._messages.join_request_image,
        )
        if sent:
            logger.info("Join request message sent: telegram_id=%s", telegram_id)
        return sent

    async def send_start_message(
        self,
        repo: UserRepository,
        telegram_id: int,
        state: FSMContext,
    ) -> bool:
        await repo.start_video_reminders(telegram_id)
        await repo.commit()

        keyboard = video_keyboard(self._messages, self._env.youtube_video_url)
        sent = await send_content_message(
            self._bot,
            telegram_id,
            self._messages.start_text,
            image_path=self._messages.start_image,
            reply_markup=keyboard,
        )
        if sent:
            await state.set_state(UserFlow.waiting_video)
            logger.info("Start message sent: telegram_id=%s", telegram_id)
        return sent

    async def handle_video_click(
        self,
        repo: UserRepository,
        telegram_id: int,
        state: FSMContext,
    ) -> bool:
        user = await repo.mark_video_clicked(telegram_id)
        if user is None:
            return False
        await repo.commit()
        await state.set_state(UserFlow.watched_video)

        if self._messages.video_button_mode == "callback":
            keyboard = youtube_link_keyboard(
                self._messages,
                self._env.youtube_video_url,
            )
            await send_content_message(
                self._bot,
                telegram_id,
                self._messages.video_link_text,
                image_path=self._messages.video_link_image,
                reply_markup=keyboard,
            )

        logger.info("Video click recorded: telegram_id=%s", telegram_id)
        return True

    async def send_consultation_message(self, repo: UserRepository, telegram_id: int) -> bool:
        user = await repo.get_by_telegram_id(telegram_id)
        if user is None or user.consultation_sent_at is not None:
            return False

        await repo.mark_consultation_sent(telegram_id)
        await repo.commit()

        keyboard = consultation_keyboard(self._messages)
        sent = await send_content_message(
            self._bot,
            telegram_id,
            self._messages.consultation_text,
            image_path=self._messages.consultation_image,
            reply_markup=keyboard,
        )
        if sent:
            logger.info("Consultation message sent: telegram_id=%s", telegram_id)
        return sent

    async def start_consultation_survey(
        self,
        repo: UserRepository,
        telegram_id: int,
        state: FSMContext,
    ) -> bool:
        await repo.start_consultation_survey(telegram_id)
        await repo.commit()
        await state.set_state(ConsultationSurvey.who)

        question = self._messages.survey_who
        keyboard = survey_options_keyboard("sv_who", question)
        try:
            await self._bot.send_message(
                telegram_id,
                question.question,
                reply_markup=keyboard,
            )
            logger.info("Consultation survey started: telegram_id=%s", telegram_id)
            return True
        except TelegramAPIError:
            logger.exception(
                "Failed to start consultation survey: telegram_id=%s", telegram_id
            )
            return False

    async def handle_survey_who(
        self,
        repo: UserRepository,
        telegram_id: int,
        state: FSMContext,
        answer: str,
    ) -> None:
        await repo.save_survey_answer(telegram_id, "survey_who", answer)
        await repo.commit()
        await state.set_state(ConsultationSurvey.income)

        question = self._messages.survey_income
        keyboard = survey_options_keyboard("sv_income", question)
        await self._bot.send_message(
            telegram_id,
            question.question,
            reply_markup=keyboard,
        )

    async def handle_survey_income(
        self,
        repo: UserRepository,
        telegram_id: int,
        state: FSMContext,
        answer: str,
    ) -> None:
        await repo.save_survey_answer(telegram_id, "survey_income", answer)
        await repo.commit()
        await state.set_state(ConsultationSurvey.age)

        question = self._messages.survey_age
        keyboard = survey_options_keyboard("sv_age", question)
        await self._bot.send_message(
            telegram_id,
            question.question,
            reply_markup=keyboard,
        )

    async def handle_survey_age(
        self,
        repo: UserRepository,
        telegram_id: int,
        state: FSMContext,
        answer: str,
    ) -> None:
        await repo.save_survey_answer(telegram_id, "survey_age", answer)
        await repo.commit()
        await state.set_state(ConsultationSurvey.request)

        question = self._messages.survey_request
        await self._bot.send_message(telegram_id, question.question)

    async def handle_survey_request(
        self,
        repo: UserRepository,
        telegram_id: int,
        state: FSMContext,
        answer: str,
    ) -> None:
        await repo.save_survey_answer(telegram_id, "survey_request", answer)
        user = await repo.complete_survey(telegram_id)
        await repo.commit()
        await state.clear()

        if user is not None:
            await self._notify_admin(user)
            await self._send_consultation_link(telegram_id)

    async def _notify_admin(self, user: User) -> None:
        username = user.username or "нет"
        text = self._messages.survey_admin_template.format(
            telegram_id=user.telegram_id,
            username=username,
            first_name=user.first_name or "—",
            survey_who=user.survey_who or "—",
            survey_income=user.survey_income or "—",
            survey_age=user.survey_age or "—",
            survey_request=user.survey_request or "—",
        )
        try:
            await self._bot.send_message(self._env.admin_id, text)
            logger.info("Admin notified about survey: telegram_id=%s", user.telegram_id)
        except TelegramAPIError:
            logger.exception(
                "Failed to notify admin about survey: telegram_id=%s",
                user.telegram_id,
            )

    async def _send_consultation_link(self, telegram_id: int) -> None:
        keyboard = consultation_link_keyboard(
            self._messages,
            self._env.consultation_url,
        )
        await send_content_message(
            self._bot,
            telegram_id,
            self._messages.consultation_link_text,
            image_path=self._messages.consultation_link_image,
            reply_markup=keyboard,
        )

    async def send_reminder(
        self,
        telegram_id: int,
        text: str,
        reminder_type: str,
        reminder_index: int = 0,
    ) -> bool:
        if reminder_type == "video":
            keyboard = video_keyboard(self._messages, self._env.youtube_video_url)
        else:
            keyboard = consultation_keyboard(self._messages)

        image_path = self._messages.get_reminder_image(reminder_type, reminder_index)

        return await send_content_message(
            self._bot,
            telegram_id,
            text,
            image_path=image_path,
            reply_markup=keyboard,
        )

    @staticmethod
    def minutes_since(dt: datetime | None) -> float:
        if dt is None:
            return 0.0
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (now - dt).total_seconds() / 60

    @staticmethod
    def should_send_scheduled_reminder(
        reference_at: datetime | None,
        reminder_index: int,
        delays_minutes: list[int],
    ) -> bool:
        if reference_at is None or reminder_index >= len(delays_minutes):
            return False
        elapsed = UserService.minutes_since(reference_at)
        return elapsed >= delays_minutes[reminder_index]

    @staticmethod
    def get_survey_answer(question: SurveyQuestion, index: int) -> str | None:
        if 0 <= index < len(question.options):
            return question.options[index]
        return None
