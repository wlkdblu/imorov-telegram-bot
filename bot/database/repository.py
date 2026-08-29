from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User, UserStage


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def upsert_from_telegram(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                stage=UserStage.NEW.value,
            )
            self._session.add(user)
            await self._session.flush()
            return user

        user.username = username
        user.first_name = first_name
        await self._session.flush()
        return user

    async def mark_join_request(self, telegram_id: int) -> User | None:
        user = await self.get_by_telegram_id(telegram_id)
        now = datetime.now(timezone.utc)
        if user is None:
            user = User(
                telegram_id=telegram_id,
                join_request_at=now,
                join_request_pending=True,
                stage=UserStage.NEW.value,
            )
            self._session.add(user)
        else:
            user.join_request_at = now
            user.join_request_pending = True
        await self._session.flush()
        return user

    async def clear_join_request_pending(self, telegram_id: int) -> None:
        user = await self.get_by_telegram_id(telegram_id)
        if user is not None:
            user.join_request_pending = False
            await self._session.flush()

    async def set_stage(self, telegram_id: int, stage: UserStage) -> User | None:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        user.stage = stage.value
        await self._session.flush()
        return user

    async def mark_video_clicked(self, telegram_id: int) -> User | None:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        now = datetime.now(timezone.utc)
        user.video_clicked_at = now
        user.stage = UserStage.WATCHED_VIDEO.value
        user.reminder_index = 0
        user.last_reminder_at = None
        await self._session.flush()
        return user

    async def mark_consultation_sent(self, telegram_id: int) -> User | None:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        now = datetime.now(timezone.utc)
        user.consultation_sent_at = now
        user.stage = UserStage.CONSULTATION_SENT.value
        user.reminder_index = 0
        user.last_reminder_at = None
        await self._session.flush()
        return user

    async def start_video_reminders(self, telegram_id: int) -> User | None:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        now = datetime.now(timezone.utc)
        user.stage = UserStage.WAITING_VIDEO.value
        user.video_reminder_started_at = now
        user.reminder_index = 0
        user.last_reminder_at = None
        await self._session.flush()
        return user

    async def start_consultation_survey(self, telegram_id: int) -> User | None:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        user.stage = UserStage.CONSULTATION_SURVEY.value
        await self._session.flush()
        return user

    async def save_survey_answer(
        self,
        telegram_id: int,
        field: str,
        value: str,
    ) -> User | None:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        setattr(user, field, value)
        await self._session.flush()
        return user

    async def complete_survey(self, telegram_id: int) -> User | None:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        now = datetime.now(timezone.utc)
        user.survey_completed_at = now
        user.stage = UserStage.CONSULTATION_BOOKED.value
        await self._session.flush()
        return user

    async def update_reminder_sent(self, telegram_id: int, next_index: int) -> None:
        await self._session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(
                last_reminder_at=datetime.now(timezone.utc),
                reminder_index=next_index,
            )
        )

    async def get_users_for_video_reminders(self) -> list[User]:
        result = await self._session.execute(
            select(User).where(
                User.stage == UserStage.WAITING_VIDEO.value,
                User.video_clicked_at.is_(None),
                User.video_reminder_started_at.is_not(None),
            )
        )
        return list(result.scalars().all())

    async def get_users_for_consultation(self) -> list[User]:
        result = await self._session.execute(
            select(User).where(
                User.stage == UserStage.WATCHED_VIDEO.value,
                User.video_clicked_at.is_not(None),
                User.consultation_sent_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def get_users_for_consultation_reminders(self) -> list[User]:
        result = await self._session.execute(
            select(User).where(
                User.stage == UserStage.CONSULTATION_SENT.value,
                User.consultation_sent_at.is_not(None),
            )
        )
        return list(result.scalars().all())

    async def commit(self) -> None:
        await self._session.commit()
