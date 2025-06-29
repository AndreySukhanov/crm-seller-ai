import logging
from typing import Any, Dict, List, Optional

from crm.services.bitrix.base_methods import bitrix_request
from crm.services.bitrix.lead_methods import update_lead

logger = logging.getLogger(__name__)


def get_sales_funnel(webhook) -> Optional[list[dict[str, Any]]]:
    """Получение воронки продаж"""
    method = "crm.status.list"
    payload = {
        "filter": {"ENTITY_ID": "STATUS"},
    }
    response = bitrix_request(webhook, method, payload)
    logger.info(f"Получение воронок: {response.get('result')}")
    if response:
        return response.get("result")


def extract_status_data(data: List[Dict]) -> List[Dict]:
    """
    Извлекает STATUS_ID, NAME и ID.

    :param data: Список словарей
    :return: Список словарей с ключами STATUS_ID, NAME, ID
    """
    result = []

    for item in data:
        status_info = {
            "STATUS_ID": item.get("STATUS_ID"),
            "NAME": item.get("NAME"),
            "ID": item.get("ID"),
        }
        result.append(status_info)

    return result

def get_funnel_status_by_name(webhook, name):
    funnels = get_funnel_lead(webhook)
    for f in funnels:
        if f['NAME'].lower() == name.lower():
            return f['STATUS_ID']


def get_funnel_lead(webhook) -> List[Dict[str, Any]]:
    """Получени воронки лидов"""
    method = "crm.status.list"
    payload = {"order": {"SORT": "ASC"}, "filter": {"ENTITY_ID": "STATUS"}}

    response = bitrix_request(webhook, method, payload)

    if response:
        return extract_status_data(response.get("result"))
    else:
        logger.info("Произошла ошибка при получении воронки Лидов")
        return None


def create_new_item_funnel_lead(webhook:str, status: str, title_field: str, weight: int):
    """
    Создать новый элемент воронки

    Пример:
    {
        "fields": {
            "ENTITY_ID": "STATUS",
            "STATUS_ID": "CUS_FIELD",
            "NAME": "Принятие решения",
            "SORT": 45,
        }
    }

    """
    method = "crm.status.add"
    payload = {
        "fields": {
            "ENTITY_ID": "STATUS",
            "STATUS_ID": status,
            "NAME": title_field,
            "SORT": weight,
        }
    }
    response = bitrix_request(webhook, method, payload)

    if response:
        logger.info(f"Поле {title_field} воронки Лида создано успешно.")
    else:
        logger.info(f"При создании поля {title_field} произошла ошибка.")


def move_lead_in_funnel(webhook: str, new_status: str, id_lead: str):
    """Перемещения Лида по воронке"""

    result = update_lead(webhook, id_lead, {"STATUS_ID": new_status})

    if result:
        logger.info(f"Перемещение лида #{id_lead} прошло успешно на {new_status}.")
    else:
        logger.info(f"Произощла ошибка при перемещении лида #{id_lead} на {new_status}")
