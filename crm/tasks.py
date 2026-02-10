import json
import logging
import time
from datetime import timedelta

import openai
from celery import shared_task
from django.utils import timezone

from chat.models import Message
from crm.models import Lead

logger = logging.getLogger(__name__)


@shared_task
def example_task(seconds):
    logger.info("Задача началась. Сплю %s секунд...", seconds)
    time.sleep(seconds)
    logger.info("Задача завершена")
    return "OK"


@shared_task
def recalc_lead_segments():
    """
    Пересчитывает сегмент каждого лида по всей истории сообщений пользователя.
    """
    now = timezone.now()

    for lead in Lead.objects.select_related("user", "user__company").all():
        user = lead.user
        current = lead.segment or "Новый"
        logger.info("current=%s (lead_id=%s)", current, lead.id)

        msgs_qs = Message.objects.filter(user=user).order_by("created_at")

        if not msgs_qs.exists():
            new_segment = "Новый"
        else:
            sleep_days = (user.company.sleep_days if user.company else None) or 30
            threshold = now - timedelta(days=sleep_days)
            last_msg = msgs_qs.last()

            if last_msg.created_at < threshold:
                new_segment = "Холодный"
            elif current in ("Купил", "Не купил"):
                new_segment = current
            else:
                history = [{"role": msg.role or "user", "content": msg.content} for msg in msgs_qs]
                new_segment = classify_segment_via_gpt(history, current) or current

        logger.info("new_segment=%s (lead_id=%s)", new_segment, lead.id)
        if new_segment:
            lead.segment = new_segment
            lead.save(update_fields=["segment"])


def classify_segment_via_gpt(history_messages: list, current_segment: str) -> str:
    system_prompt = {
        "role": "system",
        "content": (
            f"Текущий сегмент лида: {current_segment}.\n"
            "На основе истории переписки выбери один из сегментов: "
            "'Новый', 'Горячий', 'Тёплый', 'Холодный', 'Купил', 'Не купил'."
        ),
    }

    messages = [system_prompt] + history_messages

    resp = openai.chat.completions.create(
        model="gpt-4",
        messages=messages,
        functions=[FUNCTION_CLASSIFY],
        function_call={"name": FUNCTION_CLASSIFY["name"]},
        temperature=0,
    )
    args = json.loads(resp.choices[0].message.function_call.arguments)
    return args.get("segment")


FUNCTION_CLASSIFY = {
    "name": "classify_user_segment",
    "description": "Классифицирует лида по диалогу",
    "parameters": {
        "type": "object",
        "properties": {
            "segment": {
                "type": "string",
                "enum": ["Новый", "Горячий", "Тёплый", "Холодный", "Купил", "Не купил"],
                "description": "Сегмент клиента",
            }
        },
        "required": ["segment"],
    },
}
