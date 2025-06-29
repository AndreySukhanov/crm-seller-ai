from django.db import models

from utils.models import BaseModel


class Lead(BaseModel):
    """Модель Лида из crm"""

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="leads")
    lead_id = models.CharField(max_length=100, unique=True)
    dialog_id = models.CharField(max_length=100)
    crm = models.CharField(
        max_length=20,
        choices=(
            ("bitrix", "bitrix"),
            ("amo", "amo"),
        ),
    )
    lead_grade = models.CharField(
        max_length=1,
        choices=[
            ("A", "A"),
            ("B", "B"),
            ("C", "C"),
        ],
        null=True,
        blank=True,
    )
    segment = models.CharField(
        max_length=32,
        choices=[
            ('Новый', 'Новый'),
            ('Горячий', 'Горячий'),
            ('Тёплый', 'Тёплый'),
            ('Холодный', 'Холодный'),
            ('Купил', 'Купил'),
            ('Не купил', 'Не купил'),
        ],
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.user} ({self.lead_id})"

