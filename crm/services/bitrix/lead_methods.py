import logging
from typing import Optional, Dict, Any

from .base_methods import bitrix_request

logger = logging.getLogger(__name__)


def add_lead_comment(webhook, lead_id: str, message: str) -> Optional[str]:
    method = "crm.timeline.comment.add"
    payload = {
        "fields": {
            "ENTITY_ID": lead_id,
            "ENTITY_TYPE": "lead",
            "COMMENT": message,
        },
    }
    response = bitrix_request(webhook, method, payload)
    return response.get("result")


def get_lead_by_id(webhook, lead_id: str) -> Optional[dict]:
    """Получение информации о лиде"""
    method = f"crm.lead.get?ID={lead_id}"
    response = bitrix_request(webhook, method)
    return response.get("result")


def get_lead_userfields(webhook: str) -> list:
    method = "crm.lead.userfield.list"
    response = bitrix_request(webhook, method, {})
    return response.get("result", [])


def update_lead(webhook: str, lead_id: str, fields: Dict[str, Any]) -> Optional[bool]:
    method = "crm.lead.update"
    payload = {
        "id": lead_id,
        "fields": fields,
    }
    response = bitrix_request(webhook, method, payload)
    return response.get("result")


def get_latest_lead_id_by_contact(webhook, contact_id):
    leads = bitrix_request(webhook, 'crm.lead.list', {
        'filter': {'CONTACT_ID': contact_id},
        'order': {'DATE_CREATE': 'DESC'},
        'select': ['ID', 'TITLE']
    })
    if leads['result']:
        return leads['result'][0]['ID']
    return None


def create_lead_from_contact(webhook, contact_id):
    contact = get_contact(webhook, contact_id)
    if not contact:
        logger.error("Контакт не найден")
        return

    contact_data = contact
    fields = {
        "TITLE": f"Лид из открытой линии (контакт #{contact_id})",
        "NAME": contact_data.get("NAME", ""),
        "LAST_NAME": contact_data.get("LAST_NAME", ""),
        "SECOND_NAME": contact_data.get("SECOND_NAME", ""),
        "PHONE": contact_data.get("PHONE", []),
        "EMAIL": contact_data.get("EMAIL", []),
        "CONTACT_ID": contact_id
    }
    response = bitrix_request(webhook, "crm.lead.add", {"fields": fields})

    if "result" in response:
        new_lead_id = response["result"]
        logger.info(f"Создан новый лид #{new_lead_id}")

        return new_lead_id
    else:
        logger.error("Ошибка при создании лида:", response)


def get_contact(webhook: str, contact_id: str) -> dict:
    method = "crm.contact.get"
    payload = {
        "id": contact_id,
    }
    response = bitrix_request(webhook, method, payload)
    logger.info(f"contact by {contact_id}: {response.get('result')}")
    return response.get("result")


def get_contacts(webhook):
    method = "crm.contact.list"

    response = bitrix_request(webhook, method)
    logger.info(f"contacts {response.get('result')}")
    return response.get("result")


def lead_has_custom_field(webhook: str, lead_id: str, field_code: str) -> bool:
    """
    Проверяет, существует ли кастомное поле у лида.

    :param webhook: Вебхук Bitrix24
    :param lead_id: ID лида
    :param field_code: Символьный код поля, например UF_CRM_...
    :return: True если поле существует, иначе False
    """
    lead = get_lead_by_id(webhook, lead_id)
    if not lead:
        return False
    return field_code in lead


def update_custom_field(webhook: str, lead_id: str, field_code: str, value: Any) -> Optional[bool]:
    """
    Обновляет кастомное поле лида в Bitrix24.

    :param webhook: Вебхук Bitrix24
    :param lead_id: ID лида
    :param field_code: Символьный код кастомного поля (например, "UF_CRM_123ABC")
    :param value: Новое значение поля
    :return: True, если успешно, иначе None
    """
    fields = {f"UF_CRM_{field_code}": value}
    return update_lead(webhook, lead_id, fields)


