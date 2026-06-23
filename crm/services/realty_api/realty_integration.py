import logging
import os

import requests


logger = logging.getLogger(__name__)


class RealtyAPI:
    """
    Generic client for a real-estate partner API.

    Thin wrapper around a partner's ``importObject/`` endpoint that creates a
    property entry on the partner side when a new lead is qualified. The base
    URL is configured via ``REALTY_API_BASE_URL`` to keep the integration
    vendor-agnostic.
    """

    DEFAULT_BASE_URL = "https://api.example.com/realty"

    def __init__(self, appkey: str, base_url: str | None = None) -> None:
        self.appkey = appkey
        self.base_url = base_url or os.getenv("REALTY_API_BASE_URL", self.DEFAULT_BASE_URL)

    def _send_request(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url.rstrip('/')}/{endpoint}"
        logger.info(f"Отправка запроса на {url} с данными: {payload}")
        try:
            response = requests.post(url, json=payload, timeout=10)
            logger.info(f"Получен ответ ({response.status_code}): {response.text[:200]}...")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Ошибка сети при обращении к сервису недвижимости: {e}", exc_info=True)
            raise

    def create_realty(
        self,
        owner_fio: str,
        owner_phone: str,
        action: int,
        object_type: str,
        to_number: str | None,
    ) -> dict:
        """
        Создаёт объект недвижимости на стороне партнёрского сервиса.

        :param owner_fio: ФИО собственника
        :param owner_phone: Телефон собственника (только цифры, например: '79261234567')
        :param action: Тип сделки: 0 — аренда, 1 — продажа
        :param object_type: Тип недвижимости:
                          flat — квартира
                          room — комната
                          house — дом
                          land — участок
                          commerce — коммерческая недвижимость
        :param to_number: Необязательный параметр. Номер телефона колл-центра,
                          на который был осуществлён звонок (без +7)
        :return: JSON-ответ партнёрского сервиса
        """
        payload = {
            "appkey": self.appkey,
            "object_type": object_type,
            "action": action,
            "owner_fio": owner_fio,
            "owner_phone": owner_phone,
        }
        if to_number:
            payload["to_number"] = to_number
        return self._send_request("importObject/", payload)
