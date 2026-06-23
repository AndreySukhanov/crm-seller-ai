"""
Здесь скрипты по анализу лидов, анализу даилогов,
всё это записывается в бд, создайте необходимые модели для этого
Затем вся инфа выводится в админку
"""

import logging

from openai import OpenAI

from django.conf import settings

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL or None,
)


def classify_lead_with_gpt(lead_history: str, prompt: str) -> str:
    """
    Отправляет запрос к GPT для классификации лида.
    :param lead_history: история диалога с пользователем
    :param prompt: пользовательский промпт с критериями
    :return: 'A', 'B' или 'C'
    """
    try:
        """Генерация ответа от OpenAI."""
        response = client.chat.completions.create(
            messages=[
                {"role": "user", "content": f"{prompt}\n\nИстория диалога:\n{lead_history}\n\nКатегория:"}
            ],
            model="gpt-5.5",
            temperature=0.7,
            max_tokens=1000,
        )
        # logger.debug(f"OpenAI response {response}")
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"GPT error: {e}")
        return ""


# lead_history = """
# Пользователь: Здравствуйте! Я хочу оформить тариф "Про".
# Менеджер: Отлично! Хотите оплатить прямо сейчас?
# Пользователь: Да, отправьте реквизиты.
# """
# prompt = """
# Классифицируй лида на:
# A - высокий интерес и намерение купить,
# B - средний интерес,
# C - низкий интерес или отказ.
# Вернуть 'A', 'B' или 'C'.
# """
# result = classify_lead_with_gpt(lead_history, prompt)