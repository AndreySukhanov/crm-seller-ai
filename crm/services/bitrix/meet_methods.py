from typing import List, Optional
from datetime import datetime, timedelta
import pytz
import logging

from chat.models import Meet
from crm.models import Lead
from crm.services.bitrix.base_methods import bitrix_request
from crm.services.bitrix.lead_methods import get_lead_by_id

logger = logging.getLogger(__name__)


def get_lead_responsible_free_slots(
        webhook,
        lead_id: str,
        from_date: datetime,
        to_date: datetime,
) -> List[str]:
    try:
        """Получение свободных слотов с учетом рабочего времени."""
        # Преобразуем ISO-строки в datetime, если нужно
        if isinstance(from_date, str):
            # подменяем 'Z' на '+00:00', чтобы fromisoformat принял UTC
            from_date = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
        if isinstance(to_date, str):
            to_date   = datetime.fromisoformat(to_date.replace("Z", "+00:00"))

        # Локализуем в Moscow-timezone, если tzinfo ещё нет
        tz = pytz.timezone("Europe/Moscow")
        if from_date.tzinfo is None:
            from_date = tz.localize(from_date)
        if to_date.tzinfo   is None:
            to_date   = tz.localize(to_date)
       
        # Получаем данные лида
        lead_data = get_lead_by_id(webhook, lead_id)

        tz = pytz.timezone("Europe/Moscow")  # Timezone будет всегда одна?
        if from_date.tzinfo is None:
            from_date = tz.localize(from_date)
        if to_date.tzinfo is None:
            to_date = tz.localize(to_date)

        responsible_id = lead_data.get("ASSIGNED_BY_ID")

        if not responsible_id:
            # logger.info(f"Лид не найден в get_lead_responsible_free_slots: {lead_id}")
            return []

        # Получаем занятость
        accessibility_data = bitrix_request(webhook,
                                            "calendar.accessibility.get",
                                            {"users": [responsible_id], "from": from_date.isoformat(),
                                             "to": to_date.isoformat()},
                                            )
        busy_slots = accessibility_data.get("result", {}).get(responsible_id, [])

        # Настройки рабочего дня
        work_start, work_end = 9, 18
        free_slots = []
        current_date = from_date.replace(hour=work_start, minute=0, second=0, microsecond=0)
        end_date = to_date.replace(hour=work_end, minute=0, second=0, microsecond=0)

        while current_date < end_date:
            slot_is_free = True
            for busy_slot in busy_slots:
                try:
                    tz_from = pytz.timezone(busy_slot["TZ_FROM"])
                    tz_to = pytz.timezone(busy_slot["TZ_TO"])
                    busy_start = tz_from.localize(
                        datetime.strptime(busy_slot["DATE_FROM"], "%d.%m.%Y %H:%M:%S")
                    )
                    busy_end = tz_to.localize(
                        datetime.strptime(busy_slot["DATE_TO"], "%d.%m.%Y %H:%M:%S")
                    )
                except ValueError:
                    busy_start = tz_from.localize(
                        datetime.strptime(busy_slot["DATE_FROM"], "%d.%m.%Y").replace(hour=0, minute=0)
                    )
                    busy_end = tz_to.localize(
                        datetime.strptime(busy_slot["DATE_TO"], "%d.%m.%Y").replace(hour=23, minute=59)
                    )

                if current_date < busy_end and current_date + timedelta(hours=1) > busy_start:
                    slot_is_free = False
                    break

            if slot_is_free and work_start <= current_date.hour < work_end:
                free_slots.append(current_date.strftime("%d %B, %H:%M"))

            current_date += timedelta(hours=1)

        return free_slots
    except Exception as e:
        logger.error(f"Ошибка внутри класса BitrixCRM get_lead_responsible_free_slots: {e}")


def create_lead_meeting(
        webhook,
        lead_id: str,
        meeting_time: datetime,
        title: str,
        duration_hours: int = 1,
        description: Optional[str] = None,
) -> Optional[str]:
    """Создание встречи для лида в указанное время."""
    try:
        
        # Преобразуем ISO-строку в datetime, если нужно
        if isinstance(meeting_time, str):
            # если строка в формате "2025-05-22T10:00:00" без зоны, изоформат примет
            meeting_time = datetime.fromisoformat(meeting_time)
        # Локализуем в европейское время, если tzinfo нет
        tz = pytz.timezone("Europe/Moscow")
        if meeting_time.tzinfo is None:
            meeting_time = tz.localize(meeting_time)
        
        # Получаем данные лида
        lead_data = get_lead_by_id(webhook, lead_id)
        if not lead_data or not isinstance(lead_data, dict):
            # logger.error(f"Failed to fetch lead data for lead_id: {lead_id}. Response: {lead_data}")
            return None

        responsible_id = lead_data.get("ASSIGNED_BY_ID", 1)  # 1 как запасной вариант
        logger.info(f"Fetched lead data for lead_id: {lead_id}, responsible_id: {responsible_id}")

        # Формируем время окончания встречи
        end_time = meeting_time + timedelta(hours=duration_hours)

        lead_phone = lead_data.get("PHONE", [])
        lead_phone = lead_phone[0]["VALUE"] if lead_phone else "Телефон не задан"

        method = "crm.activity.add"
        payload = {
            "fields": {
                "OWNER_ID": lead_id,
                "OWNER_TYPE_ID": 1,  # 1 = Лид. Идентификатор типа объекта CRM
                "TYPE_ID": 1,  # 1 = Встреча. Тип дела
                "COMMUNICATIONS": [{"VALUE": lead_phone, "TYPE": "PHONE"}],
                "DESCRIPTION": description or "",
                "RESPONSIBLE_ID": responsible_id,
                "START_TIME": meeting_time.isoformat(),
                "END_TIME": end_time.isoformat(),
                "SUBJECT": title,
            }
        }

        # Выполняем запрос на создание встречи
        response = bitrix_request(webhook, method, payload)
        logger.info(f"Bitrix response for creating meeting: {response}")

        # Проверка успешности ответа
        if not response or not isinstance(response, dict):
            logger.error(f"Invalid response from Bitrix for lead_id: {lead_id}. Response: {response}")
            return None

        result = response.get("result")
        if not result:
            logger.error(f"Failed to create meeting for lead_id: {lead_id}. Response: {response}")
            return None

        logger.info(f"Successfully created meeting for lead_id: {lead_id}. Result: {result}")
        lead = Lead.objects.filter(lead_id=lead_id).first()
        if lead:
            Meet.objects.create(user=lead.user)
        return result

    except Exception as e:
        logger.error(f"Error in create_lead_meeting for lead_id: {lead_id}. Exception: {str(e)}")
        return None
