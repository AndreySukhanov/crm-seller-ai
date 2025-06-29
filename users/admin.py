from django.contrib import admin

from chat.models import RagFile, FaissFile, DocsFile
from chat.services.funcs import populate_funcs_from_crm
from crm.services import bitrix
from crm.services.bitrix import create_crm_custom_field_at_lead, get_lead_userfields
from users.models import Company, User, FunnelStep, CompanyFunc, CustomLeadField, OutgoingConfig


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "phone",
        "updated_at",
        "company",
        "last_activity",
    )
    list_filter = ("updated_at", "company", "updated_at", "last_activity")
    search_fields = ("company",)


class FunnelStepTabular(admin.TabularInline):
    model = FunnelStep
    extra = 0


class RagFileTabular(admin.TabularInline):
    model = RagFile
    extra = 0


class FaissFileTabular(admin.TabularInline):
    model = FaissFile
    extra = 0


class DocsFileTabular(admin.TabularInline):
    model = DocsFile
    extra = 0


class CompanyFuncTabular(admin.TabularInline):
    model = CompanyFunc
    extra = 0


class CustomLeadFieldTabular(admin.StackedInline):
    model = CustomLeadField
    extra = 0

class OutgoingConfigTabular(admin.StackedInline):
    model = OutgoingConfig
    extra = 0

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    save_on_top = True
    save_as = True
    inlines = [
        OutgoingConfigTabular,
        CustomLeadFieldTabular,
        CompanyFuncTabular,
        FunnelStepTabular,
        RagFileTabular,
        DocsFileTabular,
        FaissFileTabular,
    ]

    def stat_link(self, obj):
        return f"http://127.0.0.1:8080/company/stats?code={obj.stat_code}"

    def save_model(self, request, obj, form, change):
        is_new = obj.pk
        super().save_model(request, obj, form, change)

        populate_funcs_from_crm()

        if is_new:
            try:
                steps = bitrix.get_sales_funnel(obj.webhook)
                for step in steps:
                    FunnelStep.objects.get_or_create(
                        company=obj,
                        name=step['NAME'],
                        step_id=step.get('ID'),
                        status_id=step.get("STATUS_ID"),
                    )
            except Exception as e:
                self.message_user(request, f'Ошибка при получении стадий из Bitrix: {e}', level='error')

        # Проверяем кастомные поля компании
        try:
            existing_fields = get_lead_userfields(obj.webhook)
            existing_field_codes = {f['FIELD_NAME'] for f in existing_fields}

            for custom_field in obj.lead_fields.all():
                if custom_field.field_code not in existing_field_codes:
                    created = create_crm_custom_field_at_lead(
                        webhook=obj.webhook,
                        field_code=custom_field.field_code,
                        form_label=custom_field.form_label,
                        column_label=custom_field.column_label,
                        user_type_id=custom_field.user_type_id,
                        default_value=custom_field.default_value,
                        xml_id=custom_field.xml_id or custom_field.field_code,
                    )
                    if not created:
                        self.message_user(
                            request,
                            f"Не удалось создать кастомное поле {custom_field.field_code} в Bitrix",
                            level='error'
                        )
        except Exception as e:
            self.message_user(request, f"Ошибка при проверке/создании кастомных полей: {e}", level='error')

    readonly_fields = (
        'stat_link',
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "auth_domain",
                    "daily_limit",
                    "sleep_days",
                    "content",
                    "promt",
                    "webhook",
                    "use_realty_api",
                    "api_key_realty_api",
                    "off_gpt_on_stage"
                )
            },
        ),
        ('Statistics', {
            'fields': (
                'stat_link',
            )
        }),
    )


admin.site.register(Company, CompanyAdmin)
