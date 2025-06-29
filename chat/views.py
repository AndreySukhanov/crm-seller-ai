import json

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response

from chat.tasks import check_for_sleep_lead
from users.models import User
from chat.models import Chat


def check_redis_func(request):
    check_for_sleep_lead()
    return HttpResponse(status=200)


class DisableGptView(APIView):
    """
    Вебхук для Bitrix: отключение GPT для чата пользователя
    """
    def post(self, request, *args, **kwargs):        
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        try:
            user = User.objects.get(id=user_id)
            chat = Chat.objects.filter(user=user).order_by("-updated_at").first()
            if not chat:
                return Response({"error": "Chat not found"}, status=404)

            chat.gpt_enabled = False
            chat.save()

            return Response({"status": "success", "message": f"GPT отключён для user_id={user_id}"})

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)


class EnableGptView(APIView):
    """
    Вебхук для Bitrix: включение GPT обратно
    """
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        try:
            user = User.objects.get(id=user_id)
            chat = Chat.objects.filter(user=user).order_by("-updated_at").first()
            if not chat:
                return Response({"error": "Chat not found"}, status=404)

            chat.gpt_enabled = True
            chat.save()

            return Response({"status": "success", "message": f"GPT включён для user_id={user_id}"})

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

@csrf_exempt
def bitrix_install_view(request):
    return render(request, 'bitrix/install.html')

@csrf_exempt
def bitrix_widget_view(request):
    """
    Отдаёт HTML с двумя кнопками, получает PLACEMENT_OPTIONS
    в request.POST['PLACEMENT_OPTIONS'].
    """
    placement_options = {}

    po = request.POST.get('PLACEMENT_OPTIONS')

    if po:
        try:
            placement_options = json.loads(po)
        except json.JSONDecodeError:
            placement_options = {}
    else:
        placement_options = {}

    placement_options_json = json.dumps(placement_options)

    return render(request, 'bitrix/widget.html', {
        'placement_options_json': placement_options_json
    })

