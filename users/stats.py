from collections import defaultdict
from datetime import timedelta, datetime

from django.db.models.functions import TruncDate
from django.utils import timezone

from chat.models import Message, Meet
from users.models import Company


def get_company_stats(company):
    # Подготавливаем словарь с датами
    stats_by_date = defaultdict(lambda: {
        "incoming_messages": 0,
        "sent_messages": 0,
        "neuro_dialog_starts": 0,
        "user_dialog_starts": 0,
        "meets": 0,
    })

    # Обрабатываем сообщения
    messages = Message.objects.filter(chat__user__company=company).annotate(date=TruncDate('created_at'))
    for msg in messages:
        date_str = msg.date.strftime("%d-%m-%Y")
        if msg.role == "assistant":
            stats_by_date[date_str]["sent_messages"] += 1
            if msg.first_message:
                stats_by_date[date_str]["neuro_dialog_starts"] += 1
        else:
            stats_by_date[date_str]["incoming_messages"] += 1
            if msg.first_message:
                stats_by_date[date_str]["user_dialog_starts"] += 1

    # Обрабатываем встречи
    meets = Meet.objects.filter(user__company=company).annotate(date=TruncDate('created_at'))
    for meet in meets:
        date_str = meet.date.strftime("%d-%m-%Y")
        stats_by_date[date_str]["meets"] += 1


    result = [
        {"date": date, **data}
        for date, data in sorted(stats_by_date.items(), key=lambda x: datetime.strptime(x[0], "%d-%m-%Y"))
    ]

    return result

