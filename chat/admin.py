from django.contrib import admin
from chat.models import Message, Chat

from django.contrib import admin
from .models import Func, Property, Meet


@admin.register(Meet)
class MeetAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")


class PropertyInline(admin.TabularInline):
    model = Property
    extra = 0  # количество пустых форм по умолчанию
    fields = ("name", "type", "description", "required")
    show_change_link = False


@admin.register(Func)
class FuncAdmin(admin.ModelAdmin):
    list_display = ("name", "short_description")
    search_fields = ("name", "description")
    inlines = [PropertyInline]

    def short_description(self, obj):
        return (obj.description[:75] + '...') if len(obj.description) > 75 else obj.description

    short_description.short_description = "Описание"


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "required", "func")
    list_filter = ("required", "type", "func")
    search_fields = ("name", "description", "func__name")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("user", "channel", "first_message", "role", "content", "chat", "updated_at")
    list_filter = ("user", "channel", "first_message", "role", "content", "chat", "updated_at")
    search_fields = ("user", "channel", "content", "chat", "updated_at")


@admin.register(Chat)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "updated_at")
    list_filter = ("user", "updated_at")
    search_fields = ("user", "updated_at")
