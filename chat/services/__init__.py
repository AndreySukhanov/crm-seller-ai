"""Здесь логика обработки запросов в чат gpt,
функционал должен быть переиспользуемым для любой crm, и для любого канала связи"""
from datetime import datetime

from chat.services.base import GPT
from crm.services.request_data_handler import RequestDataHandler
from chat.models import Message, Chat

import logging

logger = logging.getLogger(__name__)


def get_or_create_chat(user):
    """
    Получает чат пользователя или создает новый, если его нет
    """
    created = False
    chat = Chat.objects.filter(user=user).order_by("-updated_at").first()
    if chat is None:
        chat = Chat.objects.create(user=user)  # заменить title
        created = True
    return chat, created


def chat_with_gpt(rdh: RequestDataHandler):
    chat, _ = get_or_create_chat(rdh.user)
    if not chat.gpt_enabled:
        return None
    gpt = GPT(rdh=rdh, chat=chat)
    return gpt.ask_gpt()


def parse_datetime(datatime: str) -> datetime:
    # Убираем всё, что после первой части времени (например, "-10:00")
    cleaned = datatime.split('-')[0].strip()

    formats = [
        '%d.%m.%Y %H:%M',
        '%d-%m-%Y %H:%M',
        '%Y-%m-%d %H:%M',
        '%Y.%m.%d %H:%M',
        '%d/%m/%Y %H:%M',
        '%Y/%m/%d %H:%M',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unsupported datetime format: {datatime}")
