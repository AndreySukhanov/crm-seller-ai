from django.contrib import admin

from .models import Lead



@admin.register(Lead)
class AdminLead(admin.ModelAdmin):
    pass
