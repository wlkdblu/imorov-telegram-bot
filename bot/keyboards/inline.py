from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.settings import MessagesConfig, SurveyQuestion


def video_keyboard(
    messages: MessagesConfig,
    youtube_url: str,
) -> InlineKeyboardMarkup:
    if messages.video_button_mode == "url":
        button = InlineKeyboardButton(
            text=messages.video_button_text,
            url=youtube_url,
        )
    else:
        button = InlineKeyboardButton(
            text=messages.video_button_text,
            callback_data="watch_video",
        )
    return InlineKeyboardMarkup(inline_keyboard=[[button]])


def consultation_keyboard(messages: MessagesConfig) -> InlineKeyboardMarkup:
    button = InlineKeyboardButton(
        text=messages.consultation_button_text,
        callback_data="start_consultation",
    )
    return InlineKeyboardMarkup(inline_keyboard=[[button]])


def consultation_link_keyboard(
    messages: MessagesConfig,
    consultation_url: str,
) -> InlineKeyboardMarkup:
    button = InlineKeyboardButton(
        text=messages.consultation_button_text,
        url=consultation_url,
    )
    return InlineKeyboardMarkup(inline_keyboard=[[button]])


def youtube_link_keyboard(
    messages: MessagesConfig,
    youtube_url: str,
) -> InlineKeyboardMarkup:
    button = InlineKeyboardButton(
        text=messages.video_button_text,
        url=youtube_url,
    )
    return InlineKeyboardMarkup(inline_keyboard=[[button]])


def survey_options_keyboard(
    prefix: str,
    question: SurveyQuestion,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for index, option in enumerate(question.options):
        rows.append([
            InlineKeyboardButton(
                text=option,
                callback_data=f"{prefix}:{index}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
