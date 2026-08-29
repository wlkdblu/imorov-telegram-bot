import logging

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

_NEW_COLUMNS: dict[str, str] = {
    "join_request_pending": "BOOLEAN DEFAULT 0",
    "video_reminder_started_at": "DATETIME",
    "survey_who": "VARCHAR(64)",
    "survey_income": "VARCHAR(64)",
    "survey_age": "VARCHAR(32)",
    "survey_request": "TEXT",
    "survey_completed_at": "DATETIME",
}


async def run_migrations(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        def _get_columns(sync_conn):  # noqa: ANN001
            inspector = inspect(sync_conn)
            if not inspector.has_table("users"):
                return set()
            return {col["name"] for col in inspector.get_columns("users")}

        existing = await conn.run_sync(_get_columns)
        for column, col_type in _NEW_COLUMNS.items():
            if column not in existing:
                await conn.execute(
                    text(f"ALTER TABLE users ADD COLUMN {column} {col_type}")
                )
                logger.info("Migration: added column users.%s", column)
