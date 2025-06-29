import json
import time
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

import openai

from crm.models import Lead
from chat.models import Chat, Message

logger = logging.getLogger(__name__)

@shared_task
def example_task(seconds):
    logger.info(f"Задача началась. Сплю {seconds} секунд...")
    time.sleep(seconds)
    logger.info("Задача завершена")
    return "OK"


@shared_task
def recalc_lead_segments():
    """
    Пересчитывает сегмент каждого лида по всей истории сообщений пользователя
    и текущему сегменту:
      1) Нет сообщений → "Новый"
      2) Последнее сообщение старше user.sleep_days → "Холодный"
      3) Если current_segment in ("Купил","Не купил") → оставляем
      4) Иначе → вызываем GPT, передавая текущий сегмент и историю
    """
    now = timezone.now()

    for lead in Lead.objects.select_related("user").all():
        user = lead.user
        current = lead.segment or "Новый"
        logger.info(f"current= {current} (lead_id={lead.id})")

        # 1) Собираем все сообщения пользователя
        msgs_qs = Message.objects.filter(user=user).order_by("updated_at")

        if not msgs_qs.exists():
            new_segment = "Новый"
        else:
            # 2) Проверка "спящего"
            sleep_days = user.sleep_days or 30
            threshold = now - timedelta(days=sleep_days)
            last_msg = msgs_qs.last()

            if last_msg.updated_at < threshold:
                new_segment = "Холодный"
            # 3) Если сегмент уже финальный — оставляем его
            elif current in ("Купил", "Не купил"):
                new_segment = current
            # 4) Иначе — классифицируем через GPT
            else:
                history = [
                    {"role": msg.role or "user", "content": msg.content}
                    for msg in msgs_qs
                ]
                new_segment = classify_segment_via_gpt(history, current) or current
        logger.info(f"new_segment = {new_segment} (lead_id={lead.id})")
        # Сохраняем 
        if new_segment:
            lead.segment = new_segment
            lead.save(update_fields=["segment"])



def classify_segment_via_gpt(history_messages: list, current_segment: str) -> str:
    """
    Вызывает OpenAI-функцию classify_user_segment,
    передавая текущий сегмент в system-промте.
    Возвращает новый сегмент из списка:
    "Новый", "Горячий", "Тёплый", "Холодный", "Купил", "Не купил".
    """
    system_prompt = {
        "role": "system",
        "content": (
            f"Текущий сегмент лида: {current_segment}.\n"
            "На основе истории переписки выбери один из сегментов: "
            "'Новый', 'Горячий', 'Тёплый', 'Холодный', 'Купил', 'Не купил'."
        )
    }

    messages = [system_prompt] + history_messages

    resp = openai.chat.completions.create(
        model="gpt-5.5",
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
                "description": "Сегмент клиента"
            }
        },
        "required": ["segment"]
    }
}
