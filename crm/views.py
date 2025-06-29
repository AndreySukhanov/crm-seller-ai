import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging

from chat.services import chat_with_gpt
from .services import bitrix
from .services.outgoing import outgoing
from .services.request_data_handler import RequestDataHandler, get_company, get_crm
from .services.realty_api.realty_api_integration import RealtyAPIAPI

logger = logging.getLogger(__name__)


class WebhookView(APIView):
    def post(self, request, *args, **kwargs):
        """
        Принимает POST-запрос и возвращает полученные данные
        """
        logger.info(f"Пришел запрос на WebhookView, содержание запроса:\n{request.data}")
        event = request.data.get("event")

        if event == "ONCRMLEADADD" or event == "ONCRMLEADUPDATE":
            outgoing(request.data)

        if event == "ONIMBOTMESSAGEADD":
            rdh: RequestDataHandler = RequestDataHandler(request.data)
            if rdh.is_manager:
                return Response(
                    {
                        "status": "success",
                        "is_manager": rdh.is_manager,
                    },
                    status=status.HTTP_200_OK,
                )

            answer_gpt = chat_with_gpt(rdh=rdh)
            if answer_gpt:
                rdh.crm.send_message_to_chat(
                    crm_entity=rdh.crm_entity,
                    chat_id=rdh.chat_id,
                    manager_id=1,  # Тестовый менеджер
                    message=answer_gpt,
                    crm_entity_type=rdh.crm_entity_type
                )

                # Для клиентов с RealtyAPI
                if rdh.company.use_realty_api:
                    api_realty_api = RealtyAPIAPI(appkey=rdh.company.api_key_realty_api)
                    api_realty_api.create_realty(
                        owner_fio=rdh.user.last_name,
                        owner_phone=rdh.user.phone,
                        action=1,
                        object_type="flat",
                    )
                    
            return Response(
                {
                    "status": "success",
                    "received_data": answer_gpt,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "status": "success",
                "received_data": request.data,
            },
            status=status.HTTP_200_OK,
        )
