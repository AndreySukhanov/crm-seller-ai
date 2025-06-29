import logging
from typing import Optional

from crm.services.bitrix.base_methods import bitrix_request
from crm.services.bitrix.lead_methods import get_lead_by_id

logger = logging.getLogger(__name__)


def send_message_to_chat(
        crm_entity: str,
        chat_id: str,
        manager_id: str,
        message: str,
        webhook: str,
        crm_entity_type: str = "lead",
) -> int | None:
    """Отправка сообщения в чат"""
    method = "imopenlines.crm.message.add"
    payload = {
        "CRM_ENTITY_TYPE": crm_entity_type,
        "CRM_ENTITY": crm_entity,  # id lead or id contact
        "CHAT_ID": chat_id,
        "USER_ID": manager_id,  # id manager
        "MESSAGE": message,
    }

    response = bitrix_request(webhook, method, payload)

    if response is None:
        switch_dialogue_to_operator(webhook=webhook, chat_id=chat_id)
        # time.sleep(10)
        start_dioalog(webhook, chat_id)
        # time.sleep(10)
        response = bitrix_request(method=method, payload=payload, webhook=webhook)

    result = response.get("result")
    if result:
        logger.info(f"Отправка сообщения в чат прошла успешно, result: {result}")
    else:
        logger.error(f"Сообщение не было доставлено в чат, response: {response}")

    return result


def start_dioalog(webhook: str, chat_id: str) -> Optional[bool]:
    """Открывает диалог с клиентом"""
    method = "imopenlines.session.start"

    response = bitrix_request(
        webhook=webhook,
        method=method,
        payload={"CHAT_ID": chat_id},
    )
    return response.get("result")


def add_new_lead_to_session(webhook: str, chat_id: str, new_lead_id):
    method = "imopenlines.dialog.updateSession"
    response = bitrix_request(
        webhook=webhook,
        method=method,
        payload={
            'CHAT_ID': chat_id,  # из data[PARAMS][CHAT_ID]
            'FIELDS': {
                'CRM_ENTITY_TYPE': 'LEAD',
                'CRM_ENTITY_ID': new_lead_id
            }},
    )
    logger.info(f"add_new_lead_to_session: {response}")
    if response:
        return response.get("result")


def switch_dialogue_to_operator(webhook: str, chat_id: str) -> Optional[bool]:
    """Переключает диалогс бота на оператора"""

    method = "imopenlines.bot.session.operator"
    response = bitrix_request(
        webhook=webhook,
        method=method,
        payload={"CHAT_ID": chat_id},
    )
    if response:
        return response.get("result")
