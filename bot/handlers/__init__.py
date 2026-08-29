from aiogram import Router

from bot.handlers import callbacks, consultation_survey, join_request, start, watched


def setup_routers() -> Router:
    root = Router(name="root")
    root.include_router(join_request.router)
    root.include_router(start.router)
    root.include_router(callbacks.router)
    root.include_router(consultation_survey.router)
    root.include_router(watched.router)
    return root
