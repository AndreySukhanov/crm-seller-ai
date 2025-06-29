from django.db import models

from utils.models import BaseModel


def upload_rag_file(instance, filename):
    return f"client_bz/{instance.company.id}_{instance.company.name}/chunks/{filename}"


def upload_faiss_file(instance, filename):
    if not filename.split(".")[-1] == "index":
        raise ValueError("file must have index extension")
    return f"client_bz/{instance.company.id}_{instance.company.name}/index/{filename}"


def upload_docs_file(instance, filename):
    if not filename.split(".")[-1] == "pkl":
        raise ValueError("file must have index extension")
    return f"client_bz/{instance.company.id}_{instance.company.name}/index/{filename}"


class DocsFile(models.Model):
    file = models.FileField(upload_to=upload_docs_file)
    company = models.ForeignKey("users.Company", on_delete=models.CASCADE, related_name="doc_files")


class FaissFile(models.Model):
    file = models.FileField(upload_to=upload_faiss_file)
    company = models.ForeignKey("users.Company", on_delete=models.CASCADE, related_name="faiss_files")


class RagFile(models.Model):
    file = models.FileField(upload_to=upload_rag_file)
    company = models.ForeignKey("users.Company", on_delete=models.CASCADE, related_name="rag_files")


class Message(BaseModel):
    """Модель сообщения из переписки с конечным пользователем"""
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    channel = models.CharField(
        max_length=40, choices=(
            ('1|TELEGRAM', 'Telegram - Открытая линия'),
            ('whatsapp', 'whatsapp'),
            ('telegram_bot', 'telegram_bot'),
            ('avito', 'avito'),
            ('vk', 'vk'),
            ('instagram', 'instagram'),
        ), blank=True, null=True,
    )
    first_message = models.BooleanField(default=False)
    role = models.CharField(max_length=40, null=True)
    content = models.TextField(null=True)
    chat = models.ForeignKey("chat.Chat", on_delete=models.CASCADE, related_name="messages")
    created_at = models.DateTimeField(auto_now_add=True)


class Chat(BaseModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="chats")
    title = models.CharField(max_length=255, default="Новый чат", null=True)
    gpt_enabled = models.BooleanField(default=True)
    stage = models.CharField(max_length=255, blank=True, null=True)

    def get(self):
        return [{"role": msg.role, "content": msg.content} for msg in self.messages.all()]

    def add(self, role, content):
        first_message = False
        if not Message.objects.filter(chat=self).count():
            first_message = True
        Message.objects.create(
            role=role, content=content, chat=self, user=self.user, first_message=first_message
        )


class Meet(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)


class Func(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name


class Property(models.Model):
    func = models.ForeignKey(Func, on_delete=models.CASCADE, related_name="props")
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, default="integer")
    description = models.TextField()
    required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}:{self.type}"
