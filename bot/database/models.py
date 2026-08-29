from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.base import Base


class UserStage(StrEnum):
    NEW = "new"
    WAITING_VIDEO = "waiting_video"
    WATCHED_VIDEO = "watched_video"
    CONSULTATION_SENT = "consultation_sent"
    CONSULTATION_SURVEY = "consultation_survey"
    CONSULTATION_BOOKED = "consultation_booked"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_contact_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    join_request_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    join_request_pending: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
    )
    stage: Mapped[str] = mapped_column(
        String(32),
        default=UserStage.NEW.value,
        server_default=UserStage.NEW.value,
    )
    video_clicked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    video_reminder_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    consultation_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_reminder_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    reminder_index: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    survey_who: Mapped[str | None] = mapped_column(String(64), nullable=True)
    survey_income: Mapped[str | None] = mapped_column(String(64), nullable=True)
    survey_age: Mapped[str | None] = mapped_column(String(32), nullable=True)
    survey_request: Mapped[str | None] = mapped_column(Text, nullable=True)
    survey_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
