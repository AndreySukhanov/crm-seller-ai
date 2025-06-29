import re
from urllib.parse import urlparse

class AllowBitrixIframeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Удаляем X-Frame-Options, если есть
        response.headers.pop('X-Frame-Options', None)

        # Получаем Referer
        referer = request.META.get('HTTP_REFERER', '')
        parsed = urlparse(referer)
        domain = parsed.scheme + "://" + parsed.netloc

        # Разрешаем iframe только с доменов *.bitrix24.ru
        if re.match(r"^https:\/\/[a-z0-9\-]+\.bitrix24\.ru$", domain):
            response['Content-Security-Policy'] = f"frame-ancestors 'self' {domain};"
        else:
            response['Content-Security-Policy'] = "frame-ancestors 'self';"  # запрет на всё кроме self

        return response
