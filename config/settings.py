from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CONFIG_DIR.parent


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(alias="BOT_TOKEN")
    channel_id: int = Field(alias="CHANNEL_ID")
    bot_username: str = Field(alias="BOT_USERNAME")
    admin_id: int = Field(alias="ADMIN_ID")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/bot.db",
        alias="DATABASE_URL",
    )
    youtube_video_url: str = Field(alias="YOUTUBE_VIDEO_URL")
    consultation_url: str = Field(alias="CONSULTATION_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str | None = Field(default=None, alias="LOG_FILE")


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


class SurveyQuestion:
    def __init__(self, question: str, options: list[str] | None = None) -> None:
        self.question = question
        self.options = options or []


class MessagesConfig:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def join_request_text(self) -> str:
        return self._data["join_request"]["text"].strip()

    @property
    def join_request_image(self) -> str | None:
        return self._data.get("join_request", {}).get("image")

    @property
    def start_text(self) -> str:
        return self._data["start"]["text"].strip()

    @property
    def start_image(self) -> str | None:
        return self._data.get("start", {}).get("image")

    @property
    def video_button_text(self) -> str:
        return self._data["start"]["video_button"]

    @property
    def video_link_text(self) -> str:
        return self._data["video_link"]["text"].strip()

    @property
    def video_link_image(self) -> str | None:
        return self._data.get("video_link", {}).get("image")

    @property
    def consultation_text(self) -> str:
        return self._data["consultation"]["text"].strip()

    @property
    def consultation_button_text(self) -> str:
        return self._data["consultation"]["button"]

    @property
    def consultation_image(self) -> str | None:
        return self._data.get("consultation", {}).get("image")

    @property
    def consultation_delay_minutes(self) -> int:
        return int(self._data["consultation"]["delay_minutes"])

    @property
    def consultation_link_text(self) -> str:
        return self._data["consultation"]["link_text"].strip()

    @property
    def consultation_link_image(self) -> str | None:
        return self._data.get("consultation", {}).get("link_image")

    @property
    def survey_who(self) -> SurveyQuestion:
        data = self._data["survey"]["who"]
        return SurveyQuestion(data["question"], data["options"])

    @property
    def survey_income(self) -> SurveyQuestion:
        data = self._data["survey"]["income"]
        return SurveyQuestion(data["question"], data["options"])

    @property
    def survey_age(self) -> SurveyQuestion:
        data = self._data["survey"]["age"]
        return SurveyQuestion(data["question"], data["options"])

    @property
    def survey_request(self) -> SurveyQuestion:
        data = self._data["survey"]["request"]
        return SurveyQuestion(data["question"])

    @property
    def survey_admin_template(self) -> str:
        return self._data["survey"]["admin_template"].strip()

    @property
    def video_reminder_delays_minutes(self) -> list[int]:
        return [int(d) for d in self._data["reminders"]["video"]["delays_minutes"]]

    @property
    def video_reminder_images(self) -> list[str]:
        section = self._data.get("reminders", {}).get("video", {})
        if "images" in section:
            return list(section["images"])
        if image := section.get("image"):
            return [image]
        return []

    @property
    def video_reminder_messages(self) -> list[str]:
        return [msg.strip() for msg in self._data["reminders"]["video"]["messages"]]

    @property
    def consultation_reminder_delays_minutes(self) -> list[int]:
        return [
            int(d) for d in self._data["reminders"]["consultation"]["delays_minutes"]
        ]

    @property
    def consultation_reminder_images(self) -> list[str]:
        section = self._data.get("reminders", {}).get("consultation", {})
        if "images" in section:
            return list(section["images"])
        if image := section.get("image"):
            return [image]
        return []

    @property
    def consultation_reminder_messages(self) -> list[str]:
        return [
            msg.strip() for msg in self._data["reminders"]["consultation"]["messages"]
        ]

    def get_reminder_image(self, reminder_type: str, index: int) -> str | None:
        if reminder_type == "video":
            images = self.video_reminder_images
        else:
            images = self.consultation_reminder_images
        if 0 <= index < len(images):
            return images[index]
        return None

    @property
    def video_button_mode(self) -> str:
        return self._data.get("buttons", {}).get("video_mode", "callback")


class AppConfig:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def scheduler_check_interval_seconds(self) -> int:
        return int(self._data["scheduler"]["check_interval_seconds"])

    @property
    def channel_name(self) -> str:
        return self._data["channel"]["name"]

    def bot_start_link(self, bot_username: str) -> str:
        return f"https://t.me/{bot_username}?start=from_channel"


def load_settings() -> tuple[EnvSettings, MessagesConfig, AppConfig]:
    env = EnvSettings()
    messages = MessagesConfig(_load_yaml(CONFIG_DIR / "messages.yaml"))
    app = AppConfig(_load_yaml(CONFIG_DIR / "settings.yaml"))
    return env, messages, app
