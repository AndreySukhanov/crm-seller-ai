from typing import Dict, Any

import requests

import logging

from conf import settings

logger = logging.getLogger(__name__)


def bitrix_request(webhook: str, method: str, payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Универсальный метод для выполнения запросов к Bitrix24."""
    url = f"{webhook}/{method}"

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Вызывает исключение при HTTP ошибках
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при выполнении запроса: {e}\nresponseData: {response.json()}\npayload:{payload}")
        return None

