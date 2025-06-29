from django.urls import path
from .views import DisableGptView, EnableGptView, bitrix_install_view, bitrix_widget_view, check_redis_func

urlpatterns = [
    path("webhook/disable-gpt/", DisableGptView.as_view(), name="disable_gpt"),
    path("webhook/enable-gpt/", EnableGptView.as_view(), name="enable_gpt"),
    path('bitrix/install/', bitrix_install_view, name='bitrix_install'),
    path('bitrix/widget/', bitrix_widget_view, name='bitrix_widget'),
    path("check_celery/", check_redis_func),
]
