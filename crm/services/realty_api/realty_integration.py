import requests
import logging


logger = logging.getLogger(__name__)


class RealtyAPIAPI:
    """
    Клиент для взаимодействия с API сервиса RealtyAPI.
    """

    def __init__(self, appkey: str) -> None:
        self.appkey = appkey
        self.base_url = "https://api.example.com/call/main"

    def _send_request(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}/{endpoint}"
        logging.info(f"Отправка запроса на {url} с данными: {payload}")
        try:
            response = requests.post(url, json=payload, timeout=10)
            logging.info(f"Получен ответ ({response.status_code}): {response.text[:200]}...")

            # Вызывает исключение, если статус не 2xx
            response.raise_for_status()

            return response.json()
        except requests.RequestException as e:
            logger.error(f"Ошибка сети при обращении к RealtyAPI: {e}", exc_info=True)
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
        Создает объект недвижимости в RealtyAPI через API

        :param owner_fio: ФИО собственника
        :param owner_phone: Телефон собственника (только цифры, например: '79261234567')
        :param action: Тип сделки: 0 - аренда, 1 - продажа
        :param object_type: Тип недвижимости:
                          flat - квартира
                          room - комната
                          house - дом
                          land - участок
                          commerce - коммерческая недвижимость
        :param to_number: Необязательный параметр. Номер телефона колл-центра,
                          на который был осуществлен звонок (без +7)
        :return: JSON-ответ от RealtyAPI
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
