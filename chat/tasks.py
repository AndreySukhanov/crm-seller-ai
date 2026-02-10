import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.db.models import DateTimeField, ExpressionWrapper, F
from django.db.models.functions import Now
from django.utils import timezone

from chat.models import Message
from chat.services.base import ask_gpt
from chat.services.documents import load_index
from crm.services.bitrix import get_contact, get_lead_by_id
from crm.services.bitrix.chat_methods import send_message_to_chat
from crm.services.request_data_handler import get_crm
from users.models import User

logger = logging.getLogger(__name__)


@shared_task(name="chat.tasks.everyday_check_for_sleep_lead")
def check_for_sleep_lead():
    """
    Проходит по всем юзерам и проверяет не вышло ли время сна.
    Если вышло, то отправляем сообщение для согрева.
    """
    users_to_wake = (
        User.objects.select_related("company")
        .annotate(
            sleep_time=ExpressionWrapper(
                Now() - F("company__sleep_days") * timedelta(days=1),
                output_field=DateTimeField(),
            )
        )
        .filter(
            last_activity__lt=F("sleep_time"),
            last_activity__isnull=False,
            company__isnull=False,
        )
    )

    for user in users_to_wake:
        logger.info("---Возвращение лида %s---", user.username)

        now = datetime.now()
        today_messages = Message.objects.filter(
            user_id=user.pk,
            role="assistant",
            created_at__date=now.date(),
        ).count()

        if today_messages >= user.company.daily_limit:
            logger.info("Дневной лимит сообщений для %r исчерпан.", user.username)
            continue

        company = user.company
        index, all_docs = load_index(company)
        chat = user.chats.first()
        lead = user.leads.first()

        if not chat or not lead:
            logger.warning("Пропуск пользователя %s: нет chat или lead", user.username)
            continue

        prompt = (
            "Ты помощник менеджера по работе с клиентами.\n"
            "Твоя задача — составить короткое, дружелюбное сообщение для клиента, который давно не выходил на связь.\n\n"
            "Правила составления:\n"
            "- Пиши от первого лица ('Привет!', 'Решил уточнить...');\n"
            "- Упоминай скидку, если она есть;\n"
            "- Без скидок — уточни, актуален ли вопрос;\n"
            "- Не используй формальные обращения ('Уважаемый клиент') и не начинай с 'Здравствуйте';\n"
            "- Не предлагай всё заново, как будто вы только что познакомились;\n"
            "- Сообщение должно быть лаконичным, без лишних объяснений;\n"
            "- Результат должен быть готов к отправке через чат или CRM.\n\n"
            "Примеры:\n"
            "- 'Привет! Видел, вы спрашивали про RCD 360 — сейчас на него скидка 15%, если ещё актуально, подскажу.'\n"
            "- 'Вы говорили, что подумаете — просто решил уточнить, остался ли интерес?'\n\n"
            "Составь короткое сообщение для клиента, который давно не выходил на связь.\n"
        )

        answer_gpt = ask_gpt(
            index=index,
            docs=all_docs,
            query=prompt,
            chat=chat,
            lead_id=lead.lead_id,
            company=company,
            crm=get_crm(company),
        )

        crm_lead = get_lead_by_id(company.webhook, lead.lead_id)
        contact = get_contact(company.webhook, crm_lead.get("CONTACT_ID"))

        send_message_to_chat(
            crm_entity=lead.lead_id if not contact else contact["ID"],
            chat_id=lead.dialog_id,
            manager_id=1,
            message=answer_gpt,
            webhook=company.webhook,
            crm_entity_type="lead" if not contact else "contact",
        )

        user.last_activity = timezone.now()
        user.save(update_fields=["last_activity"])
        logger.info("GPT написал пользователю %s. Ответ: %s", user.username, answer_gpt)
