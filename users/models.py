from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

import inspect
import secrets
import string

from crm.services.crm_abs import CRM
def generate_unique_code(length=12):
    characters = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

class Company(models.Model):
    """Модель фирмы, купившей наши услуги"""
    max_history_length = models.IntegerField(default=50)
    meeting_duration = models.IntegerField(verbose_name="Длительность встречи в секундах", default=3600)
    time_offset = models.IntegerField(default=300)
    time_zone = models.CharField(max_length=255, default="Asia/Yekaterinburg")
    promt = models.TextField(blank=True, null=True)
    crm_name = models.CharField(max_length=255, default="bitrix")
    webhook = models.CharField(max_length=255, default="")

    off_gpt_on_stage = models.CharField(
        verbose_name="Название стадии, когда надо выключить gpt", max_length=222, blank=True, null=True)

    name = models.CharField(max_length=255)
    content = models.TextField(null=True)
    auth_domain = models.CharField(max_length=250, unique=True, blank=True, null=True)

    daily_limit = models.IntegerField(
        null=True,
        default=1,
        verbose_name="Дневной лимит для сообщений помощника при возврате лида",
    )
    sleep_days = models.IntegerField(
        null=True,
        default=30,
        verbose_name="Лимит в днях для активации спящих лидов",
    )
    stat_code = models.URLField(
        default=generate_unique_code,
        blank=True,
    )

    use_realty_api = models.BooleanField(default=False, verbose_name="RealtyAPI")
    api_key_realty_api = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Ключ апи для отрпавки в запросов в RealtyAPI",
    )

    def clean(self) -> None:
        super().clean()
        if self.use_realty_api and not self.api_key_realty_api:
            raise ValidationError({"api_key_realty_api": "Это поле обязательно, если используется RealtyAPI."})


class OutgoingConfig(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name="outgoing")
    start_message = models.TextField(verbose_name="исходящее сообщение")
    stage_name = models.CharField(max_length=255)
    wappi_token = models.CharField(max_length=244)
    wappi_profile = models.CharField(max_length=223)

class Stat(models.Model):
    company = models.OneToOneField('Company', on_delete=models.CASCADE, related_name="stat")


class CompanyFunc(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name="funcs")
    func = models.ForeignKey("chat.Func", on_delete=models.CASCADE, related_name="company_funcs") 
    prompt = models.TextField(verbose_name="Промт по которому gpt определит когда вызвать и какие аргументы передать")
    func_context = models.CharField(default="", blank=True, null=True, max_length=255, verbose_name="В случае если есть несколько вызовов одной и той же функции, этот контекст припишется к её названию и создаст уникальность")


class CustomLeadField(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name="lead_fields")
    field_code = models.CharField(max_length=255, verbose_name="Код поля (например, 'LEAD_CLASSIFICATION')")
    form_label = models.CharField(max_length=255, verbose_name="Название поля в форме")
    column_label = models.CharField(max_length=255, verbose_name="Название колонки в списке")
    user_type_id = models.CharField(max_length=255,
                                    verbose_name="Тип данных ('string', 'integer', 'enumeration', 'datetime' и т.д.)")
    default_value = models.CharField(max_length=255, verbose_name="Значение по умолчанию")
    xml_id = models.CharField(max_length=255, blank=True, null=True,
                              verbose_name="XML_ID для уникальности (если не указан, берётся field_code)")

    def delete(self, *args, **kwargs):
        from crm.services.bitrix import delete_crm_custom_field_by_code
        delete_crm_custom_field_by_code(self.company.webhook, self.field_code)
        return super().delete(*args, **kwargs)


class FunnelStep(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name="funnel_steps")
    name = models.CharField(max_length=255)
    use = models.BooleanField(default=True)
    step_id = models.CharField(max_length=255)
    status_id = models.CharField(max_length=255)


class User(AbstractUser):
    """Модель конечного пользователя"""

    """В джанго есть автоматическое распредение пользователей по правам, разобраться и научиться пользоваться(админка)"""
    """Будет 2 вида прав, админы и клиенты"""
    """Админ может всё, клиент может только смотреть свою статистику и кастомизировать свои промты"""
    crm_contact_id = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, null=True)
    last_activity = models.DateTimeField(null=True) 


class AMOConfig(models.Model):
    """Когда в админке создаем клиента, вписываем его данные из амо"""

    """При сохранении в админке проверяем вызов эндпоинтов амо, чтобы убедиться, что данные валидны"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    client_id = models.CharField(max_length=255)
    redirect_uri = models.CharField(max_length=500)
    client_secret = models.CharField(max_length=255)
    default_responsible_id = models.IntegerField()
    task_type_id = models.IntegerField()

    """В админке добавить возможность вбить временный код и с его помощью получить
        эти токены из crm"""
    access_token = models.CharField(max_length=500)
    refresh_token = models.CharField(max_length=500)
