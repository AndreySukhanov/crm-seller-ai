import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")

app = Celery("conf")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # 'everyday_check_for_sleep_lead': {
    #     'task': 'chat.tasks.everyday_check_for_sleep_lead',
    #     "schedule": 30, # 30 екунд для тестов
    #     # 'schedule': crontab(hour=10, minute=0), 
    # },
    'recalc_lead_segments_daily': {
        'task': 'crm.tasks.recalc_lead_segments',
        "schedule": 30, # 30 екунд для тестов
        # 'schedule': crontab(hour=10, minute=0), 
    },
}