def create_crm_custom_field_at_lead(
        webhook,
        field_code: str,
        form_label: str,
        column_label: str,
        user_type_id: str,
        default_value: str = None,
        xml_id: str = None,
):
    """
    Создаёт пользовательское поле в lead

    :param field_code: Код поля (например, 'UF_CRM_LEAD_CLASSIFICATION')
    :param form_label: Название поля в форме
    :param column_label: Название колонки в списке
    :param user_type_id: Тип данных ('string', 'integer', 'enumeration', 'datetime' и т.д.)
    :param default_value: Значение по умолчанию
    :param xml_id: XML_ID для уникальности (если не указан, берётся field_code)
    :return: Ответ от API или False в случае ошибки

    Пример создания поля 'LEAD_CLASSIFICATION':
    {
        "fields": {
            "FIELD_NAME": "LEAD_CLASSIFICATION",
            "EDIT_FORM_LABEL": "Grade",
            "LIST_COLUMN_LABEL": "Grade",
            "USER_TYPE_ID": "string",
            "XML_ID": "LEAD_CLASSIFICATION",
            "SETTINGS": {
                "DEFAULT_VALUE": "Классификация не проводилась"
            }
        }
    }
    """

    method = f"crm.lead.userfield.add"

    payload = {
        "fields": {
            "FIELD_NAME": f"UF_CRM_{field_code}",
            "EDIT_FORM_LABEL": {"ru": form_label},
            "LIST_COLUMN_LABEL": {"ru": column_label},
            "USER_TYPE_ID": user_type_id,
            "XML_ID": f"UF_CRM_{xml_id}" or f"UF_CRM_{field_code}",
            "SETTINGS": {},
        }
    }

    if default_value is not None:
        payload["fields"]["SETTINGS"]["DEFAULT_VALUE"] = default_value

    try:
        response = bitrix_request(webhook, method, payload)
        if not response or "error" in response:
            logger.info(
                f"[ERROR] Не удалось создать поле {field_code}: {response.get('error_description', '')}"
            )
            return False
        return response
    except Exception as e:
        logger.error(f"Ошибка при создании поля {field_code}: {e}")
        return False


def delete_crm_custom_field_by_code(webhook: str, field_code: str) -> bool:
    """
    Удаляет кастомное поле лида по его коду (field_code без префикса UF_CRM_).

    :param webhook: Вебхук Bitrix24
    :param field_code: Код поля без префикса, например "LEAD_CLASSIFICATION"
    :return: True, если удаление прошло успешно, иначе False
    """
    field_name = f"UF_CRM_{field_code}"

    # Получаем список всех пользовательских полей лида
    method_list = "crm.lead.userfield.list"
    response = bitrix_request(webhook, method_list, {})

    if not response or "error" in response:
        logger.error(f"Ошибка при получении списка пользовательских полей: {response.get('error_description', response)}")
        return False

    fields = response.get("result", [])

    # Ищем поле по FIELD_NAME
    field_to_delete = next((f for f in fields if f.get("FIELD_NAME") == field_name), None)
    if not field_to_delete:
        logger.warning(f"Поле с кодом {field_name} не найдено")
        return False

    field_id = field_to_delete.get("ID")
    if not field_id:
        logger.error("ID поля не найден")
        return False

    # Удаляем поле по ID
    method_delete = "crm.lead.userfield.delete"
    delete_response = bitrix_request(webhook, method_delete, {"id": field_id})

    if delete_response and delete_response.get("result") is True:
        logger.info(f"Поле {field_name} успешно удалено")
        return True
    else:
        logger.error(f"Ошибка при удалении поля: {delete_response.get('error_description', delete_response)}")
        return False




def get_status_id_by_lead_id(webhook: str, lead_id: str) -> str:
    result = get_lead_by_id(webhook=webhook, lead_id=lead_id)
    return result.get('STATUS_ID', None)


def get_custom_field_value_by_lead_id(webhook: str, lead_id: str, field_code: str) -> str:
    result = get_lead_by_id(webhook=webhook, lead_id=lead_id)
    return result.get(f'UF_CRM_{field_code}', None)
