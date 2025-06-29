"""Здесь логика обработки лидов, добавления сообщений"""

import time
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import pytz

from django.conf import settings

from users.models import Company, User
from .models import Lead
import logging

logger = logging.getLogger(__name__)


class BitrixCRM:
    def __init__(self):
        """Инициализация клиента Bitrix24 с конфигурацией."""
        self.base_url = settings.BITRIX_WEBHOOK_URL
        self.name_crm = "bitrix"

    def create_contact_user(
        self, name: str, last_name: str = "", phone: str = "", email: str = "", lead_id: str = ""
    ) -> str:
        """Создание нового контакта"""
        method = "crm.contact.add"
        payload = {
            "fields": {
                "NAME": name,
                "LAST_NAME": last_name,
                "PHONE": [{"VALUE": phone, "VALUE_TYPE": "WORK"}] if phone else [],
                "EMAIL": [{"VALUE": email, "VALUE_TYPE": "WORK"}] if email else [],
            }
        }

        # Если есть привязка к лиду
        if lead_id:
            payload["fields"]["LEAD_ID"] = lead_id

        response = self._make_request(method, payload)
        contact_id = response.get("result")

        if contact_id:
            logger.info(f"Контакт успешно создан, \nid: {contact_id}\nresponse: {response}")
            return contact_id
        else:
            logger.warning(f"Не удалось создать контакт, \npayload: {payload}\nresponse: {response}")
            return {}

    def get_contact_user(self, contact_id: str) -> dict[str, Any]:
        """Получение информации о контакте"""
        method = "crm.contact.get"
        payload = {"ID": contact_id}
        response = self._make_request(method, payload)

        if response:
            logger.info(f"Контакт успешно получен, \nid: {contact_id}\nresponse: {response}")
            return response.get("result")
        else:
            logger.error(f"Не удалось получить контакт, \nid: {contact_id}\nresponse: {response}")


    def create_deal(
        self,
        title: str,
        stage_deal: str,
        contact_ids: list,
        responsible: int,
        id_funnel: int = 0,
        currency: str = "RUB",
        opened: str = "Y",
        closed: str = "N",
        **kwarg,
    ) -> int | None:
        """Создать новую сделку"""
        method = "crm.deal.add"
        payload = {
            "FIELDS": {
                "TITLE": title,
                "STAGE_ID": stage_deal,
                "CURRENCY_ID": currency,
                "CONTACT_IDS": contact_ids,
                "OPENED": opened,
                "CLOSED": closed,
                "CATEGORY_ID": id_funnel,
                "ASSIGNED_BY_ID": responsible,
                **kwarg,
            }
        }

        response = self._make_request(method, payload)

        if response:
            id_deal = response.get("result")
            logger.info(f"Создана сделка #{id_deal}-{title}")
            return id_deal
        else:
            logger.info(f"Ошибка при создании сделки {title!r}")

    def update_deal(self, id_deal: int, stage: str):
        """Изменить сделку, движение по воронке"""
        method = "crm.deal.update"
        payload = {"ID": id_deal, "fields": {"STAGE_ID": stage}}

        response = self._make_request(method, payload)

        if response:
            logger.info(f"Сделка #{id_deal}, успешно обновлена")
        else:
            logger.info(f"Ошибка при обновлении сделки #{id_deal}")




def data_contac_crm(entity_data: str) -> dict | None:
    """Разбивает строку для получения id контакта и получения данных о контакте."""
    contact_user_id = entity_data.split("|")[5]
    api_bitrix = BitrixCRM()

    return api_bitrix.get_contact_user(contact_user_id)


