"""Создание Application для polling и webhook."""

from __future__ import annotations

import os

from telegram.ext import Application
from telegram.request import HTTPXRequest

from bot.handlers import register_handlers


def create_application(token: str | None = None) -> Application:
    bot_token = (token or os.getenv("TELEGRAM_BOT_TOKEN", "")).strip()
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN не задан")

    http_kwargs = {"trust_env": False}
    app = (
        Application.builder()
        .token(bot_token)
        .request(HTTPXRequest(proxy=None, httpx_kwargs=http_kwargs))
        .build()
    )
    register_handlers(app)
    return app
